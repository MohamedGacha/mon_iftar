from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from user_management.models import Benevole
from user_management.permissions import IsRegularUser
from user_management.serializers import FirstLoginSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
import logging
from django.db import IntegrityError
logger = logging.getLogger(__name__)

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

        try:
            user = Benevole.objects.create_user(username=username, password=password)
        except IntegrityError:
            return Response({'error': 'Username already exists.'},
                            status=status.HTTP_400_BAD_REQUEST)
        
        user.is_first_loggin = True
        user.save()

        tokens = get_tokens_for_user(user)
        return Response(tokens, status=status.HTTP_201_CREATED)


class FirstLoginAPIView(APIView):
    def post(self, request, *args, **kwargs):
        """Handle the completion of the first login setup."""
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Nom d\'utilisateur et mot de passe requis.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response({'error': 'Nom d\'utilisateur ou mot de passe incorrect.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        if not isinstance(user, Benevole):
            return Response({'error': 'Utilisateur non autorisé.'},
                            status=status.HTTP_403_FORBIDDEN)

        if not user.is_first_loggin:
            return Response({'message': 'Profil déjà complété.'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = FirstLoginSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            user.is_first_loggin = False
            user.save()
            
            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Profil complété avec succès.',
                'tokens': tokens
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Default implementation
        data = super().validate(attrs)
        
        # Add additional user information to the response
        data['user_id'] = self.user.id
        data['username'] = self.user.username
        data['is_first_login'] = getattr(self.user, 'is_first_loggin', False)
        
        return data
class RegularLoginAPIView(TokenObtainPairView):
    """
    Custom token obtain view to include additional user information
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Log successful login
            logger.info(f'Successful login for username: {request.data.get("username")}')
            
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Log login failure
            logger.error(f'Login failure: {str(e)}')
            return Response({
                'error': 'Login failed',
                'details': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)