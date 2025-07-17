from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User

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
