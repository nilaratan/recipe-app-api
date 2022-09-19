"""
Test for models
"""
from django.contrib.auth import get_user_model
from django.test import TestCase


class ModelTests(TestCase):
    """Test model"""

    def test_create_user_with_email_successful(self):
        """Test for creating user with email successful"""
        email = 'test@example.com'
        password = 'example@123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_is_normalised(self):
        """Test the new user email is normalised."""
        sample_emails = (
            ("test1@Example.com", "test1@example.com"),
            ("test2@EXAMPLE.com", "test2@example.com"),
            ("TEST3@example.com", "TEST3@example.com")
        )
        for email, expected_email in sample_emails:
            user = get_user_model().objects.\
                create_user(email=email, password='test@123')
            self.assertEqual(user.email, expected_email)

    def test_new_user_without_email_raise_error(self):
        """Test the new user creation without the email"""
        with self.assertRaises(ValueError):
            get_user_model().objects.\
                create_user(email='', password='test@123')

    def test_create_superuser(self):
        user = get_user_model().objects.\
            create_superuser(email='test@gmail.com', password='test@123')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
