from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from user_management.models import Benevole
from user_management.permissions import IsFirstLoginUser, IsRegularUser
from user_management.serializers import FirstLoginSerializer


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def register_user(request):
    # Handle registration logic...
    user = Benevole.objects.create_user(
        username="new_user", password="password")
    # Ensure the user is marked as a first-time login user
    user.is_first_loggin = True
    user.save()

    tokens = get_tokens_for_user(user)
    return Response(tokens)


class FirstLoginAPIView(APIView):
    permission_classes = [IsAuthenticated, IsFirstLoginUser]

    def get(self, request, *args, **kwargs):
        """Check if the user needs to complete the first login setup."""
        user = request.user

        if not isinstance(user, Benevole):
            return Response({'error': 'Utilisateur non autorisé.'}, status=status.HTTP_403_FORBIDDEN)

        if not user.is_first_loggin:
            return Response({'message': 'Profil déjà complété.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Veuillez compléter votre profil.'}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Handle the completion of the first login setup."""
        user = request.user

        if not isinstance(user, Benevole) or not user.is_first_loggin:
            return Response({'error': 'Action non autorisée ou profil déjà complété.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = FirstLoginSerializer(
            user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Profil complété avec succès.'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegularLoginAPIView(APIView):
    permission_classes = [IsAuthenticated, IsRegularUser]

    def post(self, request, *args, **kwargs):
        user = request.user

        if isinstance(user, Benevole):  # Ensure the user is a Benevole instance
            if user.is_first_loggin:
                # If it's the first login, set the flag to False and update the user
                user.is_first_loggin = False
                user.save()

            # Keep the same token (no new token issued)
            return Response({'message': 'Login successful', 'username': user.username}, status=status.HTTP_200_OK)

        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
