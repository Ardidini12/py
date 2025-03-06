from django.db import models
from django.core.exceptions import ValidationError
import re

# Create your models here.

class Contact(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, unique=True)  # Increased length
    email = models.EmailField(blank=True, null=True)  # Optional field
    birthday = models.DateField()
    source = models.CharField(max_length=255, editable=False)  # Keep non-editable

    def clean(self):
        # Allow formatting but normalize for storage
        original = self.phone_number
        normalized = '+' + ''.join(filter(str.isdigit, original.lstrip('+')))
        
        # Validate format
        if not original.startswith('+'):
            raise ValidationError({'phone_number': 'Must start with +'})
        if not re.match(r'^\+[\d\s\-\(\)]+$', original):
            raise ValidationError({'phone_number': 'Invalid characters'})
        
        # Validate normalized length
        if len(normalized) > 20:
            raise ValidationError({'phone_number': 'Number too long after normalization'})
        
        self.phone_number = normalized  # Store normalized version
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()  # Normalization happens in clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} {self.surname}"
