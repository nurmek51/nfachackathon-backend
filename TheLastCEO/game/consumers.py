import json
import asyncio
from datetime import datetime, timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import GameSession, Player, QuizQuestion, QuizAnswer, RedLightMovement, HoneycombShape, HoneycombAttempt, ChatMessage
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
        elif message_type == 'honeycomb_drawing':
            await self.handle_honeycomb_drawing(data)
        elif message_type == 'ready_check':
            await self.handle_ready_check(data)
    
    async def handle_chat_message(self, data):
        """Handle chat messages"""
        player = await self.get_player()
        if not player:
            return
        
        message = await self.save_chat_message(player, data['message'])
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'player_number': player.player_number,
                    'nickname': player.user.nickname,
                    'message': message.message,
                    'timestamp': message.timestamp.isoformat()
                }
            }
        )
    
    async def handle_quiz_answer(self, data):
        """Handle quiz answers"""
        player = await self.get_player()
        if not player or not player.is_alive:
            return
        
        session = await self.get_session()
        if session.status != 'quiz':
            return
        
        question_id = data['question_id']
        answer = data['answer']
        time_taken = data.get('time_taken', 0)
        
        # Save answer and check if correct
        is_correct = await self.save_quiz_answer(player, question_id, answer, time_taken)
        
        # Check if quiz stage is complete
        await self.check_quiz_completion()
    
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
    
    async def handle_honeycomb_drawing(self, data):
        """Handle honeycomb shape drawing"""
        player = await self.get_player()
        if not player or not player.is_alive:
            return
        
        session = await self.get_session()
        if session.status != 'honeycomb':
            return
        
        shape_id = data['shape_id']
        drawing_data = data['drawing_data']
        time_taken = data.get('time_taken', 0)
        
        # Validate drawing and save attempt
        success = await self.validate_honeycomb_drawing(player, shape_id, drawing_data, time_taken)
        
        if not success:
            await self.eliminate_player(player, 'honeycomb')
        
        # Check if honeycomb stage is complete
        await self.check_honeycomb_completion()
    
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
    
    async def red_light_signal(self, event):
        await self.send(text_data=json.dumps({
            'type': 'red_light_signal',
            'data': event['signal']
        }))
    
    async def honeycomb_shape(self, event):
        await self.send(text_data=json.dumps({
            'type': 'honeycomb_shape',
            'data': event['shape']
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
            'red_light': 2,
            'honeycomb': 3
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
    def validate_honeycomb_drawing(self, player, shape_id, drawing_data, time_taken):
        shape = HoneycombShape.objects.get(id=shape_id)
        
        # Calculate accuracy score (simplified - you'd implement actual path comparison)
        accuracy_score = self.calculate_drawing_accuracy(drawing_data, shape.svg_path)
        success = accuracy_score >= (1 - shape.tolerance)
        
        HoneycombAttempt.objects.create(
            player=player,
            session=player.session,
            shape=shape,
            drawing_data=drawing_data,
            accuracy_score=accuracy_score,
            success=success,
            time_taken=time_taken
        )
        
        return success
    
    def calculate_drawing_accuracy(self, drawing_data, target_path):
        """Calculate drawing accuracy (simplified implementation)"""
        # This would implement actual path comparison algorithm
        # For now, return a random score for demonstration
        return random.uniform(0.6, 1.0)
    
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
                'avatar_color': player.user.avatar_color,
                'avatar_pattern': player.user.avatar_pattern,
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
            await self.start_honeycomb_stage()
        elif session.status == 'honeycomb':
            await self.start_freedom_room()
    
    async def start_quiz_stage(self):
        """Start quiz stage"""
        await self.update_session_status('quiz')
        questions = await self.get_quiz_questions()
        
        for question in questions:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'quiz_question',
                    'question': {
                        'id': question.id,
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
            
            # Wait for answers
            await asyncio.sleep(30)
        
        # Process quiz results
        await self.process_quiz_results()
    
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
    
    async def start_honeycomb_stage(self):
        """Start Honeycomb stage"""
        await self.update_session_status('honeycomb')
        
        # Assign shapes to players
        await self.assign_honeycomb_shapes()
    
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
        return list(QuizQuestion.objects.filter(is_active=True).order_by('?')[:10])
    
    async def process_quiz_results(self):
        """Process quiz results and eliminate players"""
        # Get all quiz answers and eliminate bottom performers
        session = await self.get_session()
        players = await self.get_alive_players()
        
        # Calculate scores and eliminate bottom 30%
        elimination_count = max(1, len(players) * 30 // 100)
        
        # This would implement actual scoring logic
        # For now, randomly eliminate players
        for _ in range(elimination_count):
            if players:
                player = random.choice(players)
                await self.eliminate_player(player, 'quiz')
                players.remove(player)
    
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
    def assign_honeycomb_shapes(self):
        """Assign honeycomb shapes to remaining players"""
        session = GameSession.objects.get(session_id=self.session_id)
        alive_players = session.get_alive_players()
        shapes = list(HoneycombShape.objects.all())
        
        for player in alive_players:
            shape = random.choice(shapes)
            # Send shape assignment
            asyncio.create_task(self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'honeycomb_shape',
                    'shape': {
                        'player_number': player.player_number,
                        'shape_id': shape.id,
                        'shape_type': shape.shape_type,
                        'svg_path': shape.svg_path,
                        'time_limit': shape.time_limit
                    }
                }
            ))
    
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
    
    async def check_honeycomb_completion(self):
        """Check if honeycomb stage is complete"""
        # This would check if all players have completed their shapes
        # For demo, we'll assume it's complete after a delay
        pass 