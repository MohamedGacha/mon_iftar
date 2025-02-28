from distribution_management.models import DistributionList
from django.contrib.auth.password_validation import validate_password
from django.utils.crypto import get_random_string
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from utils.whatsapp import send_whatsapp_message

from .models import Beneficiaire, Benevole, Location
from .permissions import IsAdminUser
from .serializers import (
    BeneficiaireSerializer,
    BenevoleSerializer,
    LocationSerializer,
)

from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django.contrib.auth.models import AnonymousUser

class CreateBenevoleAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('num_telephone')
        if not phone_number or not phone_number.startswith('+'):
            return Response({'error': 'Le numéro de téléphone doit commencer par le code du pays (ex. +33 123456789).'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Generate a random password
        generated_password = get_random_string(length=8)
        try:
            validate_password(generated_password)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Create the Benevole
        Benevole.objects.create_user(
            username=phone_number,
            num_telephone=phone_number,
            password=generated_password
        )

        send_whatsapp_message(
            phone_number, 'code_bénévole:'+generated_password, console=True)

        return Response({
            'message': 'Bénévole créé avec succès.',
            'num_telephone': phone_number
        }, status=status.HTTP_201_CREATED)


class MakeAdminAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        num_benevole = request.data.get('num_benevole')

        if not num_benevole:
            return Response(
                {'error': "Le champ 'num_benevole' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            benevole = Benevole.objects.get(num_benevole=num_benevole)
            benevole.admin = True
            benevole.save()
            return Response(
                {'message': f'Bénévole {benevole.username} ({benevole.num_benevole}) est maintenant un admin.'},
                status=status.HTTP_200_OK
            )
        except Benevole.DoesNotExist:
            return Response(
                {'error': f"Bénévole avec le numéro '{num_benevole}' non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )


class AddBeneficiaireAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if request.user.admin:
            return Response({'error': 'Seuls les bénévoles réguliers peuvent ajouter des bénéficiaires.'},
                            status=status.HTTP_403_FORBIDDEN)

        nom = request.data.get('nom')
        prenom = request.data.get('prenom')
        num_telephone = request.data.get('num_telephone')
        point_distribution = request.user.point_distribution

        if not all([nom, prenom, num_telephone]):
            return Response({'error': 'Veuillez fournir nom, prénom et numéro de téléphone.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Création du bénéficiaire
        beneficiaire = Beneficiaire.objects.create(
            nom=nom,
            prenom=prenom,
            num_telephone=num_telephone,
            point_distribution=point_distribution
        )

        # Ajout automatique à la DistributionList associée au point de distribution
        distribution_list, created = DistributionList.objects.get_or_create(
            location=point_distribution)
        distribution_list.add_beneficiaire(beneficiaire)

        return Response({'message': 'Bénéficiaire ajouté avec succès.', 'num_beneficiaire': beneficiaire.num_beneficiaire},
                        status=status.HTTP_201_CREATED)


class DeleteBeneficiaireAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def delete(self, request, *args, **kwargs):

        # Retrieve the `num_beneficiaire` from the request data
        num_beneficiaire = request.data.get('num_beneficiaire')

        if not num_beneficiaire:
            return Response({'error': 'Veuillez fournir le numéro du bénéficiaire à supprimer.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the Beneficiaire object based on the `num_beneficiaire`
            beneficiaire = Beneficiaire.objects.get(
                num_beneficiaire=num_beneficiaire)
        except Beneficiaire.DoesNotExist:
            return Response({'error': 'Bénéficiaire non trouvé.'},
                            status=status.HTTP_404_NOT_FOUND)

        # Remove the beneficiaire from the associated DistributionList
        if beneficiaire.point_distribution:
            distribution_list = DistributionList.objects.filter(
                location=beneficiaire.point_distribution).first()
            if distribution_list:
                distribution_list.remove_beneficiaire(beneficiaire)

        # Delete the beneficiaire from the database
        beneficiaire.delete()

        return Response({'message': 'Bénéficiaire supprimé avec succès.'},
                        status=status.HTTP_204_NO_CONTENT)


# API View to list all Locations
class LocationListAPIView(generics.ListAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer


# API View to list all Benevoles
class BenevoleListAPIView(generics.ListAPIView):
    queryset = Benevole.objects.all()
    serializer_class = BenevoleSerializer


# API View to list all Beneficiaires
class BeneficiaireListAPIView(generics.ListAPIView):
    queryset = Beneficiaire.objects.all()
    serializer_class = BeneficiaireSerializer


class BeneficiaireSearchAPIView(generics.GenericAPIView):
    serializer_class = BeneficiaireSerializer

    def get(self, request, *args, **kwargs):
        num_beneficiaire = request.query_params.get('num_beneficiaire', None)
        if not num_beneficiaire:
            return Response(
                {"detail": "Veuillez fournir le paramètre 'num_beneficiaire'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            beneficiaire = Beneficiaire.objects.get(
                num_beneficiaire=num_beneficiaire)
            serializer = self.get_serializer(beneficiaire)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Beneficiaire.DoesNotExist:
            return Response(
                {"detail": f"Bénéficiaire avec le numéro '{num_beneficiaire}' introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )


class CreateLocationAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        # Include max_main_list_size in the request data and validate it
        serializer = LocationSerializer(data=request.data)

        if serializer.is_valid():
            # Create the location
            location = serializer.save()

            # Extract max_main_list_size from the request data (defaults to 100 if not provided)
            max_main_list_size = request.data.get('max_main_list_size', 100)

            # Automatically create the associated DistributionList with max_main_list_size
            distribution_list = DistributionList.objects.create(
                location=location,
                max_main_list_size=max_main_list_size
            )

            return Response({
                'message': 'Location and associated DistributionList created successfully.',
                'location': serializer.data,
                'distribution_list_id': distribution_list.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SearchLocationAPIView(APIView):
    def get(self, request, *args, **kwargs):
        query = request.query_params.get('name', None)

        if not query:
            return Response({'error': 'A "name" query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        locations = Location.objects.filter(name__icontains=query)
        serializer = LocationSerializer(locations, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    

class CurrentUserAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    # Add multiple authentication classes to support both token and session auth
    authentication_classes = [TokenAuthentication, SessionAuthentication]
        
    def get(self, request, *args, **kwargs):
        serializer = BenevoleSerializer(request.user)
        return Response(serializer.data)