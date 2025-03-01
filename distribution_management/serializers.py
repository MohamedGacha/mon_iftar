from django.utils import timezone 

from rest_framework import serializers

from .models import Distribution, DistributionList

class DistributionSerializer(serializers.ModelSerializer):
    # Explicitly specify that distribution_list should be an ID
    distribution_list = serializers.PrimaryKeyRelatedField(
        queryset=DistributionList.objects.all(),
        many=False
    )

    class Meta:
        model = Distribution
        fields = [
            'distribution_list', 
            'date_distribution', 
            'stock', 
            'description'
        ]
        
    def validate(self, data):
        # Validate distribution list exists (this is now handled by PrimaryKeyRelatedField)
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
