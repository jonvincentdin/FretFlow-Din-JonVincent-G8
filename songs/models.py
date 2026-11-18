from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models
from django.urls import reverse


class Song(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='songs',
    )
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=150, blank=True)
    content = models.TextField(validators=[MaxLengthValidator(50000)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-pk']
        indexes = [models.Index(fields=['owner', '-updated_at'], name='songs_owner_updated_idx')]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('songs:detail', kwargs={'pk': self.pk})
