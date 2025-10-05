from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
# --- imports near the top of models.py ---
from django.db.models.signals import post_save
from django.dispatch import receiver
import re
from datetime import timedelta


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
    region = models.CharField(max_length=100, blank=True)  # For recommendations

    def is_farmer(self):
        return self.role == 'farmer'

    def is_technician(self):
        return self.role == 'technician'

    def is_admin(self):
        return self.role == 'admin'


# ======================
# 🌱 CROPS
# ======================

class Crop(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    ideal_seasons = models.CharField(max_length=100, help_text="e.g. Jan-Mar, Jul-Sep")

    # NEW: growth + baseline agronomy (per hectare)
    days_to_harvest_min = models.PositiveIntegerField(default=100)  # tune per crop
    days_to_harvest_max = models.PositiveIntegerField(default=130)

    seed_rate_min_kg = models.FloatField(default=0)   # e.g., Rice 40
    seed_rate_max_kg = models.FloatField(default=0)   # e.g., Rice 60
    fert_sacks_min = models.FloatField(default=0)     # e.g., Rice 4
    fert_sacks_max = models.FloatField(default=0)     # e.g., Rice 6
    yield_t_min = models.FloatField(default=0)        # e.g., Rice 4
    yield_t_max = models.FloatField(default=0)        # e.g., Rice 6

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

    farmer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'farmer'})
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)

    # NEW: only used when activity_type='planting'
    area_ha = models.FloatField(default=1.0, help_text="Area in hectares")
    seed_qty_kg = models.FloatField(null=True, blank=True)
    fert_sacks = models.FloatField(null=True, blank=True, help_text="Total # of 50kg fertilizer sacks applied (baseline plan)")
    spacing = models.CharField(max_length=50, null=True, blank=True, help_text="e.g. '20x20 cm' or '10x10 m'")

    def __str__(self):
        return f"{self.farmer.username} - {self.activity_type} - {self.crop.name}"


# ======================
# 💰 EXPENSE TRACKER
# ======================

class Expense(models.Model):
    EXPENSE_TYPES = [
        ('seed', 'Seed'),
        ('fertilizer', 'Fertilizer'),
        ('labor', 'Labor'),
        ('equipment', 'Equipment'),
        ('others', 'Others'),
    ]

    farmer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'farmer'})
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.farmer.username} - {self.expense_type} - ₱{self.amount}"


# ======================
# 📈 CROP FORECAST
# ======================

# models.py
class Forecast(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'farmer'})
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    expected_yield_kg = models.FloatField()
    forecast_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    # NEW: range + factors + harvest window
    yield_min_kg = models.FloatField(default=0)
    yield_max_kg = models.FloatField(default=0)
    season_factor = models.FloatField(default=1.0)
    input_factor = models.FloatField(default=1.0)         # seed × fertilizer
    population_factor = models.FloatField(default=1.0)    # for trees/banana via spacing
    harvest_start = models.DateField(null=True, blank=True)
    harvest_end = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.crop.name} forecast for {self.forecast_date}"

# ======================
# 🌾 CROP RECOMMENDATIONS
# ======================

class Recommendation(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    region = models.CharField(max_length=100)
    month = models.CharField(max_length=15)  # e.g., 'July'
    reason = models.TextField()

    def __str__(self):
        return f"{self.crop.name} - {self.region} - {self.month}"


# ======================
# 🔔 REMINDERS
# ======================

class Reminder(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'farmer'})
    message = models.CharField(max_length=255)
    due_date = models.DateField()

    def __str__(self):
        return f"Reminder for {self.farmer.username}: {self.message}"


# ======================
# 📝 SUPPORT & HELP
# ======================

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return self.question


class SupportContact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ---------- Helpers ----------
_MONTHS = {m:i for i, m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], start=1
)}

def _parse_spacing(spacing: str):
    """Return (row_m, hill_m) from '20x20 cm' or '10x10 m'."""
    if not spacing: return None
    m = re.match(r'^\s*(\d+(\.\d+)?)\s*[xX]\s*(\d+(\.\d+)?)\s*(cm|m)?\s*$', spacing.strip())
    if not m: return None
    a = float(m.group(1)); b = float(m.group(3)); unit = (m.group(5) or 'cm').lower()
    if unit == 'cm': a /= 100.0; b /= 100.0
    return (a, b)  # meters

def _trees_per_ha(spacing_tuple):
    if not spacing_tuple: return None
    a, b = spacing_tuple
    if a <= 0 or b <= 0: return None
    m2_per_tree = a * b
    return 10000.0 / m2_per_tree

def _season_factor(ideal: str, month: int) -> float:
    """
    ideal example: 'Jan-Mar, Jul-Sep'
    Inside window => 1.0; shoulder (adjacent months) => 0.9; otherwise 0.8
    """
    if not ideal: return 1.0
    ideal = ideal.replace(' ', '')
    good_months = set()
    for block in ideal.split(','):
        if '-' in block:
            a, b = block.split('-')
            if a in _MONTHS and b in _MONTHS:
                ai, bi = _MONTHS[a], _MONTHS[b]
                if ai <= bi:
                    rng = range(ai, bi+1)
                else:
                    # wrap (e.g., Nov-Feb)
                    rng = list(range(ai, 13)) + list(range(1, bi+1))
                good_months.update(rng)
        elif block in _MONTHS:
            good_months.add(_MONTHS[block])

    if month in good_months:
        return 1.0
    # shoulder month check
    shoulders = {((m % 12) + 1) for m in good_months} | {((m - 2) % 12) + 1 for m in good_months}
    return 0.9 if month in shoulders else 0.8

def _clamp(x, lo, hi): return max(lo, min(hi, x))


# ---------- The calculator ----------
def compute_forecast_from_activity(activity: Activity):
    """
    Returns dict: {yield_min_kg, yield_max_kg, expected_yield_kg, season_factor, input_factor, population_factor, harvest_start, harvest_end, notes}
    """
    crop = activity.crop
    area = max(activity.area_ha or 1.0, 1e-6)
    seed_qty = (activity.seed_qty_kg or 0.0)
    fert_sacks = (activity.fert_sacks or 0.0)
    spacing = activity.spacing or ""

    # Baselines
    baseline_min = crop.yield_t_min * 1000.0  # kg/ha
    baseline_max = crop.yield_t_max * 1000.0  # kg/ha
    if baseline_min <= 0 or baseline_max <= 0:
        # No baselines? Fall back to zero to avoid fake numbers.
        return {
            "yield_min_kg": 0, "yield_max_kg": 0, "expected_yield_kg": 0,
            "season_factor": 1.0, "input_factor": 1.0, "population_factor": 1.0,
            "harvest_start": None, "harvest_end": None,
            "notes": "Missing baseline yields for this crop."
        }

    # Season
    plant_month = activity.date.month
    s_factor = _season_factor(crop.ideal_seasons or "", plant_month)

    # Inputs
    # Seed factor (if seed rate exists)
    seed_factor = 1.0
    if crop.seed_rate_max_kg > 0 and seed_qty > 0:
        per_ha = seed_qty / area
        mid = (crop.seed_rate_min_kg + crop.seed_rate_max_kg) / 2.0 if (crop.seed_rate_min_kg + crop.seed_rate_max_kg) > 0 else per_ha
        seed_factor = _clamp(per_ha / max(mid, 1e-6), 0.7, 1.15)

    # Fert factor
    fert_factor = 1.0
    if crop.fert_sacks_max > 0 and fert_sacks > 0:
        per_ha_f = fert_sacks / area
        mid_f = (crop.fert_sacks_min + crop.fert_sacks_max) / 2.0 if (crop.fert_sacks_min + crop.fert_sacks_max) > 0 else per_ha_f
        fert_factor = _clamp(per_ha_f / max(mid_f, 1e-6), 0.6, 1.2)

    input_factor = seed_factor * fert_factor

    # Population factor for tree/banana if spacing provided
    pop_factor = 1.0
    crop_name = (crop.name or "").strip().lower()
    if crop_name in ("mango", "guava", "banana"):
        sp = _parse_spacing(spacing)
        if sp:
            trees_ha = _trees_per_ha(sp)
            nominal = 100 if crop_name == "mango" else (400 if crop_name == "guava" else 1100)
            if trees_ha:
                pop_factor = _clamp(trees_ha / nominal, 0.6, 1.3)

    combined = _clamp(s_factor * input_factor * pop_factor, 0.5, 1.3)

    ha_min = baseline_min * combined
    ha_max = baseline_max * combined
    total_min = ha_min * area
    total_max = ha_max * area
    est = (total_min + total_max) / 2.0

    # Harvest window
    start = activity.date + timedelta(days=crop.days_to_harvest_min or 0)
    end = activity.date + timedelta(days=crop.days_to_harvest_max or 0)

    notes = (f"season={s_factor:.2f}, seed×fert={input_factor:.2f} "
             f"(seed={seed_factor:.2f}, fert={fert_factor:.2f}), pop={pop_factor:.2f}, "
             f"area={area}ha, combined={combined:.2f}")

    return {
        "yield_min_kg": total_min,
        "yield_max_kg": total_max,
        "expected_yield_kg": est,
        "season_factor": s_factor,
        "input_factor": input_factor,
        "population_factor": pop_factor,
        "harvest_start": start,
        "harvest_end": end,
        "notes": notes,
    }


# ---------- Auto-create/refresh Forecast on planting ----------
@receiver(post_save, sender=Activity)
def auto_forecast_on_planting(sender, instance: Activity, created, **kwargs):
    if instance.activity_type != 'planting':
        return

    data = compute_forecast_from_activity(instance)

    Forecast.objects.update_or_create(
        farmer=instance.farmer,
        crop=instance.crop,
        forecast_date=timezone.now().date(),
        defaults={
            "expected_yield_kg": data["expected_yield_kg"],
            "yield_min_kg": data["yield_min_kg"],
            "yield_max_kg": data["yield_max_kg"],
            "season_factor": data["season_factor"],
            "input_factor": data["input_factor"],
            "population_factor": data["population_factor"],
            "harvest_start": data["harvest_start"],
            "harvest_end": data["harvest_end"],
            "notes": data["notes"],
            "created_at": timezone.now(),
        }
    )
