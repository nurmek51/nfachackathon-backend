from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, GameSession, Player, ChatMessage, Purchase

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['nickname', 'email', 'password', 'confirm_password']
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    nickname = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, data):
        user = authenticate(username=data['nickname'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        data['user'] = user
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'nickname', 'balance', 'avatar_color', 'avatar_pattern', 
                 'total_games_played', 'total_games_won', 'total_earnings', 'created_at']
        read_only_fields = ['id', 'nickname', 'total_games_played', 'total_games_won', 
                           'total_earnings', 'created_at']

class GameSessionSerializer(serializers.ModelSerializer):
    alive_players_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GameSession
        fields = ['session_id', 'status', 'max_players', 'entry_fee', 'prize_pool', 
                 'current_stage', 'alive_players_count', 'created_at']
    
    def get_alive_players_count(self, obj):
        return obj.get_alive_players().count()

class PlayerSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source='user.nickname', read_only=True)
    avatar_color = serializers.CharField(source='user.avatar_color', read_only=True)
    avatar_pattern = serializers.CharField(source='user.avatar_pattern', read_only=True)
    
    class Meta:
        model = Player
        fields = ['player_number', 'nickname', 'avatar_color', 'avatar_pattern', 
                 'is_alive', 'position_x', 'position_y', 'joined_at']

class ChatMessageSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source='player.user.nickname', read_only=True)
    player_number = serializers.IntegerField(source='player.player_number', read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'message', 'nickname', 'player_number', 'timestamp', 'is_system_message']

class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ['item_type', 'item_value', 'cost']
        
    def create(self, validated_data):
        user = self.context['request'].user
        if user.balance < validated_data['cost']:
            raise serializers.ValidationError("Insufficient balance")
        
        purchase = Purchase.objects.create(user=user, **validated_data)
        user.balance -= validated_data['cost']
        
        # Apply the purchase
        if validated_data['item_type'] == 'color':
            user.avatar_color = validated_data['item_value']
        elif validated_data['item_type'] == 'pattern':
            user.avatar_pattern = validated_data['item_value']
        
        user.save()
        return purchase 