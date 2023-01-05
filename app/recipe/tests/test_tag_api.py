"""Tests for tag api"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from core.models import Tag
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def get_detail_tag_url(tag_id):
    """Create and return a tag detail url."""
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='testmyuser@gmail.com', password='testmeiam@123'):
    """Create a test user and return."""
    return get_user_model().objects.create_user(email=email,
                                                password=password)


def create_tag(name, user):
    """Create tag and return."""
    return Tag.objects.create(name=name, user=user)


class PublicTagApiTest(TestCase):
    """Test for unauthenticated API requests."""
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTest(TestCase):
    """Test for authorized API requests."""
    def setUp(self) -> None:
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tags(self):
        """Test for retrieve a list tags."""
        create_tag(name='Vegan', user=self.user)
        create_tag(name='Dessert', user=self.user)

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_tags_limited_to_user(self):
        """Test for retrieving tags limited to authenticated user."""
        other_user = create_user(email='anotheruser@gmail.com',
                                 password='another@123')
        create_tag(name='fruity', user=other_user)
        create_tag(name='comfort food', user=self.user)

        tags = Tag.objects.filter(user=self.user)
        serializer = TagSerializer(tags, many=True)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_for_update_tag(self):
        """Test for updating tag."""
        tag = create_tag(name='sample_tag', user=self.user)
        payload = {
            'name': 'updated_sample_tag'
        }

        url = get_detail_tag_url(tag_id=tag.id)
        res = self.client.patch(url, data=payload)

        tag.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(payload['name'], tag.name)

    def test_for_delete_tag(self):
        tag = create_tag(name='Okay', user=self.user)

        url = get_detail_tag_url(tag_id=tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())
