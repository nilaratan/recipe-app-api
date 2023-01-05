"""
Test recipe api
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import Recipe, Tag, Ingredient
from decimal import Decimal
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def get_detail_url(recipe_id):
    """Create and return a recipe detail url."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 5,
        'price': Decimal('15.40'),
        'description': 'Sample description',
        'link': 'demo link'
    }
    defaults.update(**params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicRecipeApiTest(TestCase):
    """Test for unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call the API"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTest(TestCase):
    """Test for authenticated user"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='testme@test.com',
            password='testpass123'
        )

        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipe(self):
        """Test for retrieving a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_list_recipe_limited_to_user(self):
        """Test for retrieving recipes related to the authenticated user"""
        other_user = get_user_model().objects.create_user(
            email='myemailtest@gmail.com',
            password='ohmydemo123'
        )

        create_recipe(user=other_user)
        create_recipe(user=self.user)
        res = self.client.get(RECIPES_URL)
        recipe = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipe, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_detail_recipe(self):
        """Test get recipe detail"""
        recipe = create_recipe(self.user)
        url = get_detail_url(recipe.id)
        res = self.client.get(url)
        recipe_data = Recipe.objects.get(id=recipe.id)
        serialize = RecipeDetailSerializer(recipe_data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serialize.data)

    def test_create_recipe(self):
        """Test to create a recipe successfully."""
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 5,
            'price': Decimal('15.40'),
            'description': 'Sample description',
            'link': 'demo link'
        }
        res = self.client.post(RECIPES_URL, data=payload)
        recipe = Recipe.objects.get(id=res.data.get('id'))
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test for partial update."""
        recipe = create_recipe(user=self.user)
        payload = {
            'title': 'new sample recipe'
        }

        url = get_detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, data=payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload.get('title'))
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test for full update."""
        recipe = create_recipe(user=self.user)

        payload = {
            'title': 'updated title',
            'time_minutes': 10,
            'price': Decimal('15.44'),
            'description': 'Sample description',
            'link': 'demo link'
        }

        url = get_detail_url(recipe_id=recipe.id)
        res = self.client.put(url, data=payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_changing_user_not_possible(self):
        """Test the changing user of recipe not possible."""
        new_user = get_user_model().objects.create_user(
            email='myemailtest@gmail.com',
            password='ohmydemo123'
        )

        recipe = create_recipe(user=self.user)
        payload = {
            "user": new_user.id
        }

        url = get_detail_url(recipe_id=recipe.id)
        self.client.patch(url, data=payload)
        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        recipe = create_recipe(user=self.user)

        url = get_detail_url(recipe_id=recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe(self):
        new_user = get_user_model().objects.create_user(
            email='myemailtest@gmail.com',
            password='ohmydemo123'
        )
        recipe = create_recipe(user=new_user)

        url = get_detail_url(recipe_id=recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags."""
        payload = {
            'title': 'Thai prawn curry.',
            'time_minutes': 5,
            'price': Decimal('2.50'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating recipe with existing tags."""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload["tags"]:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_recipe_update(self):
        """Test creating tag when updating a recipe."""
        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'Lunch'}]}
        url = get_detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_recipe_assign_tag(self):
        """Assigning an existing recipe when updating a recipe."""
        tag_breakfast = Tag.objects.create(
            user=self.user,
            name='Breakfast'
        )
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(
            user=self.user,
            name='Lunch'
        )
        payload = {
            'tags': [{'name': 'Lunch'}]
        }
        url = get_detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_tags_of_recipe(self):
        """Test for clearing all the tags of a recipe."""
        recipe = create_recipe(user=self.user)
        tag_dessert = Tag.objects.create(
            user=self.user,
            name='Dessert'
        )
        recipe.tags.add(tag_dessert)
        payload = {
            'tags': []
        }
        url = get_detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredient(self):
        """Test creating recipe with new ingredients."""
        payload = {
            'title': 'Khichidi',
            'time_minutes': 20,
            'price': Decimal('10.00'),
            'ingredients': [{'name': 'Rice'}, {'name': 'Dal'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """Test creating recipe with existing ingredient."""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Ghee'
        )
        payload = {
            'title': 'Vietnamese soup',
            'time_minutes': 25,
            'price': '2.55',
            'ingredients': [{'name': 'Ghee'}, {'name': 'Fish Sauce'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredients_on_update(self):
        """Test creating ingredients on update of recipe."""
        recipe = create_recipe(user=self.user)
        payload = {
            'ingredients': [{'name': 'Basumati'}]
        }

        url = get_detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user,
                                                name='Basumati')
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating recipe."""
        ingredient1 = Ingredient.objects.create(
            name='Pepper',
            user=self.user
        )
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(
            name='Chili',
            user=self.user
        )
        payload = {
            'ingredients': [{'name': 'Chili'}]
        }

        url = get_detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Clearing a recipe ingredients."""
        ingredient = Ingredient.objects.create(
            name='Kancha Lanka',
            user=self.user
        )
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {
            'ingredients': []
        }
        url = get_detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)


class PrivateRecipeApiTestForAdminUser(TestCase):
    def setUp(self):
        self.client = APIClient()
        admin_user = get_user_model().objects.create_user(
            email='admin@gmail.com',
            password='adminwe@123',
            is_superuser=True
        )
        self.client.force_authenticate(user=admin_user)

    def test_admin_user_view_all_recipe(self):
        normal_user = get_user_model().objects.create_user(
            email='normal@gmail.com',
            password='adminwe@123'
        )

        create_recipe(normal_user)
        recipes = Recipe.objects.all()
        serializer = RecipeSerializer(recipes, many=True)

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_admin_user_update_other_user_recipe(self):
        normal_user = get_user_model().objects.create_user(
            email='normal@gmail.com',
            password='adminwe@123'
        )

        link = "This is demo link"
        recipe = create_recipe(user=normal_user, link=link)

        payload = {
            'description': 'Hello description is awesome'
        }

        url = get_detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, data=payload)
        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.description, payload['description'])
        self.assertEqual(recipe.link, link)

    def test_deleting_recipe_of_other_user_as_admin_user(self):
        normal_user = get_user_model().objects.create_user(
            email='normal@gmail.com',
            password='adminwe@123'
        )
        recipe = create_recipe(user=normal_user)

        url = get_detail_url(recipe_id=recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())
