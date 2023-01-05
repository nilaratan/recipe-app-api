"""
Tests for ingredients API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def get_detail_url(ingredient_id):
    """Create and return ingredient detail url."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_ingredient(user, name):
    """Create a ingredient."""
    return Ingredient.objects.create(user=user, name=name)


class PublicIngredientApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving ingredients."""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email='ingredientuser@gmail.com',
            password='ingredient@123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredients(self):
        """Test for retrieving a list of ingredients."""
        create_ingredient(user=self.user,
                          name='Lasun')
        create_ingredient(user=self.user,
                          name='Coriander')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serialize = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serialize.data)

    def test_ingredients_limited_to_user(self):
        """Test list of ingredients limited to authenticated user."""
        other_user = get_user_model().objects.create_user(
            email='otheruser@gmail.com',
            password='otheruser@123'
        )
        create_ingredient(user=other_user, name='Kashmir lanka')
        create_ingredient(user=self.user, name='Chilly powder')

        res = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.filter(user=self.user)
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(len(res.data), 1)

    def test_ingredient_update(self):
        """Test for updating ingredients."""
        ingredient = create_ingredient(user=self.user, name='Turmeric powder')

        payload = {
            'name': 'Updated turmeric powder'
        }

        url = get_detail_url(ingredient_id=ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])
        self.assertEqual(ingredient.user, self.user)

    def test_ingredient_delete(self):
        """Test for deleting ingredients."""
        ingredient = create_ingredient(user=self.user, name='Cinnamon')

        url = get_detail_url(ingredient_id=ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())
