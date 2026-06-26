from datetime import timedelta

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

# Force the built-in email field to be unique across the site
User._meta.get_field("email")._unique = True


class Profile(models.Model):
    # Links directly to Django's built-in User (handles id, email, first_name, last_name, password)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # Validator ensures ONLY digits are entered (0-9)
    numeric_only = RegexValidator(r"^\d+$", "Phone number must contain only numbers.")
    phone = models.CharField(max_length=20, unique=True, validators=[numeric_only])

    def __str__(self):
        return f"Profile for {self.user.username}"
    
    
class Member(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class PendingRegistration(models.Model):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=255)  # hashed password
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return self.email
class DailySpending(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    item = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField()

class EmailOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email