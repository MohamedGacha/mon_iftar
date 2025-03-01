from django.utils import timezone 

from rest_framework import serializers

from .models import Distribution


class DistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Distribution
        fields = ['date_distribution', 'stock', 'description', 'location']

    def validate(self, data):
        """Ensure the date_distribution is in the future."""
        if data['date_distribution'] <= timezone.now():
            raise serializers.ValidationError(
                "La date de distribution doit être ultérieure à la date et l'heure actuelles.")
        return data


class QRCodeScanSerializer(serializers.Serializer):
    code_unique = serializers.UUIDField()
