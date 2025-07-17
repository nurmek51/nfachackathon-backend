from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json

class CustomUserManager(UserManager):
    def create_user(self, nickname, email=None, password=None, **extra_fields):
        if not nickname:
            raise ValueError('The Nickname must be set')
        email = self.normalize_email(email)
        user = self.model(nickname=nickname, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, nickname, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(nickname, email, password, **extra_fields)

class User(AbstractUser):
    username = None  # Remove the username field
    nickname = models.CharField(max_length=30, unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=200000)
    avatar_url = models.URLField(max_length=500, null=True, blank=True)
    avatar_headwear = models.CharField(max_length=20, choices=[
        ('bandana', 'Bandana'),
        ('crown', 'Crown'),
        ('cap', 'Cap'),
    ], null=True, blank=True)
    avatar_accessory = models.CharField(max_length=20, choices=[
        ('scarf', 'Scarf'),
        ('earrings', 'Earrings'),
        ('glasses', 'Glasses'),
    ], null=True, blank=True)
    avatar_gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
    ], null=True, blank=True)
    avatar_favorite_color = models.CharField(max_length=20, choices=[
        ('red', 'Red'),
        ('blue', 'Blue'),
        ('green', 'Green'),
        ('yellow', 'Yellow'),
        ('purple', 'Purple'),
        ('orange', 'Orange'),
        ('pink', 'Pink'),
        ('black', 'Black'),
        ('white', 'White'),
        ('brown', 'Brown'),
    ], null=True, blank=True)
    avatar_generation_in_progress = models.BooleanField(default=False)
    total_games_played = models.IntegerField(default=0)
    total_games_won = models.IntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'nickname'
    REQUIRED_FIELDS = ['email']
    objects = CustomUserManager()

class GameSession(models.Model):
    """Main game session model"""
    STATUS_CHOICES = [
        ('waiting', 'Waiting for Players'),
        ('lobby', 'In Lobby'),
        ('quiz', 'Quiz Stage'),
        ('red_light', 'Red Light Green Light'),
        ('honeycomb', 'Honeycomb Stage'),
        ('freedom_room', 'Freedom Room'),
        ('finished', 'Finished'),
    ]
    
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    max_players = models.IntegerField(default=80)
    entry_fee = models.DecimalField(max_digits=12, decimal_places=2, default=200000)
    prize_pool = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_stage = models.IntegerField(default=0)
    stage_start_time = models.DateTimeField(null=True, blank=True)
    stage_duration = models.IntegerField(default=30)  # seconds
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    def get_alive_players(self):
        return self.players.filter(is_alive=True)
    
    def get_eliminated_players(self):
        return self.players.filter(is_alive=False)

class Player(models.Model):
    """Player in a specific game session"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_participations')
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='players')
    player_number = models.IntegerField()  # 001-080
    is_alive = models.BooleanField(default=True)
    elimination_stage = models.IntegerField(null=True, blank=True)
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)
    eliminated_at = models.DateTimeField(null=True, blank=True)
    final_prize = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['session', 'player_number']
        unique_together = ['session', 'user']

class QuizQuestion(models.Model):
    """Quiz questions for stage 1"""
    question_text = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    difficulty = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    category = models.CharField(max_length=50, default='general')
    is_active = models.BooleanField(default=True)

class QuizAnswer(models.Model):
    """Player answers for quiz questions"""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='quiz_answers')
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)
    time_taken = models.FloatField()  # seconds

class RedLightMovement(models.Model):
    """Track player movements during Red Light Green Light"""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='movements')
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    from_x = models.FloatField()
    from_y = models.FloatField()
    to_x = models.FloatField()
    to_y = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_during_red_light = models.BooleanField(default=False)
    eliminated = models.BooleanField(default=False)

class HoneycombShape(models.Model):
    """Honeycomb shapes for stage 3"""
    SHAPE_CHOICES = [
        ('circle', 'Circle'),
        ('triangle', 'Triangle'),
        ('square', 'Square'),
        ('star', 'Star'),
        ('heart', 'Heart'),
    ]
    
    shape_type = models.CharField(max_length=20, choices=SHAPE_CHOICES)
    svg_path = models.TextField()  # SVG path data
    tolerance = models.FloatField(default=0.1)  # Drawing tolerance
    time_limit = models.IntegerField(default=120)  # seconds
    difficulty = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])

class HoneycombAttempt(models.Model):
    """Player attempts at honeycomb shapes"""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='honeycomb_attempts')
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    shape = models.ForeignKey(HoneycombShape, on_delete=models.CASCADE)
    drawing_data = models.JSONField()  # Path coordinates
    accuracy_score = models.FloatField()
    success = models.BooleanField()
    completed_at = models.DateTimeField(auto_now_add=True)
    time_taken = models.FloatField()

class ChatMessage(models.Model):
    """Chat messages in lobby and freedom room"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='chat_messages')
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    message = models.TextField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_system_message = models.BooleanField(default=False)

class GameStatistics(models.Model):
    """Overall game statistics"""
    session = models.OneToOneField(GameSession, on_delete=models.CASCADE, related_name='statistics')
    total_players = models.IntegerField()
    quiz_eliminations = models.IntegerField(default=0)
    red_light_eliminations = models.IntegerField(default=0)
    honeycomb_eliminations = models.IntegerField(default=0)
    winners_count = models.IntegerField(default=0)
    total_prize_distributed = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_survival_time = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
