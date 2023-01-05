"""
Tests for the user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


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
            'email': 'user1@gmail.com',
            'password': 'test',
            'name': 'Test user'
        }
        res = self.client.post(CREATE_USER_URL, data=payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.\
            filter(email=payload['email']).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_use(self):
        """Test generates token for valid user"""
        user_details = {
            'email': 'testuser@gmail.com',
            'password': 'test',
            'name': 'Test Name'
        }

        create_user(**user_details)

        payload = {
            'email': 'testuser@gmail.com',
            'password': 'test'
        }

        res = self.client.post(TOKEN_URL, data=payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials invalid"""
        user_details = {
            'email': 'testuser@gmail.com',
            'password': 'test',
            'name': 'Test Name'
        }

        create_user(**user_details)

        payload = {
            'email': 'testuser@gmail.com',
            'password': 'test123'
        }

        res = self.client.post(TOKEN_URL, data=payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error"""
        user_details = {
            'email': 'testuser@gmail.com',
            'password': 'test',
            'name': 'Test Name'
        }

        create_user(**user_details)

        payload = {
            'email': 'testuser@gmail.com',
            'password': ''
        }

        res = self.client.post(TOKEN_URL, data=payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_authorized(self):
        """Test authentication is required for users"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUerApiTest(TestCase):
    """Test API requests that require authentication"""

    def setUp(self) -> None:
        self.user = create_user(
            email='testuser@gmail.com',
            password='testpass',
            name='My Name test'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_user_partial_update_successful(self):
        """Test updating the profile of a logged in user"""
        payload = {
            'name': 'newtestuser'
        }

        res = self.client.patch(ME_URL, data=payload)
        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, payload['name'])

    def test_delete_method_is_not_allowed(self):
        """Test delete method is not allowed"""
        res = self.client.delete(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_post_method_is_not_allowed(self):
        """Test delete method is not allowed"""
        res = self.client.post(ME_URL, data={})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
