from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
import csv
import calendar
from io import BytesIO
from reportlab.pdfgen import canvas

from .forms import (
    CustomUserCreationForm,
    ActivityForm,
    CropForm,
    ExpenseForm,
)

from .models import (
    User,
    Activity,
    Crop,
    Forecast,
    Expense,
    Reminder,
    Recommendation,
)

# =====================================================
# 🔐 AUTH
# =====================================================

def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("farmer_dashboard")
    else:
        form = CustomUserCreationForm()
    return render(request, "auth/register.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


def role_redirect_view(request):
    if not request.user.is_authenticated:
        return redirect("login")

    if request.user.role == "admin":
        return redirect("/admin/")

    return redirect("farmer_dashboard")


# =====================================================
# 🌾 FARMER DASHBOARD
# =====================================================
@login_required
def farmer_dashboard(request):
    user = request.user
    today = timezone.now().date()
    current_month = today.strftime("%B")

    # ---------- ALL Forecasts (for Snapshot) ----------
    all_forecasts = (
        Forecast.objects
        .filter(farmer=user)
        .select_related("crop")
        .order_by("harvest_start")
    )

    # ---------- Upcoming Forecasts (for Next Harvest only) ----------
    forecasts = all_forecasts.filter(harvest_end__gte=today)

    # ---------- Expenses per Crop ----------
    expenses = Expense.objects.filter(farmer=user).select_related("crop")
    expense_by_crop = {}

    for e in expenses:
        crop_name = e.crop.name if e.crop else "Unassigned"
        expense_by_crop.setdefault(crop_name, {"items": [], "total": 0})
        expense_by_crop[crop_name]["items"].append(e)
        expense_by_crop[crop_name]["total"] += float(e.amount)

    total_expenses = expenses.aggregate(total=Sum("amount"))["total"] or 0

    # ---------- Crop Cost Efficiency ----------
    expense_summary = (
        Expense.objects
        .filter(farmer=user)
        .values("crop")
        .annotate(total=Sum("amount"))
    )

    crop_efficiency = {}

    for item in expense_summary:
        crop_id = item["crop"]
        total_expense = float(item["total"])

        crop = Crop.objects.filter(id=crop_id).first()
        crop_name = crop.name if crop else "Unassigned"

        forecast = Forecast.objects.filter(
            farmer=user,
            crop=crop
        ).order_by("-created_at").first()

        harvest_kg = float(forecast.expected_yield_kg) if forecast else 0
        cost_per_kg = total_expense / harvest_kg if harvest_kg > 0 else 0

        crop_efficiency[crop_name] = {
            "total_expense": total_expense,
            "harvest_kg": harvest_kg,
            "cost_per_kg": cost_per_kg,
        }

    # ---------- Activities ----------
    recent_activities = (
        Activity.objects
        .filter(farmer=user)
        .order_by("-date")[:5]
    )

    # ---------- Reminders ----------
    reminders = Reminder.objects.filter(
        farmer=user,
        due_date__gte=today
    ).order_by("due_date")

    # ---------- Recommendations ----------
    recommended_crops = []

    for rec in Recommendation.objects.all():
        if not rec.month:
            continue

        months = [m.strip() for m in rec.month.split(",") if m.strip()]

        recommended_crops.append({
            "crop": rec.crop,
            "season_match": current_month in months,
            "avg_yield": rec.crop.yield_t_max,
            "avg_days": rec.crop.days_to_harvest_min,
        })

    return render(request, "myApp/farmer_dashboard.html", {
        "forecasts": forecasts,              # for Next Harvest
        "all_forecasts": all_forecasts,      # for Forecast Snapshot
        "expense_by_crop": expense_by_crop,
        "total_expenses": total_expenses,
        "crop_efficiency": crop_efficiency,
        "recent_activities": recent_activities,
        "reminders": reminders,
        "recommended_crops": recommended_crops,
        "current_month": current_month,
        "today": today,
    })

# =====================================================
# 📋 ACTIVITIES
# =====================================================

@login_required
def activity_log_view(request):
    user = request.user
    activities = Activity.objects.filter(farmer=user).order_by("-date")
    crops = Crop.objects.all()

    form = ActivityForm()

    if request.method == "POST" and "add_activity" in request.POST:
        form = ActivityForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.farmer = user
            obj.save()
            messages.success(request, "Activity added")
            return redirect("activity_log")

    return render(request, "myApp/activity_log.html", {
        "activities": activities,
        "crops": crops,
        "form": form,
    })


@login_required
def planting_detail_view(request, pk):
    activity = get_object_or_404(
        Activity,
        pk=pk,
        farmer=request.user,
        activity_type="planting"
    )

    forecast = (
        Forecast.objects
        .filter(farmer=request.user, crop=activity.crop)
        .order_by("-created_at")
        .first()
    )

    return render(request, "myApp/planting_detail.html", {
        "activity": activity,
        "forecast": forecast,
    })


# =====================================================
# 💰 EXPENSES
# =====================================================

@login_required
def expense_log_view(request):
    user = request.user
    expenses = Expense.objects.filter(farmer=user).order_by("-date")
    form = ExpenseForm()

    if request.method == "POST" and "add_expense" in request.POST:
        form = ExpenseForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.farmer = user
            obj.save()
            return redirect("expense_log")

    total = expenses.aggregate(Sum("amount"))["amount__sum"] or 0

    return render(request, "myApp/expense_log.html", {
        "expenses": expenses,
        "form": form,
        "total": total,
    })


# =====================================================
# 🔔 REMINDERS
# =====================================================

@login_required
def add_reminder(request):
    if request.method == "POST":
        Reminder.objects.create(
            farmer=request.user,
            message=request.POST.get("message"),
            due_date=request.POST.get("due_date"),
        )
    return redirect("farmer_dashboard")


@login_required
def delete_reminder(request):
    if request.method == "POST":
        reminder_id = request.POST.get("reminder_id")
        reminder = get_object_or_404(Reminder, id=reminder_id, farmer=request.user)
        reminder.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": True, "message": "Reminder deleted."})
        messages.success(request, "Reminder deleted.")
    return redirect("farmer_dashboard")


@login_required
def update_reminder(request):
    if request.method == "POST":
        reminder_id = request.POST.get("reminder_id")
        reminder = get_object_or_404(Reminder, id=reminder_id, farmer=request.user)
        reminder.message = request.POST.get("message")
        reminder.due_date = request.POST.get("due_date")
        reminder.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": True, "message": "Reminder updated."})
        messages.success(request, "Reminder updated.")
    return redirect("farmer_dashboard")


# =====================================================
# ACTIVITY UPDATE/DELETE
# =====================================================

@login_required
def update_activity(request, pk):
    activity = get_object_or_404(Activity, pk=pk, farmer=request.user)
    if request.method == "POST":
        form = ActivityForm(request.POST, instance=activity)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.farmer = request.user
            obj.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": True, "message": "Activity updated successfully."})
            messages.success(request, "Activity updated successfully.")
            return redirect("activity_log")
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "id": activity.id,
                "crop": activity.crop.id,
                "activity_type": activity.activity_type,
                "date": activity.date.isoformat(),
                "notes": activity.notes or "",
                "area_ha": activity.area_ha or "",
                "seed_qty_kg": activity.seed_qty_kg or "",
                "fert_sacks": activity.fert_sacks or "",
                "spacing": activity.spacing or "",
            })
    form = ActivityForm(instance=activity)
    return render(request, "myApp/activity_log.html", {
        "form": form,
        "edit_activity": activity,
        "activities": Activity.objects.filter(farmer=request.user).order_by("-date"),
        "crops": Crop.objects.all(),
    })


@login_required
def delete_activity(request, pk):
    activity = get_object_or_404(Activity, pk=pk, farmer=request.user)
    if request.method == "POST":
        activity.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": True, "message": "Activity deleted."})
        messages.success(request, "Activity deleted.")
        return redirect("activity_log")
    return redirect("activity_log")


# =====================================================
# EXPENSE UPDATE/DELETE
# =====================================================

@login_required
def update_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, farmer=request.user)
    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.farmer = request.user
            obj.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": True, "message": "Expense updated successfully."})
            messages.success(request, "Expense updated successfully.")
            return redirect("expense_log")
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return JSON for AJAX requests
            return JsonResponse({
                "id": expense.id,
                "crop": expense.crop.id if expense.crop else None,
                "expense_type": expense.expense_type,
                "amount": str(expense.amount),
                "date": expense.date.isoformat(),
                "description": expense.description or "",
            })
    form = ExpenseForm(instance=expense)
    return render(request, "myApp/expense_log.html", {
        "form": form,
        "edit_expense": expense,
        "expenses": Expense.objects.filter(farmer=request.user).order_by("-date"),
        "total": Expense.objects.filter(farmer=request.user).aggregate(Sum("amount"))["amount__sum"] or 0,
    })


@login_required
def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, farmer=request.user)
    if request.method == "POST":
        expense.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": True, "message": "Expense deleted."})
        messages.success(request, "Expense deleted.")
        return redirect("expense_log")
    return redirect("expense_log")


# =====================================================
# CROP UPDATE/DELETE
# =====================================================

@login_required
def update_crop(request, pk):
    crop = get_object_or_404(Crop, pk=pk)
    if request.method == "POST":
        form = CropForm(request.POST, instance=crop)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": True, "message": "Crop updated successfully."})
            messages.success(request, "Crop updated successfully.")
            return redirect("activity_log")
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "id": crop.id,
                "name": crop.name,
                "description": crop.description or "",
                "ideal_seasons": crop.ideal_seasons or "",
                "days_to_harvest_min": crop.days_to_harvest_min or "",
                "days_to_harvest_max": crop.days_to_harvest_max or "",
                "seed_rate_min_kg": crop.seed_rate_min_kg or "",
                "seed_rate_max_kg": crop.seed_rate_max_kg or "",
                "fert_sacks_min": crop.fert_sacks_min or "",
                "fert_sacks_max": crop.fert_sacks_max or "",
                "yield_t_min": crop.yield_t_min or "",
                "yield_t_max": crop.yield_t_max or "",
            })
    form = CropForm(instance=crop)
    return render(request, "myApp/activity_log.html", {
        "crop_form": form,
        "edit_crop": crop,
        "activities": Activity.objects.filter(farmer=request.user).order_by("-date"),
        "crops": Crop.objects.all(),
        "form": ActivityForm(),
    })


@login_required
def delete_crop(request, pk):
    crop = get_object_or_404(Crop, pk=pk)
    if request.method == "POST":
        crop.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": True, "message": "Crop deleted."})
        messages.success(request, "Crop deleted.")
        return redirect("activity_log")
    return redirect("activity_log")

def flash_messages(request):
    return render(request, "partials/flash_messages.html")

@login_required
def export_activities_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="activities.csv"'

    writer = csv.writer(response)
    writer.writerow(['Crop', 'Activity Type', 'Date'])

    activities = Activity.objects.filter(farmer=request.user)

    for a in activities:
        writer.writerow([a.crop.name if a.crop else "N/A", a.activity_type, a.date])

    return response

@login_required
def export_activities_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="activities.pdf"'

    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    activities = Activity.objects.filter(
        farmer=request.user
    ).order_by("-date")

    y = 800
    p.drawString(50, y, "Activity Report")
    y -= 30

    for a in activities:
        line = f"{a.date} - {a.crop.name} - {a.activity_type}"
        p.drawString(50, y, line)
        y -= 20
        if y < 50:
            p.showPage()
            y = 800

    p.save()

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

@login_required
def chart_activities_by_type(request):
    qs = (
        Activity.objects
        .filter(farmer=request.user)
        .values("activity_type")
        .annotate(total=Count("id"))
        .order_by()
    )

    labels = [x["activity_type"].title() for x in qs]
    data = [x["total"] for x in qs]

    return JsonResponse({
        "labels": labels,
        "data": data
    })

@login_required
def chart_activities_monthly(request):
    qs = (
        Activity.objects
        .filter(farmer=request.user)
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )

    labels = [x["month"].strftime("%b %Y") for x in qs if x["month"]]
    data = [x["total"] for x in qs]

    return JsonResponse({
        "labels": labels,
        "data": data
    })


@login_required
def chart_activities_by_crop(request):
    qs = (
        Activity.objects
        .filter(farmer=request.user)
        .values("crop__name")
        .annotate(total=Count("id"))
        .order_by()
    )

    labels = [x["crop__name"] or "Unassigned" for x in qs]
    data = [x["total"] for x in qs]

    return JsonResponse({
        "labels": labels,
        "data": data
    })


@login_required
def chart_expenses_by_crop(request):
    qs = (
        Expense.objects
        .filter(farmer=request.user)
        .values("crop__name")
        .annotate(total=Sum("amount"))
    )

    labels = [x["crop__name"] or "Unassigned" for x in qs]
    data = [float(x["total"]) for x in qs]

    return JsonResponse({
        "labels": labels,
        "data": data
    })
