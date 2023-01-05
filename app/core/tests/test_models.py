"""
Test for models
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from core import models
from decimal import Decimal


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
        """Test create superuser"""
        user = get_user_model().objects.\
            create_superuser(email='test@gmail.com', password='test@123')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_recipe(self):
        """Test create recipe"""
        user = get_user_model().objects.create_user(
            email='testuser1@gmail.com',
            name='Test user',
            password='testpass123'
        )

        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample recipe name',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample recipe description'
        )

        self.assertEqual(recipe.user, user)
        self.assertEqual(recipe.title, 'Sample recipe name')

    def test_create_tag(self):
        """Test tag created success"""
        user = get_user_model().objects.create_user(
            email='testuser2@gmail.com',
            name='Test user',
            password='testpass123'
        )
        tag = models.Tag.objects.create(
            name='sample tag',
            user=user
        )

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredients(self):
        """Test for creating ingredients is successful."""
        user = get_user_model().objects.create_user(
            email='demodemo@gmail.com',
            password='demodemo@123'
        )
        ingredient = models.Ingredient.objects.create(
            name='Lasun',
            user=user
        )

        self.assertEqual(ingredient.user, user)
        self.assertEqual(str(ingredient), ingredient.name)
        self.assertEqual(ingredient.name, 'Lasun')
