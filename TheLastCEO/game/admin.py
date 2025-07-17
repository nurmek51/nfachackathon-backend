from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, GameSession, Player, QuizQuestion, QuizAnswer, RedLightMovement, ChatMessage, GameStatistics

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('nickname', 'email', 'balance', 'total_games_played', 'total_games_won', 'total_earnings', 'is_active', 'created_at')
    list_filter = ('is_active', 'avatar_gender', 'avatar_favorite_color', 'created_at')
    search_fields = ('nickname', 'email')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('nickname', 'password')}),
        ('Personal info', {'fields': ('email', 'first_name', 'last_name')}),
        ('Avatar', {'fields': ('avatar_url', 'avatar_headwear', 'avatar_accessory', 'avatar_gender', 'avatar_favorite_color')}),
        ('Game Stats', {'fields': ('balance', 'total_games_played', 'total_games_won', 'total_earnings')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('nickname', 'email', 'password1', 'password2'),
        }),
    )

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'status', 'max_players', 'entry_fee', 'prize_pool', 'current_stage', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('session_id',)
    readonly_fields = ('session_id', 'created_at', 'started_at', 'finished_at')

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('player_number', 'user', 'session', 'is_alive', 'elimination_stage', 'final_prize', 'joined_at')
    list_filter = ('is_alive', 'elimination_stage', 'joined_at')
    search_fields = ('user__nickname', 'session__session_id')

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'correct_answer', 'difficulty', 'category', 'is_active')
    list_filter = ('difficulty', 'category', 'is_active')
    search_fields = ('question_text',)

@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ('player', 'question', 'answer', 'is_correct', 'time_taken', 'answered_at')
    list_filter = ('is_correct', 'answered_at')
    search_fields = ('player__user__nickname', 'question__question_text')

@admin.register(RedLightMovement)
class RedLightMovementAdmin(admin.ModelAdmin):
    list_display = ('player', 'session', 'from_x', 'from_y', 'to_x', 'to_y', 'is_during_red_light', 'eliminated', 'timestamp')
    list_filter = ('is_during_red_light', 'eliminated', 'timestamp')
    search_fields = ('player__user__nickname', 'session__session_id')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('player', 'session', 'message', 'is_system_message', 'timestamp')
    list_filter = ('is_system_message', 'timestamp')
    search_fields = ('player__user__nickname', 'message')

@admin.register(GameStatistics)
class GameStatisticsAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'total_players', 'quiz_eliminations', 'red_light_eliminations', 'winners_count', 'total_prize_distributed', 'average_survival_time', 'created_at')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
