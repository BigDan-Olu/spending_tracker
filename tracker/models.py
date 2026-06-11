from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
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


class DailySpending(models.Model):
    CATEGORY_CHOICES = [
        ("Food", "Food"),
        ("Transport", "Transport"),
        ("Bills", "Bills"),
        ("Entertainment", "Entertainment"),
        ("Shopping", "Shopping"),
        ("Other", "Other"),
    ]
    # Link spending to Django's built-in User now
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    item = models.CharField(max_length=100, blank=True, null=True)

    category = models.CharField(
        max_length=50,
        default="Other"
    )

    date = models.DateField()

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)