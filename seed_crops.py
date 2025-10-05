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
    # 🌾 Major Crops
    dict(
        name="Rice",
        description="Palay. Direct-seeded or transplanted (20x20 cm).",
        ideal_seasons="Jun-Nov, Dec-Apr",
        seed_rate_min_kg=40, seed_rate_max_kg=60,
        fert_sacks_min=4, fert_sacks_max=6,
        yield_t_min=4, yield_t_max=6,
        days_to_harvest_min=110, days_to_harvest_max=130,
    ),
    dict(
        name="Corn",
        description="75 cm rows x 25 cm hills.",
        ideal_seasons="Jan-Dec",
        seed_rate_min_kg=15, seed_rate_max_kg=20,
        fert_sacks_min=4, fert_sacks_max=6,
        yield_t_min=4, yield_t_max=5,
        days_to_harvest_min=90, days_to_harvest_max=120,
    ),
    # 🥭 Fruits
    dict(
        name="Mango",
        description="Carabao variety. ~10x10 m (~100 trees/ha). Bearing stage yields.",
        ideal_seasons="Dec-Apr",
        seed_rate_min_kg=0, seed_rate_max_kg=0,   # population via spacing; seed not used
        # per tree 0.5–1 kg; ~100 trees/ha ≈ 1–2 sacks/ha
        fert_sacks_min=1, fert_sacks_max=2,
        yield_t_min=3, yield_t_max=5,
        days_to_harvest_min=120, days_to_harvest_max=150,  # from flowering to harvest
    ),
    dict(
        name="Banana",
        description="~3x3 m (~1100 plants/ha). Perennial; window is for first cycle.",
        ideal_seasons="Jan-Dec",
        seed_rate_min_kg=0, seed_rate_max_kg=0,
        fert_sacks_min=10, fert_sacks_max=15,
        yield_t_min=20, yield_t_max=30,
        days_to_harvest_min=270, days_to_harvest_max=360,
    ),
    dict(
        name="Papaya",
        description="~2x2 m (~2500 plants/ha). Starts fruiting ~8 months.",
        ideal_seasons="Jan-Dec",
        seed_rate_min_kg=0, seed_rate_max_kg=0,
        fert_sacks_min=4, fert_sacks_max=6,
        yield_t_min=25, yield_t_max=40,
        days_to_harvest_min=240, days_to_harvest_max=300,
    ),
    dict(
        name="Guava",
        description="~5x5 m (~400 trees/ha). Yields assume bearing trees.",
        ideal_seasons="Jan-Dec",
        seed_rate_min_kg=0, seed_rate_max_kg=0,
        # 0.5–1 kg/tree → 200–400 kg/ha → 4–8 sacks
        fert_sacks_min=4, fert_sacks_max=8,
        yield_t_min=10, yield_t_max=15,
        days_to_harvest_min=540, days_to_harvest_max=720,  # ~1.5–2 yrs to first substantial crop
    ),
    # 🍠 Root Crops & Vegetables
    dict(
        name="Sweet Potato",
        description="Vines; ~20,000 cuttings/ha.",
        ideal_seasons="Jan-Dec",
        seed_rate_min_kg=0, seed_rate_max_kg=0,
        fert_sacks_min=2, fert_sacks_max=4,
        yield_t_min=8, yield_t_max=12,
        days_to_harvest_min=90, days_to_harvest_max=120,
    ),
    dict(
        name="Cassava",
        description="Stem cuttings; 10–12k cuttings/ha.",
        ideal_seasons="Jan-Dec",
        seed_rate_min_kg=0, seed_rate_max_kg=0,
        fert_sacks_min=3, fert_sacks_max=5,
        yield_t_min=20, yield_t_max=30,
        days_to_harvest_min=270, days_to_harvest_max=360,
    ),
    dict(
        name="Vegetables",
        description="Generic bucket (eggplant, tomato, okra, ampalaya).",
        ideal_seasons="Jan-Dec",
        seed_rate_min_kg=1, seed_rate_max_kg=6,  # 1–6 kg/ha (varies)
        fert_sacks_min=4, fert_sacks_max=6,
        yield_t_min=10, yield_t_max=20,
        days_to_harvest_min=70, days_to_harvest_max=120,
    ),
    dict(
        name="Onion",
        description="Bulb onion; seed 3–4 kg/ha (or bulbs 20–25 kg).",
        ideal_seasons="Nov-Feb",
        seed_rate_min_kg=3, seed_rate_max_kg=4,
        fert_sacks_min=5, fert_sacks_max=7,
        yield_t_min=8, yield_t_max=12,
        days_to_harvest_min=90, days_to_harvest_max=120,
    ),
    dict(
        name="Garlic",
        description="Cloves ~1000–1200 kg/ha.",
        ideal_seasons="Nov-Feb",
        seed_rate_min_kg=1000, seed_rate_max_kg=1200,  # kg of cloves/ha
        fert_sacks_min=5, fert_sacks_max=7,
        yield_t_min=4, yield_t_max=6,
        days_to_harvest_min=150, days_to_harvest_max=180,
    ),
    # 🍬 Sugar & Industrial
    dict(
        name="Sugarcane",
        description="Setts; 35–40k cuttings/ha. ~5–6 tons sugar per 60–80 tons cane.",
        ideal_seasons="Jan-Dec",
        seed_rate_min_kg=0, seed_rate_max_kg=0,
        fert_sacks_min=8, fert_sacks_max=12,
        yield_t_min=60, yield_t_max=80,
        days_to_harvest_min=300, days_to_harvest_max=420,
    ),
    dict(
        name="Tobacco",
        description="~50x60 cm spacing.",
        ideal_seasons="Dec-Mar",
        seed_rate_min_kg=0.5, seed_rate_max_kg=1.0,
        fert_sacks_min=4, fert_sacks_max=6,
        yield_t_min=1, yield_t_max=2,   # dried leaves
        days_to_harvest_min=90, days_to_harvest_max=130,
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
