from rest_framework import serializers

from .models import Beneficiaire, Benevole, Location


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name']


class BenevoleSerializer(serializers.ModelSerializer):
    # You may want to exclude the password field from the API
    class Meta:
        model = Benevole
        fields = ['id', 'username', 'first_name', 'last_name', 'is_first_loggin',
                  'num_benevole', 'num_telephone', 'point_distribution', 'admin']
        # Make num_benevole read-only, as it is generated automatically
        read_only_fields = ['num_benevole']


class BenevoleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benevole
        fields = ['username', 'first_name', 'last_name',
                  'num_telephone', 'point_distribution', 'admin']
        extra_kwargs = {
            # Exclude num_telephone validator, let it be handled manually
            'num_telephone': {'validators': []}
        }

    def create(self, validated_data):
        # When creating a Benevole, the num_benevole field is automatically generated
        benevole = Benevole.objects.create(**validated_data)
        # Set the generated num_benevole
        benevole.num_benevole = benevole.generate_num_benevole()
        benevole.save()
        return benevole


class BeneficiaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Beneficiaire
        fields = ['id', 'num_beneficiaire', 'nom',
                  'prenom', 'num_telephone', 'point_distribution']
        # Make num_beneficiaire read-only, as it is generated automatically
        read_only_fields = ['num_beneficiaire']


class BeneficiaireCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Beneficiaire
        fields = ['nom', 'prenom', 'num_telephone', 'point_distribution']

    def create(self, validated_data):
        # Create the beneficiaire and generate the unique num_beneficiaire
        beneficiaire = Beneficiaire.objects.create(**validated_data)
        beneficiaire.num_beneficiaire = beneficiaire.generate_unique_num_beneficiaire()
        beneficiaire.save()
        return beneficiaire


class FirstLoginSerializer(serializers.ModelSerializer):
    point_distribution = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), required=True)

    class Meta:
        model = Benevole
        fields = ['first_name', 'last_name', 'point_distribution']

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get(
            'first_name', instance.first_name)
        instance.last_name = validated_data.get(
            'last_name', instance.last_name)
        instance.point_distribution = validated_data.get(
            'point_distribution', instance.point_distribution)
        instance.is_first_loggin = False  # Mark as no longer the first login
        instance.save()
        return instance
