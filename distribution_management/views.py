
from django.utils import timezone 

from django.shortcuts import get_object_or_404
from rest_framework import status

# Create your views here.
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from user_management.models import Benevole, Location
from user_management.permissions import IsAdminUser, IsRegularUser
from user_management.serializers import (
    BeneficiaireSerializer,
    BenevoleSerializer,
)
from utils.whatsapp import send_whatsapp_message

from .models import Distribution, DistributionList, QRCodeDistribution
from .serializers import DistributionSerializer, QRCodeScanSerializer
import logging

logger = logging.getLogger(__name__)

class CreateDistributionView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        # Extract the location from the request data
        location_id = request.data.get('location')
        location = get_object_or_404(Location, id=location_id)

        # Check if there is a distribution list associated with the location
        distribution_list = DistributionList.objects.filter(location=location).first()

        if not distribution_list:
            return Response(
                {"detail": "No distribution list found for the specified location."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prepare data for serialization
        data = request.data.copy()
        # Explicitly add distribution_list to the data
        data['distribution_list'] = distribution_list.id

        # Create a DistributionSerializer instance with the provided data
        serializer = DistributionSerializer(data=data)

        if serializer.is_valid():
            # Save the new distribution
            distribution = serializer.save()

            # Create QR codes for all beneficiaries in the MAIN list
            beneficiaries = distribution_list.main_list.all()
            qr_codes = []
            for beneficiaire in beneficiaries:
                # Create the QRCodeDistribution for each beneficiaire
                qr_code = QRCodeDistribution.objects.create(
                    beneficiaire=beneficiaire,
                    date_validite=timezone.localdate()
                )
                qr_codes.append(qr_code)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteDistributionView(APIView):
    """
    API View to handle distribution deletion with comprehensive checks and permissions.
    
    This view ensures that:
    - Only admin users can delete distributions
    - Associated QR codes are also cleaned up
    - Proper error handling is implemented
    """
    
    permission_classes = [IsAdminUser]

    def delete(self, request, distribution_id):
        """
        Delete a specific distribution by its ID.
        
        Workflow:
        1. Validate the distribution exists
        2. Check if deletion is allowed (e.g., not in the past)
        3. Delete associated QR codes
        4. Delete the distribution
        5. Return appropriate response
        """
        try:
            # Retrieve the specific distribution
            distribution = get_object_or_404(Distribution, id=distribution_id)
            
            # Optional: Add a check to prevent deleting past distributions
            if distribution.date_distribution < timezone.now():
                return Response(
                    {"detail": "Cannot delete a distribution that has already occurred."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find and delete associated QR codes
            QRCodeDistribution.objects.filter(
                beneficiaire__in=distribution.distribution_list.main_list.all()
            ).delete()
            
            # Store some information before deletion for the response
            distribution_info = {
                'id': distribution.id,
                'date': distribution.date_distribution,
                'location': distribution.location.name,
                'stock': distribution.stock
            }
            
            # Delete the distribution
            distribution.delete()
            
            return Response({
                'detail': 'Distribution deleted successfully',
                'deleted_distribution': distribution_info
            }, status=status.HTTP_200_OK)
        
        except Distribution.DoesNotExist:
            return Response(
                {"detail": "Distribution not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            # Catch-all for unexpected errors
            return Response(
                {"detail": f"Error deleting distribution: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DistributionListBeneficiaireListAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        distribution_list_id = kwargs.get('distribution_list_id')

        try:
            distribution_list = DistributionList.objects.get(
                id=distribution_list_id)
        except DistributionList.DoesNotExist:
            return Response({"detail": "DistributionList not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get the filter parameter to determine which list to show
        list_type = request.query_params.get('list_type', None)

        if list_type == 'main_list':
            beneficiaries = distribution_list.main_list.all()
        elif list_type == 'waiting_list':
            beneficiaries = distribution_list.waiting_list.all()
        else:
            # Default to showing both lists if no filter is provided
            beneficiaries = distribution_list.main_list.all(
            ) | distribution_list.waiting_list.all()

        # Serialize the beneficiaries with the enhanced serializer
        serializer = BeneficiaireSerializer(beneficiaries, many=True)

        return Response({
            'distribution_list_id': distribution_list.id,
            'location': distribution_list.location.name,
            'beneficiaries': serializer.data
        })


class QRCodeScanView(APIView):
    permission_classes = [IsAuthenticated, IsRegularUser]

    def post(self, request):
        # Validate input data
        serializer = QRCodeScanSerializer(data=request.data)
        if serializer.is_valid():
            code_unique = serializer.validated_data['code_unique']

            try:
                # Retrieve the QR code object based on code_unique
                qr_code = QRCodeDistribution.objects.get(code_unique=code_unique)

                # Get the beneficiaire associated with the qr_code
                beneficiaire = qr_code.beneficiaire
                
                # The current user IS the benevole (since Benevole inherits from AbstractUser)
                benevole = request.user  # No need to query for Benevole

                # Compare point_distribution fields, not location fields
                if beneficiaire.point_distribution != benevole.point_distribution:
                    return Response({"detail": "Distribution points must match between Benevole and Beneficiaire."}, 
                                status=status.HTTP_400_BAD_REQUEST)

                # Validate the QR code (it will set heure_utilise if valid)
                qr_code.validate_code()

                # Send a success message (optional, you can remove this if not needed)
                send_whatsapp_message(
                    beneficiaire.num_telephone,
                    f"Your QR code {code_unique} has been validated successfully!",
                    console=True
                )

                # Serialize the beneficiaire data
                beneficiaire_data = BeneficiaireSerializer(beneficiaire).data

                # Return response with beneficiaire data included
                return Response({
                    "detail": "QR code validated successfully!",
                    "beneficiaire": beneficiaire_data  # Include the beneficiaire data
                }, status=status.HTTP_200_OK)

            except QRCodeDistribution.DoesNotExist:
                return Response({"detail": "QR code not found."}, status=status.HTTP_404_NOT_FOUND)
            except Benevole.DoesNotExist:
                return Response({"detail": "Benevole not found."}, status=status.HTTP_404_NOT_FOUND)
            except Location.DoesNotExist:
                return Response({"detail": "Location mismatch error."}, status=status.HTTP_400_BAD_REQUEST)

        # If serializer is invalid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DistributionListLocationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        location_id = kwargs.get('location_id')

        # Fetch the location object based on the ID
        try:
            location = Location.objects.get(id=location_id)
        except Location.DoesNotExist:
            return Response({"detail": "Location not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch all distribution lists for the given location
        distribution_lists = DistributionList.objects.filter(location=location)

        # Fetch all benevoles with the same location
        benevoles = Benevole.objects.filter(point_distribution=location)

        # Serialize benevoles
        benevole_serializer = BenevoleSerializer(benevoles, many=True)

        # Serialize distribution lists
        distribution_list_data = []
        for distribution_list in distribution_lists:
            distribution_list_data.append({
                'id': distribution_list.id,
                'location': location.name,  # Add other location details if needed
                'main_list_size': distribution_list.main_list.count(),
                'waiting_list_size': distribution_list.waiting_list.count(),
                # Add benevoles associated with this location
                'benevoles': benevole_serializer.data
            })

        return Response({
            'location': location.name,
            'distribution_lists': distribution_list_data
        })


class TodayDistributionAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        # Get today's date in UTC
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(
            hour=23, minute=59, second=59, microsecond=999999)

        # Filter distributions happening today
        distributions_today = Distribution.objects.filter(
            date_distribution__range=[today_start, today_end]
        )

        # Serialize the distribution data
        distribution_serializer = DistributionSerializer(
            distributions_today, many=True)

        return Response({
            'today_distributions': distribution_serializer.data
        })


class UpcomingDistributionAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        # Get the current date and time correctly using Django's timezone
        now = timezone.now()

        # Filter distributions that are scheduled in the future (after the current time)
        upcoming_distributions = Distribution.objects.filter(
            date_distribution__gt=now)

        # Serialize the distribution data
        distribution_serializer = DistributionSerializer(
            upcoming_distributions, many=True)

        return Response({
            'upcoming_distributions': distribution_serializer.data
        })