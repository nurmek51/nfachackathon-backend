from django.core.management.base import BaseCommand
from game.models import QuizQuestion

class Command(BaseCommand):
    help = 'Create quiz questions for the game'

    def handle(self, *args, **options):
        # Clear existing questions
        QuizQuestion.objects.all().delete()
        self.stdout.write('Cleared existing quiz questions')

        # Define the questions with correct answers
        questions_data = [
            {
                'question_text': 'Как пишется полное имя Бахи:',
                'option_a': 'Баха',
                'option_b': 'Бахаудин',
                'option_c': 'Бахауддин',
                'option_d': 'Бахардуино',
                'correct_answer': 'B',
                'difficulty': 2,
                'category': 'incubator'
            },
            {
                'question_text': 'Какой самый любимый звук бернара:',
                'option_a': 'Ааахх',
                'option_b': 'Аааахххх',
                'option_c': 'Аххххахххх',
                'option_d': 'АААхх',
                'correct_answer': 'D',
                'difficulty': 2,
                'category': 'incubator'
            },
            {
                'question_text': 'Самый лучший проект за всю историю инкубатора:',
                'option_a': 'EPITET',
                'option_b': 'Talapacademy',
                'option_c': 'TabAI',
                'option_d': 'CalAI',
                'correct_answer': 'B',
                'difficulty': 3,
                'category': 'incubator'
            },
            {
                'question_text': 'Кто украл HDMI?',
                'option_a': 'Бахредин',
                'option_b': 'Асхат Самедулла',
                'option_c': 'Рандомный пацанчик',
                'option_d': 'Типичный обладатель гранта nFactorial Incubator',
                'correct_answer': 'A',
                'difficulty': 2,
                'category': 'incubator'
            },
            {
                'question_text': 'Существует ли Аймурат на самом деле?',
                'option_a': 'Да',
                'option_b': 'Нет',
                'option_c': 'Это городская легенда',
                'option_d': 'Не знаю',
                'correct_answer': 'C',
                'difficulty': 2,
                'category': 'incubator'
            },
            {
                'question_text': 'Какое самое крутое названиие проекта:',
                'option_a': 'Куока AI',
                'option_b': 'Мено AI',
                'option_c': 'Auar AI',
                'option_d': 'Toonzy AI',
                'correct_answer': 'A',
                'difficulty': 2,
                'category': 'incubator'
            }
        ]

        # Create questions
        created_count = 0
        for question_data in questions_data:
            question = QuizQuestion.objects.create(**question_data)
            created_count += 1
            self.stdout.write(f'Created question: {question.question_text}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} quiz questions')
        ) 