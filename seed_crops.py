# seed_crops.py
# Usage:
#   DJANGO_SETTINGS_MODULE=myProject.settings python seed_crops.py

import os
import sys
import django

# --- Configure Django (edit if needed) ---
if "DJANGO_SETTINGS_MODULE" not in os.environ:
    # Fallback: try a common/default; edit this to your project if you prefer hardcoding
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myProject.settings")

django.setup()

from django.db import transaction
from django.utils import timezone

# >>>> CHANGE THIS import to your app label if not 'myApp'
from myApp.models import Crop


DATA = [
    # 🌾 Rice Varieties
    dict(
        name="Rice - NSIC Rc216",
        description="NSIC Rc216 rice variety. Direct-seeded or transplanted (20x20 cm).",
        ideal_seasons="Jun-Nov, Dec-Apr",
        seed_rate_min_kg=40, seed_rate_max_kg=60,
        fert_sacks_min=4, fert_sacks_max=6,
        yield_t_min=4, yield_t_max=6,
        days_to_harvest_min=110, days_to_harvest_max=130,
    ),
    dict(
        name="Rice - NSIC Rc222",
        description="NSIC Rc222 rice variety. Direct-seeded or transplanted (20x20 cm).",
        ideal_seasons="Jun-Nov, Dec-Apr",
        seed_rate_min_kg=40, seed_rate_max_kg=60,
        fert_sacks_min=4, fert_sacks_max=6,
        yield_t_min=4, yield_t_max=6,
        days_to_harvest_min=110, days_to_harvest_max=130,
    ),
    # 🌽 Corn Varieties
    dict(
        name="Yellow Corn (Hybrid)",
        description="Yellow corn hybrid variety. 75 cm rows x 25 cm hills.",
        ideal_seasons="Jan-Dec",
        seed_rate_min_kg=15, seed_rate_max_kg=20,
        fert_sacks_min=4, fert_sacks_max=6,
        yield_t_min=4, yield_t_max=5,
        days_to_harvest_min=90, days_to_harvest_max=120,
    ),
    dict(
        name="White Corn (Open Pollinated)",
        description="White corn open pollinated variety. 75 cm rows x 25 cm hills.",
        ideal_seasons="Jan-Dec",
        seed_rate_min_kg=15, seed_rate_max_kg=20,
        fert_sacks_min=4, fert_sacks_max=6,
        yield_t_min=4, yield_t_max=5,
        days_to_harvest_min=90, days_to_harvest_max=120,
    ),
]


def upsert_crop(payload: dict):
    """
    Create or update a Crop by name with the provided defaults.
    """
    name = payload["name"]
    defaults = {
        "description": payload.get("description", ""),
        "ideal_seasons": payload.get("ideal_seasons", ""),
        "seed_rate_min_kg": payload.get("seed_rate_min_kg", 0) or 0,
        "seed_rate_max_kg": payload.get("seed_rate_max_kg", 0) or 0,
        "fert_sacks_min": payload.get("fert_sacks_min", 0) or 0,
        "fert_sacks_max": payload.get("fert_sacks_max", 0) or 0,
        "yield_t_min": payload.get("yield_t_min", 0) or 0,
        "yield_t_max": payload.get("yield_t_max", 0) or 0,
        "days_to_harvest_min": payload.get("days_to_harvest_min", 0) or 0,
        "days_to_harvest_max": payload.get("days_to_harvest_max", 0) or 0,
    }
    obj, created = Crop.objects.update_or_create(
        name=name,
        defaults=defaults
    )
    return obj, created


def main():
    # Schema sanity check (helpful if someone forgot to add fields)
    required_fields = [
        "seed_rate_min_kg", "seed_rate_max_kg",
        "fert_sacks_min", "fert_sacks_max",
        "yield_t_min", "yield_t_max",
        "days_to_harvest_min", "days_to_harvest_max",
        "ideal_seasons", "description",
    ]
    missing = [f for f in required_fields if not hasattr(Crop, f)]
    if missing:
        print("❌ Your Crop model is missing fields:", ", ".join(missing))
        print("   Add these fields and run migrations, then re-run this script.")
        sys.exit(1)

    # Delete all existing crops first
    with transaction.atomic():
        count = Crop.objects.count()
        Crop.objects.all().delete()
        print(f"🗑️  Deleted {count} existing crop(s)")

    # Create only the crops we need
    created, updated = 0, 0
    with transaction.atomic():
        for row in DATA:
            _, was_created = upsert_crop(row)
            if was_created:
                created += 1
            else:
                updated += 1

    print(f"✅ Seed complete. Created: {created}, Updated: {updated}")
    print("   You can now log a Planting activity and see forecasts immediately.")


if __name__ == "__main__":
    main()
