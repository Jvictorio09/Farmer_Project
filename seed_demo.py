# seed_demo.py
# Usage:
#   DJANGO_SETTINGS_MODULE=myProject.settings python seed_demo.py
#
# Seeds a set of demo users, crops, activities, forecasts, expenses, reminders,
# recommendations, FAQs, and support tickets for walkthroughs.

import os
import django
from datetime import date, timedelta
from decimal import Decimal

if "DJANGO_SETTINGS_MODULE" not in os.environ:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myProject.settings")

django.setup()

from django.utils import timezone
from django.db import transaction

from myApp.models import (
    User,
    Crop,
    Activity,
    Expense,
    Forecast,
    Reminder,
    Recommendation,
    FAQ,
    SupportContact,
    compute_forecast_from_activity,
)

from seed_crops import DATA as CROP_DATA, upsert_crop


def _create_users():
    """Create demo admin, technician, and farmers."""
    users = [
        dict(username="admin", email="admin@agritrack.demo", role="admin"),
        dict(username="tech_ana", email="tech@agritrack.demo", role="technician", first_name="Ana"),
        dict(username="farmer_ben", email="ben@agritrack.demo", role="farmer", first_name="Ben", region="Ilocos Norte"),
        dict(username="farmer_rosa", email="rosa@agritrack.demo", role="farmer", first_name="Rosa", region="Bukidnon"),
    ]
    created = []
    for entry in users:
        user, is_new = User.objects.update_or_create(
            username=entry["username"],
            defaults={
                "email": entry.get("email", ""),
                "role": entry["role"],
                "first_name": entry.get("first_name", ""),
                "region": entry.get("region", ""),
            },
        )
        user.set_password("demo12345")
        user.save()
        if is_new:
            created.append(user.username)
    return created


def _create_crops():
    """Upsert baseline crop data."""
    created, updated = 0, 0
    for payload in CROP_DATA:
        _, was_created = upsert_crop(payload)
        if was_created:
            created += 1
        else:
            updated += 1
    return created, updated


def _sample_dates():
    today = date.today()
    return {
        "today": today,
        "yesterday": today - timedelta(days=1),
        "last_week": today - timedelta(days=7),
        "two_weeks": today - timedelta(days=14),
        "last_month": today - timedelta(days=30),
    }


def _create_activities(farmer):
    dates = _sample_dates()
    corn = Crop.objects.get(name="Corn")
    rice = Crop.objects.get(name="Rice")
    mango = Crop.objects.get(name="Mango")

    activities = [
        dict(
            crop=rice,
            activity_type="planting",
            date=dates["two_weeks"],
            notes="Direct seeding in lowland field.",
            area_ha=1.2,
            seed_qty_kg=55,
            fert_sacks=5,
            spacing="20x20 cm",
        ),
        dict(
            crop=corn,
            activity_type="watering",
            date=dates["last_week"],
            notes="Irrigation after dry spell.",
        ),
        dict(
            crop=mango,
            activity_type="harvesting",
            date=dates["yesterday"],
            notes="Early harvest due to incoming storm.",
        ),
    ]

    created = []
    for payload in activities:
        defaults = {
            "notes": payload.get("notes", ""),
            "area_ha": payload.get("area_ha"),
            "seed_qty_kg": payload.get("seed_qty_kg"),
            "fert_sacks": payload.get("fert_sacks"),
            "spacing": payload.get("spacing"),
        }
        # Drop keys that resolve to None so model defaults apply.
        defaults = {k: v for k, v in defaults.items() if v is not None}

        activity, _ = Activity.objects.update_or_create(
            farmer=farmer,
            crop=payload["crop"],
            activity_type=payload["activity_type"],
            date=payload["date"],
            defaults=defaults,
        )
        created.append(activity)
    return created


def _create_expenses(farmer):
    today = timezone.now().date()
    entries = [
        dict(expense_type="seed", amount=Decimal("3500.00"), date=today - timedelta(days=20), description="Certified rice seeds"),
        dict(expense_type="fertilizer", amount=Decimal("4200.50"), date=today - timedelta(days=10), description="Urea fertilizer"),
        dict(expense_type="labor", amount=Decimal("1800.00"), date=today - timedelta(days=3), description="Weeding labor"),
    ]
    created = []
    for data in entries:
        expense, _ = Expense.objects.update_or_create(
            farmer=farmer,
            expense_type=data["expense_type"],
            date=data["date"],
            defaults={
                "amount": data["amount"],
                "description": data["description"],
            },
        )
        created.append(expense)
    return created


def _create_reminders(farmer):
    today = timezone.now().date()
    reminders = [
        dict(message="Inspect rice field for pests", due_date=today + timedelta(days=2)),
        dict(message="Schedule technician visit for soil testing", due_date=today + timedelta(days=7)),
    ]
    for payload in reminders:
        Reminder.objects.update_or_create(
            farmer=farmer,
            message=payload["message"],
            defaults={"due_date": payload["due_date"]},
        )


def _create_recommendations():
    recs = [
        dict(crop_name="Rice", region="Ilocos Norte", month="July", reason="Monsoon rains ideal for transplanting."),
        dict(crop_name="Corn", region="Bukidnon", month="September", reason="Favorable temperature and rainfall pattern."),
    ]
    for entry in recs:
        crop = Crop.objects.filter(name=entry["crop_name"]).first()
        if not crop:
            continue
        Recommendation.objects.update_or_create(
            crop=crop,
            region=entry["region"],
            month=entry["month"],
            defaults={"reason": entry["reason"]},
        )


def _create_support_content():
    FAQ.objects.update_or_create(
        question="How do I reset my password?",
        defaults={"answer": "Use the “Forgot password” link on the login page and check your email for instructions."},
    )
    SupportContact.objects.get_or_create(
        name="Demo Farmer",
        email="demo_farmer@agritrack.demo",
        message="Need help exporting my expense report.",
    )


@transaction.atomic
def main():
    new_users = _create_users()
    crop_created, crop_updated = _create_crops()

    farmer_ben = User.objects.get(username="farmer_ben")
    farmer_rosa = User.objects.get(username="farmer_rosa")

    activities_ben = _create_activities(farmer_ben)
    activities_rosa = _create_activities(farmer_rosa)

    expenses_ben = _create_expenses(farmer_ben)
    expenses_rosa = _create_expenses(farmer_rosa)

    _create_reminders(farmer_ben)
    _create_reminders(farmer_rosa)
    _create_recommendations()
    _create_support_content()

    # Ensure forecasts in sync with planting activities
    planting_activities = Activity.objects.filter(activity_type='planting')
    refreshed = 0
    for act in planting_activities:
        data = compute_forecast_from_activity(act)
        Forecast.objects.update_or_create(
            farmer=act.farmer,
            crop=act.crop,
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
        refreshed += 1

    print("✅ Demo seed complete.")
    if new_users:
        print(f"   Created users: {', '.join(new_users)} (password: demo12345)")
    print(f"   Crops created: {crop_created} · updated: {crop_updated}")
    print(f"   Activities: {len(activities_ben) + len(activities_rosa)} · Expenses: {len(expenses_ben) + len(expenses_rosa)}")
    print("   Reminders, recommendations, FAQs, and support tickets populated.")


if __name__ == "__main__":
    main()

