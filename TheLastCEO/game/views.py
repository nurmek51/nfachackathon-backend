from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import User, GameSession, Player
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
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id': user.id,
            'nickname': user.nickname,
            'balance': user.balance
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile(request):
    """Get user profile"""
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    """Update user profile (non-avatar fields only)"""
    # Only allow updating certain fields, not avatar-related fields
    allowed_fields = {}
    # Currently no updatable fields in the profile, but keeping the endpoint for future use
    
    serializer = UserProfileSerializer(request.user, data=allowed_fields, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_avatar(request):
    """Generate a new avatar based on user's customization choices"""
    serializer = AvatarCustomizationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    headwear = serializer.validated_data['headwear']
    accessory = serializer.validated_data['accessory']
    gender = serializer.validated_data['gender']
    favorite_color = serializer.validated_data['favorite_color']
    
    # Check if avatar generation is already in progress
    if user.avatar_generation_in_progress:
        return Response({
            'error': 'Avatar generation already in progress. Please wait.'
        }, status=status.HTTP_409_CONFLICT)
    
    try:
        # Set generation in progress flag
        user.avatar_generation_in_progress = True
        user.avatar_headwear = headwear
        user.avatar_accessory = accessory
        user.avatar_gender = gender
        user.avatar_favorite_color = favorite_color
        user.save()
        
        # Generate and upload avatar
        success, avatar_url = avatar_service.generate_and_upload_avatar(
            user.id, headwear, accessory, gender, favorite_color
        )
        
        if success and avatar_url:
            # Update user with new avatar URL
            user.avatar_url = avatar_url
            user.avatar_generation_in_progress = False
            user.save()
            
            logger.info(f"Avatar generated successfully for user {user.id}")
            return Response({
                'message': 'Avatar generated successfully',
                'avatar_url': avatar_url,
                'headwear': headwear,
                'accessory': accessory,
                'gender': gender,
                'favorite_color': favorite_color
            }, status=status.HTTP_201_CREATED)
        else:
            # Reset generation flag on failure
            user.avatar_generation_in_progress = False
            user.save()
            
            logger.error(f"Avatar generation failed for user {user.id}")
            return Response({
                'error': 'Failed to generate avatar. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        # Reset generation flag on exception
        user.avatar_generation_in_progress = False
        user.save()
        
        logger.error(f"Exception during avatar generation for user {user.id}: {str(e)}")
        return Response({
            'error': 'An error occurred during avatar generation. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
    
    if session.status not in ['waiting', 'lobby']:
        return Response({'error': 'Game already started'}, status=status.HTTP_400_BAD_REQUEST)
    
    if session.players.count() >= session.max_players:
        return Response({'error': 'Game is full'}, status=status.HTTP_400_BAD_REQUEST)
    
    if session.players.filter(user=request.user).exists():
        return Response({'error': 'Already in this game'}, status=status.HTTP_400_BAD_REQUEST)
    
    if request.user.balance < session.entry_fee:
        return Response({'error': 'Insufficient balance'}, status=status.HTTP_402_PAYMENT_REQUIRED)
    
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
        'player_number': player_number,
        'session_id': session.session_id
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def game_statistics(request):
    """Get user's game statistics"""
    user_stats = {
        'total_games': request.user.total_games_played,
        'total_wins': request.user.total_games_won,
        'win_rate': (request.user.total_games_won / request.user.total_games_played * 100) if request.user.total_games_played > 0 else 0,
        'total_earnings': request.user.total_earnings,
        'current_balance': request.user.balance
    }
    return Response(user_stats)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def hall_of_fame(request):
    """Get hall of fame - top players"""
    top_players = User.objects.filter(
        total_games_played__gt=0
    ).order_by('-total_earnings')[:10]
    
    hall_of_fame = []
    for i, player in enumerate(top_players, 1):
        hall_of_fame.append({
            'rank': i,
            'nickname': player.nickname,
            'total_earnings': player.total_earnings,
            'games_played': player.total_games_played,
            'games_won': player.total_games_won,
            'win_rate': (player.total_games_won / player.total_games_played * 100) if player.total_games_played > 0 else 0,
            'avatar_url': player.avatar_url
        })
    
    return Response(hall_of_fame)
