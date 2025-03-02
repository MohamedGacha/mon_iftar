import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from utils.whatsapp import send_whatsapp_message, send_whatsapp_qr_code


class DistributionList(models.Model):

    location = models.ForeignKey(
        "user_management.Location", related_name='list_location', on_delete=models.CASCADE, blank=True)
    main_list = models.ManyToManyField(
        "user_management.Beneficiaire", related_name='main_list', blank=True)
    waiting_list = models.ManyToManyField(
        "user_management.Beneficiaire", related_name='waiting_list', blank=True)

    max_main_list_size = models.PositiveIntegerField(default=100)

    def clean(self):
        """Validation to ensure max_main_list_size is not less than the current size of main_list."""
        if self.pk:
            current_main_list_size = self.main_list.count()
            if self.max_main_list_size < current_main_list_size:
                raise ValidationError(
                    f"Le nombre maximum de places ({self.max_main_list_size}) ne peut pas être inférieur "
                    f"au nombre actuel de bénéficiaires dans la liste principale ({current_main_list_size})."
                )

    def add_beneficiaire(self, beneficiaire):
        """Ajoute un bénéficiaire à la liste principale ou à la liste d'attente."""
        if self.main_list.count() < self.max_main_list_size:
            self.main_list.add(beneficiaire)
            message_body = 'You have been added to the primary distribution list.'
        else:
            self.waiting_list.add(beneficiaire)
            message_body = 'You have been added to the waiting list.'

        # Use the beneficiaire's num_telephone for sending the message
        send_whatsapp_message(
            beneficiaire.num_telephone, message_body, console=True)

    def remove_beneficiaire(self, beneficiaire):
        """Supprime un bénéficiaire et gère la promotion FIFO depuis la liste d'attente."""
        # Initialize message_body with a default value
        message_body = "Your status in the distribution list has been updated."
        
        if beneficiaire in self.main_list.all():
            self.main_list.remove(beneficiaire)
            message_body = 'You have been removed from the primary distribution list.'

            if self.waiting_list.exists():
                next_in_line = self.waiting_list.order_by(
                    'date_inscription').first()
                self.waiting_list.remove(next_in_line)
                self.main_list.add(next_in_line)
                # Send message to the promoted beneficiaire
                send_whatsapp_message(
                    next_in_line.num_telephone,
                    'Congratulations! You have been promoted to the primary distribution list.',
                    console=True)

        elif beneficiaire in self.waiting_list.all():
            self.waiting_list.remove(beneficiaire)
            message_body = 'You have been removed from the waiting list.'
        else:
            # Beneficiary is not in any list, maybe log this unusual situation
            message_body = "You were not found in our distribution lists."

        # Send the message to the removed beneficiaire
        send_whatsapp_message(beneficiaire.num_telephone,
                            message_body, console=True)

    def save(self, *args, **kwargs):
        """Custom save to enforce validation."""
        self.full_clean()  # Calls the clean() method to validate
        super().save(*args, **kwargs)


# Modèle pour les QR Codes de distribution


class QRCodeDistribution(models.Model):
    beneficiaire = models.ForeignKey(
        "user_management.Beneficiaire", on_delete=models.CASCADE)
    date_validite = models.DateField(auto_now_add=True)
    code_unique = models.UUIDField(max_length=10,
                                   default=uuid.uuid4, editable=False, unique=True)
    heure_utilise = models.TimeField(null=True, blank=True)

    def clean(self):
        """Validation to ensure date_validite is always today's date on creation."""
        if self.date_validite != timezone.localdate():
            raise ValidationError(
                "La date de validité doit être la date du jour.")

    def save(self, *args, **kwargs):
        """Override save to ensure clean() is always called."""
        self.full_clean()

        # Send WhatsApp message to the beneficiaire
        send_whatsapp_qr_code(
            self.beneficiaire.num_telephone,
            str(self.code_unique),
            str(self.date_validite)
        )

        super().save(*args, **kwargs)

    def validate_code(self):
        """Validates the code and sets heure_utilise if date is valid."""
        today = timezone.localdate()

        # Check if the QR code is valid for today
        if self.date_validite == today:
            # Get the point_distribution of the beneficiaire (NOT location)
            beneficiaire_point_dist = self.beneficiaire.point_distribution

            # Find the distribution that matches the beneficiaire's point_distribution
            try:
                distribution = Distribution.objects.get(
                    location=beneficiaire_point_dist)  # This may also need revision
            except Distribution.DoesNotExist:
                raise ValidationError("No distribution found for this location.")

            # Decrement the stock for the distribution (we assume 1 item per scan)
            try:
                distribution.decrement_stock(quantity=1)
            except ValidationError as e:
                raise ValidationError(f"Failed to decrement stock: {e}")

            # Set the heure_utilise (time when the code was validated)
            self.heure_utilise = timezone.now().time()

            # Save the QR code
            self.save()
        else:
            raise ValidationError("Le code n'est pas valide aujourd'hui.")

    def __str__(self):
        return f"QR Code {self.code_unique} pour {self.beneficiaire.nom} {self.beneficiaire.prenom} - {self.date_validite}"


class Distribution(models.Model):
    stock = models.PositiveIntegerField(default=0)
    distribution_list = models.ForeignKey(
        'DistributionList', on_delete=models.CASCADE)

    date_distribution = models.DateTimeField()
    description = models.CharField(max_length=255)
    location = models.ForeignKey(
        "user_management.Location", related_name='distribution_location', on_delete=models.CASCADE, blank=True)

    def clean(self):
        """Validation to ensure date_distribution is always later than the current date and time."""
        if self.date_distribution <= timezone.now():
            raise ValidationError(
                "La date de distribution doit être ultérieure à la date et l'heure actuelles."
            )

    def decrement_stock(self, quantity=1):
        """Décrémente le stock en fonction de la quantité spécifiée."""
        if quantity > self.stock:
            raise ValidationError(
                "Quantité demandée supérieure au stock disponible.")
        self.stock -= quantity
        self.save()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
