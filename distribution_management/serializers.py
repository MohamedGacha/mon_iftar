from django.utils import timezone 

from rest_framework import serializers

from .models import Distribution


class DistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Distribution
        fields = [
            'distribution_list', 
            'date_distribution', 
            'stock', 
            'description'
        ]
        
    def validate(self, data):
        # Validate distribution list exists
        distribution_list_id = data.get('distribution_list')
        if not DistributionList.objects.filter(id=distribution_list_id).exists():
            raise serializers.ValidationError({
                "distribution_list": "Invalid distribution list ID"
            })
        
        # Validate stock is positive
        stock = data.get('stock')
        if stock is not None and stock < 0:
            raise serializers.ValidationError({
                "stock": "Stock must be a non-negative number"
            })
        
        # Validate date is in the future
        date_distribution = data.get('date_distribution')
        if date_distribution and date_distribution <= timezone.now():
            raise serializers.ValidationError({
                "date_distribution": "Distribution date must be in the future"
            })
        
        return data

class QRCodeScanSerializer(serializers.Serializer):
    code_unique = serializers.UUIDField()
