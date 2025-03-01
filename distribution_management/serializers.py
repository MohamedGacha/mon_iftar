from django.utils import timezone 

from rest_framework import serializers

from .models import Distribution,DistributionList


class DistributionSerializer(serializers.ModelSerializer):
    distribution_list = serializers.PrimaryKeyRelatedField(
        queryset=DistributionList.objects.all(),
        required=True
    )

    class Meta:
        model = Distribution
        fields = ['id', 'date_distribution', 'stock', 'description', 'location', 'distribution_list']

    def validate(self, data):
        """Ensure the date_distribution is in the future."""
        if data['date_distribution'] <= timezone.now():
            raise serializers.ValidationError(
                "La date de distribution doit être ultérieure à la date et l'heure actuelles."
            )
        return data
    

class QRCodeScanSerializer(serializers.Serializer):
    code_unique = serializers.UUIDField()
