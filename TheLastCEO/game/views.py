from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import User, GameSession, Player, QuizQuestion
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    GameSessionSerializer, PlayerSerializer, AvatarCustomizationSerializer
)
from .avatar_service import avatar_service
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id': user.id,
            'nickname': user.nickname,
            'balance': user.balance
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """User login endpoint"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id': user.id,
            'nickname': user.nickname,
            'balance': user.balance
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def profile(request):
    """User profile endpoint"""
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def customize_avatar(request):
    """Customize user avatar"""
    serializer = AvatarCustomizationSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        
        # Update user avatar preferences
        user = request.user
        user.avatar_headwear = data.get('headwear')
        user.avatar_accessory = data.get('accessory')
        user.avatar_gender = data.get('gender')
        user.avatar_favorite_color = data.get('favorite_color')
        user.save()
        
        # Generate new avatar
        try:
            avatar_url = avatar_service.generate_avatar_url(user)
            user.avatar_url = avatar_url
            user.save()
            
            return Response({
                'message': 'Avatar customized successfully',
                'avatar_url': avatar_url
            })
        except Exception as e:
            logger.error(f"Error generating avatar: {str(e)}")
            return Response({
                'error': 'Failed to generate avatar'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def avatar_options(request):
    """Get available avatar customization options"""
    options = {
        'headwear': [
            {'value': 'bandana', 'name': 'Bandana'},
            {'value': 'crown', 'name': 'Crown'},
            {'value': 'cap', 'name': 'Cap'},
        ],
        'accessories': [
            {'value': 'scarf', 'name': 'Scarf'},
            {'value': 'earrings', 'name': 'Earrings'},
            {'value': 'glasses', 'name': 'Glasses'},
        ],
        'gender': [
            {'value': 'male', 'name': 'Male'},
            {'value': 'female', 'name': 'Female'},
        ],
        'favorite_color': [
            {'value': 'red', 'name': 'Red'},
            {'value': 'blue', 'name': 'Blue'},
            {'value': 'green', 'name': 'Green'},
            {'value': 'yellow', 'name': 'Yellow'},
            {'value': 'purple', 'name': 'Purple'},
            {'value': 'orange', 'name': 'Orange'},
            {'value': 'pink', 'name': 'Pink'},
            {'value': 'black', 'name': 'Black'},
            {'value': 'white', 'name': 'White'},
            {'value': 'brown', 'name': 'Brown'},
        ]
    }
    return Response(options)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def available_games(request):
    """Get available game sessions"""
    sessions = GameSession.objects.filter(
        status__in=['waiting', 'lobby']
    ).exclude(
        players__user=request.user
    )
    serializer = GameSessionSerializer(sessions, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_game(request):
    """Create a new game session"""
    # Accept optional settings from request.data
    max_players = request.data.get('max_players', 80)
    entry_fee = request.data.get('entry_fee', 200000)
    # Additional settings can be added as needed
    session = GameSession.objects.create(
        max_players=max_players,
        entry_fee=entry_fee
    )
    serializer = GameSessionSerializer(session)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def join_game(request, session_id):
    """Join a game session"""
    session = get_object_or_404(GameSession, session_id=session_id)
    
    # Check if user already joined
    if session.players.filter(user=request.user).exists():
        return Response({
            'error': 'Already joined this game'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if game is full
    if session.players.count() >= session.max_players:
        return Response({
            'error': 'Game is full'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if user has enough balance
    if request.user.balance < session.entry_fee:
        return Response({
            'error': 'Insufficient balance'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Deduct entry fee
    request.user.balance -= session.entry_fee
    request.user.save()
    
    # Add to prize pool
    session.prize_pool += session.entry_fee
    session.save()
    
    # Find next available player number
    taken_numbers = set(session.players.values_list('player_number', flat=True))
    player_number = next(i for i in range(1, session.max_players + 1) if i not in taken_numbers)
    
    # Create player
    player = Player.objects.create(
        user=request.user,
        session=session,
        player_number=player_number
    )
    
    return Response({
        'message': 'Successfully joined game',
        'player_number': player_number
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def quiz_questions(request):
    """Get quiz questions for the game"""
    questions = QuizQuestion.objects.filter(is_active=True).order_by('?')[:6]
    
    questions_data = []
    for question in questions:
        questions_data.append({
            'id': question.id,
            'question_text': question.question_text,
            'options': {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d
            },
            'difficulty': question.difficulty,
            'category': question.category
        })
    
    return Response({
        'questions': questions_data,
        'total_questions': len(questions_data)
    })
