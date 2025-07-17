from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import User, GameSession, Player, Purchase
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    GameSessionSerializer, PlayerSerializer, PurchaseSerializer
)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
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
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
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
    """Update user profile (avatar customization)"""
    serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
            'win_rate': (player.total_games_won / player.total_games_played * 100) if player.total_games_played > 0 else 0
        })
    
    return Response(hall_of_fame)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def available_items(request):
    """Get available items for purchase"""
    items = {
        'colors': [
            {'value': '#FF6B6B', 'name': 'Red', 'cost': 10000},
            {'value': '#4ECDC4', 'name': 'Teal', 'cost': 10000},
            {'value': '#45B7D1', 'name': 'Blue', 'cost': 10000},
            {'value': '#96CEB4', 'name': 'Green', 'cost': 10000},
            {'value': '#FFEAA7', 'name': 'Yellow', 'cost': 10000},
            {'value': '#DDA0DD', 'name': 'Purple', 'cost': 15000},
            {'value': '#FFD700', 'name': 'Gold', 'cost': 25000},
            {'value': '#FF1493', 'name': 'Pink', 'cost': 15000},
        ],
        'patterns': [
            {'value': 'solid', 'name': 'Solid', 'cost': 0},
            {'value': 'stripes', 'name': 'Stripes', 'cost': 5000},
            {'value': 'dots', 'name': 'Dots', 'cost': 5000},
            {'value': 'gradient', 'name': 'Gradient', 'cost': 8000},
            {'value': 'diamond', 'name': 'Diamond', 'cost': 12000},
            {'value': 'stars', 'name': 'Stars', 'cost': 15000},
        ]
    }
    return Response(items)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def purchase_item(request):
    """Purchase avatar customization item"""
    serializer = PurchaseSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Item purchased successfully'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
