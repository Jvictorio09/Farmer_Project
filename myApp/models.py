from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
import re

# ======================
# 💰 EXPENSE TYPES
# ======================

EXPENSE_TYPES = [
    ('seed', 'Seed'),
    ('fertilizer', 'Fertilizer'),
    ('labor', 'Labor'),
    ('pesticide', 'Pesticide'),
    ('fuel', 'Fuel'),
    ('other', 'Other'),
]

# ======================
# 🔐 USER & ROLES
# ======================

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('farmer', 'Farmer'),
        ('technician', 'Technician'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='farmer')
    region = models.CharField(max_length=100, blank=True)

    def is_farmer(self): return self.role == 'farmer'
    def is_technician(self): return self.role == 'technician'
    def is_admin(self): return self.role == 'admin'


# ======================
# 🌱 CROPS
# ======================

class Crop(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    ideal_seasons = models.CharField(max_length=100)

    days_to_harvest_min = models.PositiveIntegerField(default=100)
    days_to_harvest_max = models.PositiveIntegerField(default=130)

    seed_rate_min_kg = models.FloatField(default=0)
    seed_rate_max_kg = models.FloatField(default=0)
    fert_sacks_min = models.FloatField(default=0)
    fert_sacks_max = models.FloatField(default=0)
    yield_t_min = models.FloatField(default=0)
    yield_t_max = models.FloatField(default=0)

    def __str__(self):
        return self.name


# ======================
# 📋 ACTIVITY LOG
# ======================

class Activity(models.Model):
    ACTIVITY_TYPES = [
        ('planting', 'Planting'),
        ('watering', 'Watering'),
        ('harvesting', 'Harvesting'),
    ]

    farmer = models.ForeignKey(User, on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)

    area_ha = models.FloatField(default=1.0)
    seed_qty_kg = models.FloatField(null=True, blank=True)
    fert_sacks = models.FloatField(null=True, blank=True)
    spacing = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.farmer.username} - {self.activity_type} - {self.crop.name}"


# ======================
# 💰 EXPENSE TRACKER
# ======================

class Expense(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE)
    crop = models.ForeignKey(
        Crop,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)


    def __str__(self):
        crop_name = self.crop.name if self.crop else "No crop"
        return f"{self.farmer.username} - {crop_name} - {self.expense_type} - ₱{self.amount}"

# ======================
# 📈 FORECAST
# ======================

class Forecast(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)

    expected_yield_kg = models.FloatField()
    yield_min_kg = models.FloatField()
    yield_max_kg = models.FloatField()

    season_factor = models.FloatField(default=1.0)
    input_factor = models.FloatField(default=1.0)
    population_factor = models.FloatField(default=1.0)

    forecast_date = models.DateField()   # planting date
    harvest_start = models.DateField(null=True, blank=True)
    harvest_end = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.crop.name} forecast ({self.forecast_date})"


# ======================
# 🔔 REMINDERS
# ======================

class Reminder(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    due_date = models.DateField()


# ======================
# 🌾 RECOMMENDATIONS
# ======================

class Recommendation(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    region = models.CharField(max_length=100)
    month = models.CharField(max_length=100)
    reason = models.TextField()


# ======================
# 🧮 FORECAST CALCULATION
# ======================

def compute_forecast(activity):
    crop = activity.crop
    area = max(activity.area_ha, 0.01)

    baseline_min = crop.yield_t_min * 1000
    baseline_max = crop.yield_t_max * 1000

    seed_factor = 1.0
    if activity.seed_qty_kg and crop.seed_rate_max_kg:
        per_ha = activity.seed_qty_kg / area
        mid = (crop.seed_rate_min_kg + crop.seed_rate_max_kg) / 2
        seed_factor = max(0.7, min(1.15, per_ha / max(mid, 1)))

    fert_factor = 1.0
    if activity.fert_sacks and crop.fert_sacks_max:
        per_ha = activity.fert_sacks / area
        mid = (crop.fert_sacks_min + crop.fert_sacks_max) / 2
        fert_factor = max(0.6, min(1.2, per_ha / max(mid, 1)))

    input_factor = seed_factor * fert_factor
    combined = max(0.5, min(1.3, input_factor))

    total_min = baseline_min * combined * area
    total_max = baseline_max * combined * area
    expected = (total_min + total_max) / 2

    harvest_start = activity.date + timedelta(days=crop.days_to_harvest_min)
    harvest_end = activity.date + timedelta(days=crop.days_to_harvest_max)

    return {
        "expected": expected,
        "min": total_min,
        "max": total_max,
        "harvest_start": harvest_start,
        "harvest_end": harvest_end,
        "notes": f"input_factor={input_factor:.2f}"
    }


# ======================
# ⚡ AUTO FORECAST SIGNAL
# ======================

@receiver(post_save, sender=Activity)
def generate_forecast(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.activity_type != 'planting':
        return

    data = compute_forecast(instance)

    Forecast.objects.create(
        farmer=instance.farmer,
        crop=instance.crop,
        expected_yield_kg=data["expected"],
        yield_min_kg=data["min"],
        yield_max_kg=data["max"],
        forecast_date=instance.date,
        harvest_start=data["harvest_start"],
        harvest_end=data["harvest_end"],
        notes=data["notes"],
    )
