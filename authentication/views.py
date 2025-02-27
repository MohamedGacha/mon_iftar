from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from user_management.models import Benevole
from user_management.permissions import IsRegularUser
from user_management.serializers import FirstLoginSerializer
from django.contrib.auth import authenticate


def get_tokens_for_user(user):
    """Generate JWT tokens for the user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterUserAPIView(APIView):
    
    permission_classes = [IsAuthenticated, IsRegularUser]
    def post(self, request, *args, **kwargs):
        """Register a new user and return their tokens"""
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Create the user and mark as first login
        user = Benevole.objects.create_user(username=username, password=password)
        user.is_first_loggin = True
        user.save()

        tokens = get_tokens_for_user(user)
        return Response(tokens, status=status.HTTP_201_CREATED)


class FirstLoginAPIView(APIView):

    def get(self, request, *args, **kwargs):
        """Check if the user needs to complete the first login setup."""
        user = request.user

        if not isinstance(user, Benevole):
            return Response({'error': 'Utilisateur non autorisé.'}, status=status.HTTP_403_FORBIDDEN)

        if not user.is_first_loggin:
            return Response({'message': 'Profil déjà complété.'}, status=status.HTTP_400_BAD_REQUEST)

        # Token is not required for the first login setup process, just guiding the user.
        return Response({
            'message': 'Veuillez compléter votre profil.'
        }, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Handle the completion of the first login setup."""
        user = request.user

        if user.is_first_loggin:
            return Response({'error': 'Action non autorisée ou profil déjà complété.'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = FirstLoginSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            user.is_first_loggin = False  # Mark the user as having completed their first login
            user.save()
            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Profil complété avec succès.',
                'tokens': tokens
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegularLoginAPIView(APIView):
    def post(self, request, *args, **kwargs):
        """Authenticate the user and return JWT tokens."""
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Authenticate the user using the provided credentials
        user = authenticate(username=username, password=password)

        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        if isinstance(user, Benevole) and user.is_first_loggin:
            return Response({'message': 'Please complete your profile first.'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate and return JWT tokens for the authenticated user
        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Login successful',
            'username': user.username,
            'tokens': tokens
        }, status=status.HTTP_200_OK)
