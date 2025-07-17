import json
import asyncio
from datetime import datetime, timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import GameSession, Player, QuizQuestion, QuizAnswer, RedLightMovement, ChatMessage
import random
import math

class GameConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'game_{self.session_id}'
        self.user = self.scope['user']
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Get player info and send initial state
        player = await self.get_player()
        if player:
            await self.send_game_state()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            await self.handle_chat_message(data)
        elif message_type == 'quiz_answer':
            await self.handle_quiz_answer(data)
        elif message_type == 'player_movement':
            await self.handle_player_movement(data)
        elif message_type == 'ready_check':
            await self.handle_ready_check(data)
    
    async def handle_chat_message(self, data):
        """Handle chat messages"""
        player = await self.get_player()
        if not player:
            return
        
        message = data.get('message', '').strip()
        if not message:
            return
        
        # Save chat message
        await self.save_chat_message(player, message)
        
        # Broadcast to all players
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'player_number': player.player_number,
                    'nickname': player.user.nickname,
                    'message': message,
                    'timestamp': timezone.now().isoformat()
                }
            }
        )
    
    async def handle_quiz_answer(self, data):
        """Handle quiz answer submission"""
        player = await self.get_player()
        if not player or not player.is_alive:
            return
        
        session = await self.get_session()
        if session.status != 'quiz':
            return
        
        question_id = data['question_id']
        answer = data['answer']
        time_taken = data.get('time_taken', 0)
        
        # Check if player already answered this question
        already_answered = await self.check_if_already_answered(player, question_id)
        if already_answered:
            return
        
        # Save answer and check if correct
        is_correct = await self.save_quiz_answer(player, question_id, answer, time_taken)
        
        # Broadcast answer received (for real-time feedback)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'quiz_answer_received',
                'answer_data': {
                    'player_number': player.player_number,
                    'nickname': player.user.nickname,
                    'question_id': question_id,
                    'answer': answer,
                    'is_correct': is_correct,
                    'time_taken': time_taken
                }
            }
        )
    
    async def handle_player_movement(self, data):
        """Handle player movement in Red Light Green Light"""
        player = await self.get_player()
        if not player or not player.is_alive:
            return
        
        session = await self.get_session()
        if session.status != 'red_light':
            return
        
        new_x = data['x']
        new_y = data['y']
        
        # Check if movement is allowed (green light)
        is_red_light = await self.is_red_light_active()
        
        if is_red_light:
            # Player moved during red light - eliminate
            await self.eliminate_player(player, 'red_light')
        else:
            # Update player position
            await self.update_player_position(player, new_x, new_y)
            
            # Broadcast position update
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player_movement',
                    'player_number': player.player_number,
                    'x': new_x,
                    'y': new_y
                }
            )
    
    async def handle_ready_check(self, data):
        """Handle player ready status"""
        player = await self.get_player()
        if not player:
            return
        
        # Mark player as ready and check if all players are ready
        ready_count = await self.get_ready_count()
        total_alive = await self.get_alive_count()
        
        if ready_count >= total_alive and total_alive > 0:
            await self.start_next_stage()
    
    # WebSocket event handlers
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'data': event['message']
        }))
    
    async def game_state_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_state_update',
            'data': event['state']
        }))
    
    async def player_eliminated(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_eliminated',
            'data': event['elimination']
        }))
    
    async def stage_transition(self, event):
        await self.send(text_data=json.dumps({
            'type': 'stage_transition',
            'data': event['stage_info']
        }))
    
    async def quiz_question(self, event):
        await self.send(text_data=json.dumps({
            'type': 'quiz_question',
            'data': event['question']
        }))
    
    async def quiz_answer_received(self, event):
        await self.send(text_data=json.dumps({
            'type': 'quiz_answer_received',
            'data': event['answer_data']
        }))
    
    async def quiz_results(self, event):
        await self.send(text_data=json.dumps({
            'type': 'quiz_results',
            'data': event['results']
        }))
    
    async def red_light_signal(self, event):
        await self.send(text_data=json.dumps({
            'type': 'red_light_signal',
            'data': event['signal']
        }))
    
    async def player_movement(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_movement',
            'data': {
                'player_number': event['player_number'],
                'x': event['x'],
                'y': event['y']
            }
        }))
    
    async def game_finished(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_finished',
            'data': event['results']
        }))
    
    # Database operations
    @database_sync_to_async
    def get_player(self):
        try:
            return Player.objects.select_related('user').get(
                session__session_id=self.session_id,
                user=self.user
            )
        except Player.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_session(self):
        return GameSession.objects.get(session_id=self.session_id)
    
    @database_sync_to_async
    def save_chat_message(self, player, message):
        return ChatMessage.objects.create(
            session=player.session,
            player=player,
            message=message
        )
    
    @database_sync_to_async
    def check_if_already_answered(self, player, question_id):
        return QuizAnswer.objects.filter(
            player=player,
            question_id=question_id
        ).exists()
    
    @database_sync_to_async
    def save_quiz_answer(self, player, question_id, answer, time_taken):
        question = QuizQuestion.objects.get(id=question_id)
        is_correct = question.correct_answer == answer
        
        QuizAnswer.objects.create(
            player=player,
            session=player.session,
            question=question,
            answer=answer,
            is_correct=is_correct,
            time_taken=time_taken
        )
        
        return is_correct
    
    @database_sync_to_async
    def eliminate_player(self, player, stage):
        player.is_alive = False
        player.eliminated_at = timezone.now()
        player.elimination_stage = {
            'quiz': 1,
            'red_light': 2
        }[stage]
        player.save()
        
        # Send elimination notification
        asyncio.create_task(self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_eliminated',
                'elimination': {
                    'player_number': player.player_number,
                    'nickname': player.user.nickname,
                    'stage': stage,
                    'eliminated_at': player.eliminated_at.isoformat()
                }
            }
        ))
    
    @database_sync_to_async
    def update_player_position(self, player, x, y):
        player.position_x = x
        player.position_y = y
        player.save()
    
    @database_sync_to_async
    def get_alive_count(self):
        session = GameSession.objects.get(session_id=self.session_id)
        return session.get_alive_players().count()
    
    @database_sync_to_async
    def get_ready_count(self):
        # This would track ready status - simplified for demo
        return 1
    
    @database_sync_to_async
    def is_red_light_active(self):
        # This would check current red light status
        # For demo, return random
        return random.choice([True, False])
    
    async def send_game_state(self):
        """Send current game state to client"""
        session = await self.get_session()
        players = await self.get_session_players()
        
        state = {
            'session_id': str(session.session_id),
            'status': session.status,
            'current_stage': session.current_stage,
            'prize_pool': float(session.prize_pool),
            'players': players,
            'timestamp': timezone.now().isoformat()
        }
        
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'data': state
        }))
    
    @database_sync_to_async
    def get_session_players(self):
        session = GameSession.objects.get(session_id=self.session_id)
        players = []
        for player in session.players.select_related('user').all():
            players.append({
                'player_number': player.player_number,
                'nickname': player.user.nickname,
                'avatar_color': player.user.avatar_favorite_color,
                'is_alive': player.is_alive,
                'position_x': player.position_x,
                'position_y': player.position_y
            })
        return players
    
    async def start_next_stage(self):
        """Start the next game stage"""
        session = await self.get_session()
        
        if session.status == 'lobby':
            await self.start_quiz_stage()
        elif session.status == 'quiz':
            await self.start_red_light_stage()
        elif session.status == 'red_light':
            await self.start_freedom_room()
    
    async def start_quiz_stage(self):
        """Start quiz stage with real-time answers like Kahoot"""
        await self.update_session_status('quiz')
        questions = await self.get_quiz_questions()
        
        for i, question in enumerate(questions):
            # Send question to all players
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'quiz_question',
                    'question': {
                        'id': question.id,
                        'question_number': i + 1,
                        'total_questions': len(questions),
                        'question': question.question_text,
                        'options': {
                            'A': question.option_a,
                            'B': question.option_b,
                            'C': question.option_c,
                            'D': question.option_d
                        },
                        'time_limit': 30
                    }
                }
            )
            
            # Wait for answers with real-time tracking
            await self.wait_for_quiz_answers(question.id, 30)
            
            # Show results for this question
            await self.show_question_results(question.id)
            
            # Wait a bit before next question
            await asyncio.sleep(3)
        
        # Process final quiz results and eliminate players
        await self.process_quiz_results()
    
    async def wait_for_quiz_answers(self, question_id, time_limit):
        """Wait for answers with real-time tracking"""
        start_time = timezone.now()
        answered_players = set()
        
        while (timezone.now() - start_time).total_seconds() < time_limit:
            # Check for new answers
            new_answers = await self.get_new_answers(question_id, answered_players)
            
            for answer in new_answers:
                answered_players.add(answer['player_number'])
                # Broadcast answer received
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'quiz_answer_received',
                        'answer_data': answer
                    }
                )
            
            await asyncio.sleep(0.5)  # Check every 500ms
    
    @database_sync_to_async
    def get_new_answers(self, question_id, answered_players):
        """Get new answers for a question"""
        answers = QuizAnswer.objects.filter(
            question_id=question_id,
            session__session_id=self.session_id
        ).select_related('player__user')
        
        new_answers = []
        for answer in answers:
            if answer.player.player_number not in answered_players:
                new_answers.append({
                    'player_number': answer.player.player_number,
                    'nickname': answer.player.user.nickname,
                    'question_id': question_id,
                    'answer': answer.answer,
                    'is_correct': answer.is_correct,
                    'time_taken': answer.time_taken
                })
        
        return new_answers
    
    async def show_question_results(self, question_id):
        """Show results for a specific question"""
        results = await self.get_question_results(question_id)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'quiz_results',
                'results': {
                    'question_id': question_id,
                    'correct_answer': results['correct_answer'],
                    'answer_stats': results['answer_stats'],
                    'player_results': results['player_results']
                }
            }
        )
    
    @database_sync_to_async
    def get_question_results(self, question_id):
        """Get results for a specific question"""
        question = QuizQuestion.objects.get(id=question_id)
        answers = QuizAnswer.objects.filter(
            question_id=question_id,
            session__session_id=self.session_id
        ).select_related('player__user')
        
        # Count answers for each option
        answer_stats = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        player_results = []
        
        for answer in answers:
            answer_stats[answer.answer] += 1
            player_results.append({
                'player_number': answer.player.player_number,
                'nickname': answer.player.user.nickname,
                'answer': answer.answer,
                'is_correct': answer.is_correct,
                'time_taken': answer.time_taken
            })
        
        return {
            'correct_answer': question.correct_answer,
            'answer_stats': answer_stats,
            'player_results': player_results
        }
    
    async def start_red_light_stage(self):
        """Start Red Light Green Light stage"""
        await self.update_session_status('red_light')
        
        # Send stage transition
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'stage_transition',
                'stage_info': {
                    'stage': 'red_light',
                    'duration': 180,
                    'instructions': 'Move forward when green light is on. Stop when red light is on!'
                }
            }
        )
        
        # Run red light green light sequence
        await self.run_red_light_sequence()
    
    async def start_freedom_room(self):
        """Start Freedom Room - distribute prizes"""
        await self.update_session_status('freedom_room')
        
        # Calculate and distribute prizes
        await self.distribute_prizes()
    
    @database_sync_to_async
    def update_session_status(self, status):
        session = GameSession.objects.get(session_id=self.session_id)
        session.status = status
        session.stage_start_time = timezone.now()
        session.save()
    
    @database_sync_to_async
    def get_quiz_questions(self):
        return list(QuizQuestion.objects.filter(is_active=True).order_by('?')[:6])
    
    async def process_quiz_results(self):
        """Process quiz results and eliminate players"""
        # Get all quiz answers and eliminate bottom performers
        session = await self.get_session()
        players = await self.get_alive_players()
        
        # Calculate scores based on correct answers and speed
        player_scores = await self.calculate_player_scores()
        
        # Sort players by score and eliminate bottom 30%
        elimination_count = max(1, len(players) * 30 // 100)
        
        # Eliminate players with lowest scores
        for i in range(elimination_count):
            if player_scores:
                worst_player = min(player_scores, key=lambda x: x['score'])
                player = await self.get_player_by_number(worst_player['player_number'])
                if player:
                    await self.eliminate_player(player, 'quiz')
                player_scores.remove(worst_player)
    
    @database_sync_to_async
    def calculate_player_scores(self):
        """Calculate scores for all players based on quiz performance"""
        session = GameSession.objects.get(session_id=self.session_id)
        players = session.get_alive_players()
        
        player_scores = []
        for player in players:
            answers = QuizAnswer.objects.filter(
                player=player,
                session=session
            )
            
            correct_answers = answers.filter(is_correct=True).count()
            total_time = sum(answer.time_taken for answer in answers if answer.is_correct)
            
            # Score based on correct answers and speed (lower time = higher score)
            score = correct_answers * 100 - total_time
            player_scores.append({
                'player_number': player.player_number,
                'score': score,
                'correct_answers': correct_answers,
                'total_time': total_time
            })
        
        return player_scores
    
    @database_sync_to_async
    def get_player_by_number(self, player_number):
        """Get player by player number"""
        try:
            return Player.objects.get(
                session__session_id=self.session_id,
                player_number=player_number
            )
        except Player.DoesNotExist:
            return None
    
    async def run_red_light_sequence(self):
        """Run the red light green light sequence"""
        total_time = 180  # 3 minutes
        current_time = 0
        
        while current_time < total_time:
            # Green light period
            green_duration = random.randint(3, 8)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'red_light_signal',
                    'signal': {
                        'state': 'green',
                        'duration': green_duration
                    }
                }
            )
            
            await asyncio.sleep(green_duration)
            current_time += green_duration
            
            # Red light period
            red_duration = random.randint(2, 5)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'red_light_signal',
                    'signal': {
                        'state': 'red',
                        'duration': red_duration
                    }
                }
            )
            
            await asyncio.sleep(red_duration)
            current_time += red_duration
        
        # Eliminate players who didn't reach the end
        await self.eliminate_slow_players()
    
    @database_sync_to_async
    def distribute_prizes(self):
        """Distribute prizes to winners"""
        session = GameSession.objects.get(session_id=self.session_id)
        winners = session.get_alive_players()
        
        if winners.exists():
            prize_per_winner = session.prize_pool / winners.count()
            
            results = []
            for player in winners:
                player.final_prize = prize_per_winner
                player.save()
                
                # Update user balance and stats
                user = player.user
                user.balance += prize_per_winner
                user.total_earnings += prize_per_winner
                user.total_games_won += 1
                user.save()
                
                results.append({
                    'player_number': player.player_number,
                    'nickname': user.nickname,
                    'prize': float(prize_per_winner)
                })
            
            # Send final results
            asyncio.create_task(self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_finished',
                    'results': {
                        'winners': results,
                        'total_prize_pool': float(session.prize_pool)
                    }
                }
            ))
        
        # Update session status
        session.status = 'finished'
        session.finished_at = timezone.now()
        session.save()
    
    @database_sync_to_async
    def get_alive_players(self):
        session = GameSession.objects.get(session_id=self.session_id)
        return list(session.get_alive_players())
    
    @database_sync_to_async
    def eliminate_slow_players(self):
        """Eliminate players who didn't reach the finish line"""
        session = GameSession.objects.get(session_id=self.session_id)
        alive_players = session.get_alive_players()
        
        # Eliminate players who didn't move far enough (simplified)
        for player in alive_players:
            if player.position_x < 90:  # Didn't reach 90% of the way
                player.is_alive = False
                player.eliminated_at = timezone.now()
                player.elimination_stage = 2
                player.save()
    
    async def check_quiz_completion(self):
        """Check if quiz stage is complete"""
        # This would check if all players have answered
        # For demo, we'll assume it's complete after a delay
        pass 