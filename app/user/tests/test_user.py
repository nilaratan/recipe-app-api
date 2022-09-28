"""
Tests for the user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')


def create_user(**kwargs):
    """Create and return a user."""
    return get_user_model().objects.create_user(**kwargs)


class PublicUserApiTests(TestCase):
    """Test the public features of user API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Tests creating a user is successful"""
        payload = {
            'email': 'user11@gmail.com',
            'password': 'test@123',
            'name': 'Test user'
        }
        res = self.client.post(CREATE_USER_URL, data=payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn('password', res.data)

    def test_create_user_with_email_exist_error(self):
        """Test error returned if user with email exists."""
        payload = {
            'email': 'user11@gmail.com',
            'password': 'test@123',
            'name': 'Test user'
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, data=payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_passwd_too_short_error(self):
        """Test error returned if password is too short"""
        payload = {
            'email': 'user11@gmail.com',
            'password': 'test',
            'name': 'Test user'
        }
        res = self.client.post(CREATE_USER_URL, data=payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.\
            filter(email=payload['email']).exists()
        self.assertFalse(user_exists)
