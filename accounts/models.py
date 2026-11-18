from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    class Accidentals(models.TextChoices):
        SHARPS = 'sharps', 'Sharps (F♯, C♯)'
        FLATS = 'flats', 'Flats (B♭, E♭)'

    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=30, blank=True)
    preferred_accidentals = models.CharField(
        max_length=6, choices=Accidentals, default=Accidentals.SHARPS,
    )
    default_bpm = models.PositiveSmallIntegerField(
        'default tempo (BPM)', default=80,
        validators=[MinValueValidator(40), MaxValueValidator(240)],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower('email'), name='accounts_email_ci_unique'),
            models.UniqueConstraint(Lower('username'), name='accounts_username_ci_unique'),
            models.CheckConstraint(
                condition=models.Q(default_bpm__gte=40, default_bpm__lte=240),
                name='accounts_bpm_range',
            ),
        ]

    @property
    def display_name(self):
        return self.first_name or self.username
