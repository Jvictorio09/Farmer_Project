# seed_demo.py
# Usage:
#   DJANGO_SETTINGS_MODULE=myProject.settings python seed_demo.py
#
# Seeds a set of demo users, crops, activities, forecasts, expenses, reminders,
# and recommendations for walkthroughs.

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
    compute_forecast,
)

from seed_crops import DATA as CROP_DATA, upsert_crop


def _create_users():
    """Create demo admin, technician, and farmers."""
    users = [
        dict(username="admin", email="admin@Agriplus.demo", role="admin"),
        dict(username="tech_ana", email="tech@Agriplus.demo", role="technician", first_name="Ana"),
        dict(username="farmer_ben", email="ben@Agriplus.demo", role="farmer", first_name="Ben", region="Ilocos Norte"),
        dict(username="farmer_rosa", email="rosa@Agriplus.demo", role="farmer", first_name="Rosa", region="Bukidnon"),
        dict(username="farmer_carlos", email="carlos@Agriplus.demo", role="farmer", first_name="Carlos", region="Laguna"),
        dict(username="farmer_let", email="let@Agriplus.demo", role="farmer", first_name="Let", region="Cebu", password="let12345"),
    ]
    created = []
    admin_user = None
    
    for entry in users:
        user, is_new = User.objects.update_or_create(
            username=entry["username"],
            defaults={
                "email": entry.get("email", ""),
                "role": entry["role"],
                "first_name": entry.get("first_name", ""),
                "region": entry.get("region", ""),
                "is_active": True,  # Ensure user is active
                "is_staff": entry["role"] == "admin",  # Admins get staff access
            },
        )
        # Always set password to ensure it's correct, even for existing users
        user.set_password(entry.get("password", "demo12345"))
        # Ensure user is active
        user.is_active = True
        user.is_staff = entry["role"] == "admin"
        user.save()  # Save all fields
        
        # Store admin user for later assignment
        if entry["role"] == "admin":
            admin_user = user
        
        if is_new:
            created.append(user.username)
    
    # Assign all farmers to the admin user
    if admin_user:
        farmers = User.objects.filter(role='farmer')
        assigned_count = 0
        for farmer in farmers:
            farmer.assigned_admin = admin_user
            farmer.save()
            assigned_count += 1
        print(f"✅ Assigned {assigned_count} farmer(s) to admin")
    
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


def _create_activities(farmer):
    """Create activities throughout December 2025 and January 2026."""
    rice_rc216 = Crop.objects.get(name="Rice - NSIC Rc216")
    rice_rc222 = Crop.objects.get(name="Rice - NSIC Rc222")
    yellow_corn = Crop.objects.get(name="Yellow Corn (Hybrid)")
    white_corn = Crop.objects.get(name="White Corn (Open Pollinated)")
    
    # Create a realistic activity schedule
    # Planting activities (early in the period)
    # Watering activities (regularly throughout)
    # Harvesting activities (later in the period)
    
    activities = []
    
    # December 2025 activities
    activities.append(dict(
        crop=rice_rc216,
        activity_type="planting",
        date=date(2025, 12, 3),
        notes="Direct seeding NSIC Rc216 in lowland field. Prepared soil with organic compost.",
        area_ha=1.2,
        seed_qty_kg=55,
        fert_sacks=5,
        spacing="20x20 cm",
    ))
    
    activities.append(dict(
        crop=yellow_corn,
        activity_type="planting",
        date=date(2025, 12, 8),
        notes="Planted yellow corn hybrid in upland area.",
        area_ha=0.8,
        seed_qty_kg=18,
        fert_sacks=5,
        spacing="75x25 cm",
    ))
    
    activities.append(dict(
        crop=rice_rc222,
        activity_type="planting",
        date=date(2025, 12, 10),
        notes="Planted NSIC Rc222 variety in second field. Transplanted method.",
        area_ha=0.9,
        seed_qty_kg=50,
        fert_sacks=5,
        spacing="20x20 cm",
    ))
    
    activities.append(dict(
        crop=white_corn,
        activity_type="planting",
        date=date(2025, 12, 12),
        notes="Planted white corn open pollinated variety.",
        area_ha=0.7,
        seed_qty_kg=15,
        fert_sacks=4,
        spacing="75x25 cm",
    ))
    
    activities.append(dict(
        crop=rice_rc216,
        activity_type="watering",
        date=date(2025, 12, 15),
        notes="First irrigation after planting. Field conditions good.",
        area_ha=1.2,
    ))
    
    activities.append(dict(
        crop=yellow_corn,
        activity_type="watering",
        date=date(2025, 12, 18),
        notes="Irrigation applied. Monitoring soil moisture.",
        area_ha=0.8,
    ))
    
    activities.append(dict(
        crop=rice_rc222,
        activity_type="watering",
        date=date(2025, 12, 20),
        notes="Regular watering schedule. No issues observed.",
        area_ha=0.9,
    ))
    
    activities.append(dict(
        crop=white_corn,
        activity_type="watering",
        date=date(2025, 12, 22),
        notes="Irrigation after dry spell. Plants showing good growth.",
        area_ha=0.7,
    ))
    
    activities.append(dict(
        crop=rice_rc216,
        activity_type="watering",
        date=date(2025, 12, 25),
        notes="Holiday season maintenance. Field in good condition.",
        area_ha=1.2,
    ))
    
    activities.append(dict(
        crop=yellow_corn,
        activity_type="watering",
        date=date(2025, 12, 28),
        notes="End of month irrigation. Monitoring crop development.",
        area_ha=0.8,
    ))
    
    # January 2026 activities
    activities.append(dict(
        crop=rice_rc222,
        activity_type="watering",
        date=date(2026, 1, 5),
        notes="New year maintenance. Rice field progressing well.",
        area_ha=0.9,
    ))
    
    activities.append(dict(
        crop=white_corn,
        activity_type="watering",
        date=date(2026, 1, 8),
        notes="Regular irrigation. Corn plants healthy.",
        area_ha=0.7,
    ))
    
    activities.append(dict(
        crop=rice_rc216,
        activity_type="watering",
        date=date(2026, 1, 12),
        notes="Mid-month irrigation. No pest issues detected.",
        area_ha=1.2,
    ))
    
    activities.append(dict(
        crop=yellow_corn,
        activity_type="watering",
        date=date(2026, 1, 15),
        notes="Watering schedule maintained. Good weather conditions.",
        area_ha=0.8,
    ))
    
    activities.append(dict(
        crop=white_corn,
        activity_type="harvesting",
        date=date(2026, 1, 18),
        notes="White corn harvest completed. Good yield achieved.",
        area_ha=0.7,
    ))
    
    activities.append(dict(
        crop=rice_rc222,
        activity_type="watering",
        date=date(2026, 1, 20),
        notes="Continued irrigation. Rice plants maturing.",
        area_ha=0.9,
    ))
    
    activities.append(dict(
        crop=yellow_corn,
        activity_type="harvesting",
        date=date(2026, 1, 25),
        notes="Yellow corn harvest completed. Good yield achieved.",
        area_ha=0.8,
    ))
    
    activities.append(dict(
        crop=rice_rc216,
        activity_type="harvesting",
        date=date(2026, 1, 28),
        notes="NSIC Rc216 harvest completed. Successful season overall.",
        area_ha=1.2,
    ))
    
    activities.append(dict(
        crop=rice_rc222,
        activity_type="watering",
        date=date(2026, 1, 30),
        notes="Final irrigation before harvest. Field inspection done.",
        area_ha=0.9,
    ))

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


def _create_activities_upcoming_harvest(farmer):
    """Create activities for farmer_carlos with a harvest within 5 days of Feb 16, 2026."""
    rice_rc222 = Crop.objects.get(name="Rice - NSIC Rc222")
    
    # Rice has days_to_harvest_min = 110
    # To get harvest_start on Feb 18, 2026 (2 days from today), plant on Nov 1, 2025 (110 days earlier)
    planting_date = date(2025, 11, 1)  # 110 days before Feb 18, 2026
    
    activities = []
    
    # Planting activity that will result in harvest_start on Feb 18, 2026
    activities.append(dict(
        crop=rice_rc222,
        activity_type="planting",
        date=planting_date,
        notes="Planted NSIC Rc222 rice variety. Direct seeding method. Applied organic compost.",
        area_ha=1.0,
        seed_qty_kg=50,
        fert_sacks=5,
        spacing="20x20 cm",
    ))
    
    # Some watering activities
    activities.append(dict(
        crop=rice_rc222,
        activity_type="watering",
        date=date(2025, 11, 10),
        notes="First irrigation after planting. Soil moisture good.",
        area_ha=1.0,
    ))
    
    activities.append(dict(
        crop=rice_rc222,
        activity_type="watering",
        date=date(2025, 12, 5),
        notes="Regular watering schedule. Plants growing well.",
        area_ha=1.0,
    ))
    
    activities.append(dict(
        crop=rice_rc222,
        activity_type="watering",
        date=date(2026, 1, 15),
        notes="Mid-season irrigation. Rice plants maturing.",
        area_ha=1.0,
    ))
    
    activities.append(dict(
        crop=rice_rc222,
        activity_type="watering",
        date=date(2026, 2, 10),
        notes="Final watering before harvest. Rice ready soon.",
        area_ha=1.0,
    ))

    created = []
    for payload in activities:
        defaults = {
            "notes": payload.get("notes", ""),
            "area_ha": payload.get("area_ha"),
            "seed_qty_kg": payload.get("seed_qty_kg"),
            "fert_sacks": payload.get("fert_sacks"),
            "spacing": payload.get("spacing"),
        }
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


def _create_activities_farmer_let(farmer):
    """Create activities for farmer_let with backdated logs from Feb 3 onwards (watering, etc.)."""
    rice_rc216 = Crop.objects.get(name="Rice - NSIC Rc216")
    rice_rc222 = Crop.objects.get(name="Rice - NSIC Rc222")
    yellow_corn = Crop.objects.get(name="Yellow Corn (Hybrid)")
    white_corn = Crop.objects.get(name="White Corn (Open Pollinated)")

    activities = []

    # Planting activities in January 2026 (so we have crops to water from Feb 3 onwards)
    activities.append(dict(
        crop=yellow_corn,
        activity_type="planting",
        date=date(2026, 1, 6),
        notes="Planted yellow corn hybrid in upland area.",
        area_ha=1.0,
        seed_qty_kg=18,
        fert_sacks=5,
        spacing="75x25 cm",
    ))
    activities.append(dict(
        crop=rice_rc216,
        activity_type="planting",
        date=date(2026, 1, 10),
        notes="Direct seeding NSIC Rc216. Prepared soil with organic compost.",
        area_ha=1.2,
        seed_qty_kg=55,
        fert_sacks=5,
        spacing="20x20 cm",
    ))
    activities.append(dict(
        crop=rice_rc222,
        activity_type="planting",
        date=date(2026, 1, 15),
        notes="Planted NSIC Rc222 variety. Transplanted method.",
        area_ha=0.9,
        seed_qty_kg=50,
        fert_sacks=5,
        spacing="20x20 cm",
    ))

    # Watering activities from Feb 3 onwards
    activities.append(dict(
        crop=yellow_corn,
        activity_type="watering",
        date=date(2026, 2, 3),
        notes="First irrigation in February. Field conditions good.",
        area_ha=1.0,
    ))
    activities.append(dict(
        crop=rice_rc216,
        activity_type="watering",
        date=date(2026, 2, 3),
        notes="Irrigation applied. Monitoring soil moisture.",
        area_ha=1.2,
    ))
    activities.append(dict(
        crop=yellow_corn,
        activity_type="watering",
        date=date(2026, 2, 7),
        notes="Regular watering schedule. Plants showing good growth.",
        area_ha=1.0,
    ))
    activities.append(dict(
        crop=rice_rc222,
        activity_type="watering",
        date=date(2026, 2, 10),
        notes="First irrigation after transplanting. Rice field progressing well.",
        area_ha=0.9,
    ))
    activities.append(dict(
        crop=rice_rc216,
        activity_type="watering",
        date=date(2026, 2, 12),
        notes="Mid-month irrigation. No pest issues detected.",
        area_ha=1.2,
    ))
    activities.append(dict(
        crop=yellow_corn,
        activity_type="watering",
        date=date(2026, 2, 15),
        notes="Watering schedule maintained. Good weather conditions.",
        area_ha=1.0,
    ))
    activities.append(dict(
        crop=rice_rc222,
        activity_type="watering",
        date=date(2026, 2, 18),
        notes="Continued irrigation. Rice plants maturing.",
        area_ha=0.9,
    ))
    activities.append(dict(
        crop=rice_rc216,
        activity_type="watering",
        date=date(2026, 2, 22),
        notes="Irrigation before dry spell. Field in good condition.",
        area_ha=1.2,
    ))
    activities.append(dict(
        crop=yellow_corn,
        activity_type="watering",
        date=date(2026, 2, 25),
        notes="End of month irrigation. Monitoring crop development.",
        area_ha=1.0,
    ))
    activities.append(dict(
        crop=rice_rc222,
        activity_type="watering",
        date=date(2026, 2, 28),
        notes="Final irrigation before harvest window. Rice ready soon.",
        area_ha=0.9,
    ))
    # March 2026 watering
    activities.append(dict(
        crop=yellow_corn,
        activity_type="watering",
        date=date(2026, 3, 5),
        notes="Regular irrigation. Corn plants healthy.",
        area_ha=1.0,
    ))
    activities.append(dict(
        crop=rice_rc216,
        activity_type="watering",
        date=date(2026, 3, 8),
        notes="Maintenance irrigation. Field conditions good.",
        area_ha=1.2,
    ))

    created = []
    for payload in activities:
        defaults = {
            "notes": payload.get("notes", ""),
            "area_ha": payload.get("area_ha"),
            "seed_qty_kg": payload.get("seed_qty_kg"),
            "fert_sacks": payload.get("fert_sacks"),
            "spacing": payload.get("spacing"),
        }
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
    """Create expenses distributed across December 2025 and January 2026."""
    # Get crop objects
    rice_rc216 = Crop.objects.get(name="Rice - NSIC Rc216")
    rice_rc222 = Crop.objects.get(name="Rice - NSIC Rc222")
    yellow_corn = Crop.objects.get(name="Yellow Corn (Hybrid)")
    white_corn = Crop.objects.get(name="White Corn (Open Pollinated)")
    
    entries = [
        dict(expense_type="seed", amount=Decimal("3500.00"), date=date(2025, 12, 2), description="Certified rice seeds for planting", crop=rice_rc216),
        dict(expense_type="fertilizer", amount=Decimal("4200.50"), date=date(2025, 12, 5), description="Urea fertilizer - initial application", crop=rice_rc216),
        dict(expense_type="labor", amount=Decimal("1800.00"), date=date(2025, 12, 15), description="Field preparation and weeding labor", crop=rice_rc216),
        dict(expense_type="fertilizer", amount=Decimal("3800.00"), date=date(2025, 12, 20), description="NPK fertilizer for corn field", crop=yellow_corn),
        dict(expense_type="labor", amount=Decimal("2200.00"), date=date(2025, 12, 23), description="Corn harvesting labor", crop=yellow_corn),
        dict(expense_type="seed", amount=Decimal("2800.00"), date=date(2026, 1, 2), description="Corn seeds for replanting", crop=white_corn),
        dict(expense_type="fertilizer", amount=Decimal("3500.00"), date=date(2026, 1, 10), description="Top dressing fertilizer application", crop=rice_rc222),
        dict(expense_type="labor", amount=Decimal("2500.00"), date=date(2026, 1, 18), description="Harvesting labor - white corn", crop=white_corn),
        dict(expense_type="labor", amount=Decimal("3000.00"), date=date(2026, 1, 28), description="Rice harvesting and threshing labor", crop=rice_rc216),
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
                "crop": data.get("crop"),
            },
        )
        created.append(expense)
    return created


def _create_expenses_farmer_let(farmer):
    """Create expenses for farmer_let (Feb 2026 onwards)."""
    rice_rc216 = Crop.objects.get(name="Rice - NSIC Rc216")
    rice_rc222 = Crop.objects.get(name="Rice - NSIC Rc222")
    yellow_corn = Crop.objects.get(name="Yellow Corn (Hybrid)")

    entries = [
        dict(expense_type="seed", amount=Decimal("3200.00"), date=date(2026, 1, 5), description="Yellow corn seeds", crop=yellow_corn),
        dict(expense_type="seed", amount=Decimal("3800.00"), date=date(2026, 1, 8), description="Rice seeds NSIC Rc216", crop=rice_rc216),
        dict(expense_type="fertilizer", amount=Decimal("4500.00"), date=date(2026, 1, 12), description="Urea and NPK for rice", crop=rice_rc216),
        dict(expense_type="fertilizer", amount=Decimal("3600.00"), date=date(2026, 1, 14), description="Corn fertilizer", crop=yellow_corn),
        dict(expense_type="labor", amount=Decimal("2000.00"), date=date(2026, 2, 5), description="Field preparation", crop=rice_rc222),
        dict(expense_type="labor", amount=Decimal("1500.00"), date=date(2026, 2, 15), description="Irrigation labor", crop=yellow_corn),
        dict(expense_type="labor", amount=Decimal("1800.00"), date=date(2026, 3, 1), description="Weeding and maintenance", crop=rice_rc216),
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
                "crop": data.get("crop"),
            },
        )
        created.append(expense)
    return created


def _create_reminders(farmer):
    """Create reminders with dates in December 2025 and January 2026."""
    reminders = [
        dict(message="Inspect rice field for pests", due_date=date(2025, 12, 15)),
        dict(message="Schedule technician visit for soil testing", due_date=date(2025, 12, 20)),
        dict(message="Apply second round of fertilizer", due_date=date(2026, 1, 5)),
        dict(message="Prepare for corn harvest", due_date=date(2026, 1, 22)),
        dict(message="Schedule rice harvest equipment", due_date=date(2026, 1, 25)),
    ]
    for payload in reminders:
        Reminder.objects.update_or_create(
            farmer=farmer,
            message=payload["message"],
            defaults={"due_date": payload["due_date"]},
        )


def _create_recommendations():
    recs = [
        dict(crop_name="Rice - NSIC Rc216", region="Ilocos Norte", month="July", reason="Monsoon rains ideal for transplanting."),
        dict(crop_name="Rice - NSIC Rc222", region="Ilocos Norte", month="July", reason="Monsoon rains ideal for transplanting."),
        dict(crop_name="Yellow Corn (Hybrid)", region="Bukidnon", month="September", reason="Favorable temperature and rainfall pattern."),
        dict(crop_name="White Corn (Open Pollinated)", region="Bukidnon", month="September", reason="Favorable temperature and rainfall pattern."),
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
    # FAQ and SupportContact models were removed in migration 0004
    # This function is kept for compatibility but does nothing
    pass


@transaction.atomic
def main():
    new_users = _create_users()
    crop_created, crop_updated = _create_crops()

    farmer_ben = User.objects.get(username="farmer_ben")
    farmer_rosa = User.objects.get(username="farmer_rosa")
    farmer_carlos = User.objects.get(username="farmer_carlos")
    farmer_let = User.objects.get(username="farmer_let")

    # Delete existing activities, expenses, forecasts, and reminders for clean slate
    demo_farmers = [farmer_ben, farmer_rosa, farmer_carlos, farmer_let]
    Activity.objects.filter(farmer__in=demo_farmers).delete()
    Expense.objects.filter(farmer__in=demo_farmers).delete()
    Forecast.objects.filter(farmer__in=demo_farmers).delete()
    Reminder.objects.filter(farmer__in=demo_farmers).delete()

    activities_ben = _create_activities(farmer_ben)
    activities_rosa = _create_activities(farmer_rosa)
    activities_carlos = _create_activities_upcoming_harvest(farmer_carlos)
    activities_let = _create_activities_farmer_let(farmer_let)

    expenses_ben = _create_expenses(farmer_ben)
    expenses_rosa = _create_expenses(farmer_rosa)
    expenses_carlos = _create_expenses(farmer_carlos)
    expenses_let = _create_expenses_farmer_let(farmer_let)

    _create_reminders(farmer_ben)
    _create_reminders(farmer_rosa)
    _create_reminders(farmer_carlos)
    _create_reminders(farmer_let)
    _create_recommendations()
    _create_support_content()

    # Ensure forecasts in sync with planting activities
    # Use the planting date as forecast_date for historical accuracy
    planting_activities = Activity.objects.filter(activity_type='planting')
    refreshed = 0
    for act in planting_activities:
        data = compute_forecast(act)
        Forecast.objects.update_or_create(
            farmer=act.farmer,
            crop=act.crop,
            forecast_date=act.date,  # Use planting date instead of today
            defaults={
                "expected_yield_kg": data["expected"],
                "yield_min_kg": data["min"],
                "yield_max_kg": data["max"],
                "season_factor": 1.0,  # Default value, not calculated in compute_forecast
                "input_factor": 1.0,  # Default value, not calculated in compute_forecast
                "population_factor": 1.0,  # Default value, not calculated in compute_forecast
                "harvest_start": data["harvest_start"],
                "harvest_end": data["harvest_end"],
                "notes": data["notes"],
                "created_at": timezone.now(),
            }
        )
        refreshed += 1

    total_activities = len(activities_ben) + len(activities_rosa) + len(activities_carlos) + len(activities_let)
    total_expenses = len(expenses_ben) + len(expenses_rosa) + len(expenses_carlos) + len(expenses_let)

    print("✅ Demo seed complete.")
    if new_users:
        print(f"   Created users: {', '.join(new_users)} (default password: demo12345)")
    print(f"   Crops created: {crop_created} · updated: {crop_updated}")
    print(f"   Activities: {total_activities} · Expenses: {total_expenses}")
    print("   Reminders and recommendations populated.")
    print(f"   farmer_let / let12345 — backdated logs from Feb 3 onwards (watering, etc.)")
    print(f"   farmer_carlos — harvest within 5 days (Feb 18, 2026) to test notifications.")


if __name__ == "__main__":
    main()

