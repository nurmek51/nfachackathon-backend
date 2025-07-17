from django.contrib import admin
from django.db import models

# Register your models here.

from .models import User, GameSession, Player, QuizQuestion, QuizAnswer, RedLightMovement, HoneycombShape, HoneycombAttempt, ChatMessage, GameStatistics

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'nickname', 'email', 'balance', 'avatar_url', 'avatar_headwear', 'avatar_accessory', 'avatar_gender', 'avatar_favorite_color', 'total_games_played', 'total_games_won', 'total_earnings', 'created_at')
    list_filter = ('avatar_headwear', 'avatar_accessory', 'avatar_gender', 'avatar_favorite_color', 'created_at')
    search_fields = ('nickname', 'email')
    readonly_fields = ('created_at', 'last_active', 'total_games_played', 'total_games_won', 'total_earnings')

class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0
    readonly_fields = ('user', 'player_number', 'is_alive', 'joined_at', 'eliminated_at', 'final_prize')

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_id', 'status', 'max_players', 'entry_fee', 'prize_pool', 'current_stage', 'created_at', 'started_at', 'finished_at')
    list_filter = ('status', 'created_at', 'started_at', 'finished_at')
    search_fields = ('session_id',)
    readonly_fields = ('created_at', 'started_at', 'finished_at')
    inlines = [PlayerInline]
    actions = ['start_game', 'end_game']

    def start_game(self, request, queryset):
        updated = queryset.update(status='lobby', started_at=models.functions.Now())
        self.message_user(request, f"{updated} game(s) started.")
    start_game.short_description = "Start selected games"

    def end_game(self, request, queryset):
        updated = queryset.update(status='finished', finished_at=models.functions.Now())
        self.message_user(request, f"{updated} game(s) ended.")
    end_game.short_description = "End selected games"

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session', 'player_number', 'is_alive', 'joined_at', 'eliminated_at', 'final_prize')
    list_filter = ('is_alive', 'joined_at', 'eliminated_at')
    search_fields = ('user__nickname', 'session__session_id')

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_text', 'difficulty', 'category', 'is_active')
    list_filter = ('difficulty', 'category', 'is_active')
    search_fields = ('question_text',)

@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'player', 'session', 'question', 'answer', 'is_correct', 'answered_at', 'time_taken')
    list_filter = ('is_correct', 'answered_at')
    search_fields = ('player__user__nickname', 'session__session_id', 'question__question_text')

@admin.register(RedLightMovement)
class RedLightMovementAdmin(admin.ModelAdmin):
    list_display = ('id', 'player', 'session', 'from_x', 'from_y', 'to_x', 'to_y', 'timestamp', 'is_during_red_light', 'eliminated')
    list_filter = ('is_during_red_light', 'eliminated', 'timestamp')
    search_fields = ('player__user__nickname', 'session__session_id')

@admin.register(HoneycombShape)
class HoneycombShapeAdmin(admin.ModelAdmin):
    list_display = ('id', 'shape_type', 'difficulty', 'time_limit')
    list_filter = ('shape_type', 'difficulty')
    search_fields = ('shape_type',)

@admin.register(HoneycombAttempt)
class HoneycombAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'player', 'session', 'shape', 'accuracy_score', 'success', 'completed_at', 'time_taken')
    list_filter = ('success', 'completed_at')
    search_fields = ('player__user__nickname', 'session__session_id')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'player', 'message', 'timestamp', 'is_system_message')
    list_filter = ('is_system_message', 'timestamp')
    search_fields = ('player__user__nickname', 'session__session_id', 'message')

@admin.register(GameStatistics)
class GameStatisticsAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'total_players', 'quiz_eliminations', 'red_light_eliminations', 'honeycomb_eliminations', 'winners_count', 'total_prize_distributed', 'average_survival_time', 'created_at')
    search_fields = ('session__session_id',)
    readonly_fields = ('created_at',)
