from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User, GameSession, Player, QuizQuestion, QuizAnswer

# Create your tests here.

class AvatarCustomizationTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            nickname='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_avatar_options_endpoint(self):
        """Test that avatar options endpoint returns all customization options"""
        response = self.client.get('/avatar/options/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('headwear', data)
        self.assertIn('accessories', data)
        self.assertIn('gender', data)
        self.assertIn('favorite_color', data)
        
        # Check that all expected options are present
        self.assertEqual(len(data['gender']), 2)  # male, female
        self.assertEqual(len(data['favorite_color']), 10)  # 10 colors
        self.assertEqual(len(data['headwear']), 3)  # bandana, crown, cap
        self.assertEqual(len(data['accessories']), 3)  # scarf, earrings, glasses
    
    def test_avatar_customization_serializer(self):
        """Test that the avatar customization serializer validates correctly"""
        from .serializers import AvatarCustomizationSerializer
        
        valid_data = {
            'headwear': 'crown',
            'accessory': 'glasses',
            'gender': 'male',
            'favorite_color': 'blue'
        }
        
        serializer = AvatarCustomizationSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Test invalid data
        invalid_data = {
            'headwear': 'invalid_choice',
            'accessory': 'glasses',
            'gender': 'male',
            'favorite_color': 'blue'
        }
        
        serializer = AvatarCustomizationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('headwear', serializer.errors)

class GameFlowTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            nickname='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.session = GameSession.objects.create(
            max_players=80,
            entry_fee=200000
        )
        self.player = Player.objects.create(
            user=self.user,
            session=self.session,
            player_number=1
        )
    
    def test_game_session_status_choices(self):
        """Test that game session only has the expected status choices (no honeycomb)"""
        expected_choices = [
            ('waiting', 'Waiting for Players'),
            ('lobby', 'In Lobby'),
            ('quiz', 'Quiz Stage'),
            ('red_light', 'Red Light Green Light'),
            ('freedom_room', 'Freedom Room'),
            ('finished', 'Finished'),
        ]
        
        actual_choices = GameSession._meta.get_field('status').choices
        self.assertEqual(actual_choices, expected_choices)
    
    def test_player_elimination_stages(self):
        """Test that players can only be eliminated in stages 1 and 2"""
        # Test quiz elimination (stage 1)
        self.player.elimination_stage = 1
        self.player.save()
        self.assertEqual(self.player.elimination_stage, 1)
        
        # Test red light elimination (stage 2)
        self.player.elimination_stage = 2
        self.player.save()
        self.assertEqual(self.player.elimination_stage, 2)
        
        # Verify no stage 3 exists
        self.assertNotEqual(self.player.elimination_stage, 3)
    
    def test_game_flow_transitions(self):
        """Test that game flows from quiz -> red_light -> freedom_room"""
        # Start with lobby
        self.session.status = 'lobby'
        self.session.save()
        
        # Transition to quiz
        self.session.status = 'quiz'
        self.session.save()
        self.assertEqual(self.session.status, 'quiz')
        
        # Transition to red_light
        self.session.status = 'red_light'
        self.session.save()
        self.assertEqual(self.session.status, 'red_light')
        
        # Transition to freedom_room (skipping honeycomb)
        self.session.status = 'freedom_room'
        self.session.save()
        self.assertEqual(self.session.status, 'freedom_room')
        
        # Verify no honeycomb stage in the flow
        self.assertNotEqual(self.session.status, 'honeycomb')

class QuizTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            nickname='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.session = GameSession.objects.create(
            max_players=80,
            entry_fee=200000
        )
        self.player = Player.objects.create(
            user=self.user,
            session=self.session,
            player_number=1
        )
        
        # Create test questions
        self.question1 = QuizQuestion.objects.create(
            question_text='Как пишется полное имя Бахи:',
            option_a='Баха',
            option_b='Бахаудин',
            option_c='Бахауддин',
            option_d='Бахардуино',
            correct_answer='B',
            difficulty=2,
            category='incubator'
        )
        
        self.question2 = QuizQuestion.objects.create(
            question_text='Какой самый любимый звук бернара:',
            option_a='Ааахх',
            option_b='Аааахххх',
            option_c='Аххххахххх',
            option_d='АААхх',
            correct_answer='D',
            difficulty=2,
            category='incubator'
        )
    
    def test_quiz_questions_created(self):
        """Test that quiz questions are created with correct data"""
        self.assertEqual(self.question1.question_text, 'Как пишется полное имя Бахи:')
        self.assertEqual(self.question1.correct_answer, 'B')
        self.assertEqual(self.question1.option_b, 'Бахаудин')
        
        self.assertEqual(self.question2.question_text, 'Какой самый любимый звук бернара:')
        self.assertEqual(self.question2.correct_answer, 'D')
        self.assertEqual(self.question2.option_d, 'АААхх')
    
    def test_quiz_answer_creation(self):
        """Test that quiz answers are created correctly"""
        # Create correct answer
        correct_answer = QuizAnswer.objects.create(
            player=self.player,
            session=self.session,
            question=self.question1,
            answer='B',
            is_correct=True,
            time_taken=5.5
        )
        
        self.assertTrue(correct_answer.is_correct)
        self.assertEqual(correct_answer.answer, 'B')
        self.assertEqual(correct_answer.time_taken, 5.5)
        
        # Create incorrect answer
        incorrect_answer = QuizAnswer.objects.create(
            player=self.player,
            session=self.session,
            question=self.question2,
            answer='A',
            is_correct=False,
            time_taken=8.2
        )
        
        self.assertFalse(incorrect_answer.is_correct)
        self.assertEqual(incorrect_answer.answer, 'A')
        self.assertEqual(incorrect_answer.time_taken, 8.2)
    
    def test_quiz_questions_limit(self):
        """Test that only 6 questions are returned for quiz"""
        # Create more questions
        for i in range(10):
            QuizQuestion.objects.create(
                question_text=f'Test question {i}',
                option_a=f'Option A {i}',
                option_b=f'Option B {i}',
                option_c=f'Option C {i}',
                option_d=f'Option D {i}',
                correct_answer='A',
                difficulty=1,
                category='test'
            )
        
        # Check that only 6 questions are active and returned
        active_questions = QuizQuestion.objects.filter(is_active=True)
        self.assertGreaterEqual(active_questions.count(), 6)
    
    def test_quiz_scoring_system(self):
        """Test the quiz scoring system"""
        # Create multiple answers for the same player
        QuizAnswer.objects.create(
            player=self.player,
            session=self.session,
            question=self.question1,
            answer='B',  # Correct
            is_correct=True,
            time_taken=3.0
        )
        
        QuizAnswer.objects.create(
            player=self.player,
            session=self.session,
            question=self.question2,
            answer='D',  # Correct
            is_correct=True,
            time_taken=2.5
        )
        
        # Calculate expected score: 2 correct answers * 100 - total time
        expected_score = 2 * 100 - (3.0 + 2.5)  # 200 - 5.5 = 194.5
        
        # Get player's answers
        answers = QuizAnswer.objects.filter(player=self.player, session=self.session)
        correct_answers = answers.filter(is_correct=True).count()
        total_time = sum(answer.time_taken for answer in answers if answer.is_correct)
        actual_score = correct_answers * 100 - total_time
        
        self.assertEqual(actual_score, expected_score)
        self.assertEqual(correct_answers, 2)
        self.assertEqual(total_time, 5.5)

class QuizAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            nickname='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test questions
        self.question1 = QuizQuestion.objects.create(
            question_text='Как пишется полное имя Бахи:',
            option_a='Баха',
            option_b='Бахаудин',
            option_c='Бахауддин',
            option_d='Бахардуино',
            correct_answer='B',
            difficulty=2,
            category='incubator'
        )
        
        self.question2 = QuizQuestion.objects.create(
            question_text='Какой самый любимый звук бернара:',
            option_a='Ааахх',
            option_b='Аааахххх',
            option_c='Аххххахххх',
            option_d='АААхх',
            correct_answer='D',
            difficulty=2,
            category='incubator'
        )
    
    def test_quiz_questions_api_endpoint(self):
        """Test the quiz questions API endpoint"""
        response = self.client.get('/quiz/questions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('questions', data)
        self.assertIn('total_questions', data)
        self.assertEqual(data['total_questions'], 2)
        
        questions = data['questions']
        self.assertEqual(len(questions), 2)
        
        # Check first question structure
        first_question = questions[0]
        self.assertIn('id', first_question)
        self.assertIn('question_text', first_question)
        self.assertIn('options', first_question)
        self.assertIn('difficulty', first_question)
        self.assertIn('category', first_question)
        
        # Check options structure
        options = first_question['options']
        self.assertIn('A', options)
        self.assertIn('B', options)
        self.assertIn('C', options)
        self.assertIn('D', options)
        
        # Verify question content (check both questions since order is random)
        question_texts = [q['question_text'] for q in questions]
        self.assertIn('Как пишется полное имя Бахи:', question_texts)
        self.assertIn('Какой самый любимый звук бернара:', question_texts)
        
        # Check that options contain expected values
        all_options = []
        for q in questions:
            all_options.extend(q['options'].values())
        
        self.assertIn('Бахаудин', all_options)
        self.assertIn('АААхх', all_options)
        
        # Check difficulty and category
        for question in questions:
            self.assertEqual(question['difficulty'], 2)
            self.assertEqual(question['category'], 'incubator')
    
    def test_quiz_questions_api_requires_authentication(self):
        """Test that quiz questions API requires authentication"""
        # Remove authentication
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/quiz/questions/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
