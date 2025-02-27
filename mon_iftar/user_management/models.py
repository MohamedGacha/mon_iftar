import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class Location(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Benevole(AbstractUser):
    num_benevole = models.CharField(
        max_length=20, unique=True, help_text="Numéro du bénévole (format personnalisé)", blank=True)
    num_telephone = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                # Cette regex valide un numéro avec ou sans le préfixe '+'
                regex=r'^\+?(\d[\d\s\-]*){10,20}$',
                message="Le numéro de téléphone doit être valide (ex. +33 1 23 45 67 89 ou 0123456789)."
            )
        ]
    )
    point_distribution = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True)
    admin = models.BooleanField(default=False)
    is_first_loggin = models.BooleanField(default=True)

    REQUIRED_FIELDS = ['num_benevole', 'num_telephone',
                       'point_distribution', 'first_name', 'last_name']

    def generate_num_benevole(self):
        # Determine the first letter based on admin status
        first_letter = "A" if self.admin else "N"

        # Generate a short part of UUID (first 4 characters of the hex)
        uuid_part = uuid.uuid4().hex[:4].upper()

        # Combine the first letter with UUID part
        return f"V{first_letter}{uuid_part}"

    def save(self, *args, **kwargs):
        if not self.num_benevole:
            self.num_benevole = self.generate_num_benevole()
        super().save(*args, **kwargs)

    def __str__(self):
        role = "Admin" if self.admin else "Bénévole"
        return f"{role}: {self.username} | {self.num_benevole}"


# Modèle pour les bénéficiaires
class Beneficiaire(models.Model):
    num_beneficiaire = models.CharField(
        max_length=20,
        unique=True,
        help_text="Numéro du bénéficiaire (format E1234)"
    )
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    num_telephone = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                # Cette regex valide un numéro avec ou sans le préfixe '+'
                regex=r'^\+?(\d[\d\s\-]*){10,20}$',
                message="Le numéro de téléphone doit être valide (ex. +33 1 23 45 67 89 ou 0123456789)."
            )
        ]
    )
    point_distribution = models.ForeignKey(
        'Location', on_delete=models.SET_NULL, null=True, blank=True
    )

    def generate_unique_num_beneficiaire(self):
        """ Génère un code unique de type E1234 en utilisant un UUID. """
        while True:
            # Génère un UUID, prend les 4 premiers chiffres hexadécimaux et les convertit en entier
            code = f"E{str(uuid.uuid4().int)[:4]}"
            if not Beneficiaire.objects.filter(num_beneficiaire=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.num_beneficiaire:
            self.num_beneficiaire = self.generate_unique_num_beneficiaire()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} {self.prenom} | {self.num_beneficiaire}"
