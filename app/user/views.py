"""
Views for user API.
"""
from rest_framework import generics
from . import serializers


class CreateUserView(generics.CreateAPIView):
    """View class for creating user"""
    serializer_class = serializers.UserSerializer
