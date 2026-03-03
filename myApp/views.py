from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
from datetime import date, timedelta
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
            return redirect("home")  # Use role_redirect_view to handle role-based routing
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
        return redirect("admin_dashboard")
    
    if request.user.role == "technician":
        return redirect("technician_dashboard")

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

    # ---------- Crop Recommendations (All 4 Available Crops) ----------
    # Get all available crops in the system
    all_crops = Crop.objects.all().order_by('name')
    recommended_crops = []
    
    # Month abbreviations mapping
    month_abbr = {
        'January': 'Jan', 'February': 'Feb', 'March': 'Mar', 'April': 'Apr',
        'May': 'May', 'June': 'Jun', 'July': 'Jul', 'August': 'Aug',
        'September': 'Sep', 'October': 'Oct', 'November': 'Nov', 'December': 'Dec'
    }
    current_month_abbr = month_abbr.get(current_month, current_month[:3])
    
    for crop in all_crops:
        # Check if current month is in ideal seasons
        ideal_seasons = crop.ideal_seasons or ""
        season_match = False
        if ideal_seasons:
            # Parse seasons (e.g., "Jun-Nov, Dec-Apr")
            season_parts = [s.strip() for s in ideal_seasons.split(",")]
            for part in season_parts:
                if "-" in part:
                    # Handle ranges like "Jun-Nov" or "Dec-Apr"
                    months = part.split("-")
                    if len(months) == 2:
                        start_month = months[0].strip()
                        end_month = months[1].strip()
                        # Check if current month falls in range
                        month_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        try:
                            start_idx = month_list.index(start_month)
                            end_idx = month_list.index(end_month)
                            current_idx = month_list.index(current_month_abbr)
                            
                            # Handle year wrap-around (e.g., Dec-Apr)
                            if start_idx <= end_idx:
                                season_match = start_idx <= current_idx <= end_idx
                            else:  # Wraps around year
                                season_match = current_idx >= start_idx or current_idx <= end_idx
                        except (ValueError, IndexError):
                            # If parsing fails, default to True (show all crops)
                            season_match = True
                else:
                    # Single month check
                    if current_month_abbr in part or current_month in part:
                        season_match = True
        
        # Calculate average values
        avg_seed_rate = (crop.seed_rate_min_kg + crop.seed_rate_max_kg) / 2 if (crop.seed_rate_min_kg + crop.seed_rate_max_kg) > 0 else 0
        avg_fert = (crop.fert_sacks_min + crop.fert_sacks_max) / 2 if (crop.fert_sacks_min + crop.fert_sacks_max) > 0 else 0
        avg_yield = (crop.yield_t_min + crop.yield_t_max) / 2
        avg_days = (crop.days_to_harvest_min + crop.days_to_harvest_max) / 2
        
        recommended_crops.append({
            "crop": crop,
            "season_match": season_match if ideal_seasons else True,  # Show all if no season data
            "avg_yield": avg_yield,
            "yield_min": crop.yield_t_min,
            "yield_max": crop.yield_t_max,
            "avg_days": int(avg_days),
            "days_min": crop.days_to_harvest_min,
            "days_max": crop.days_to_harvest_max,
            "seed_rate_min": crop.seed_rate_min_kg,
            "seed_rate_max": crop.seed_rate_max_kg,
            "avg_seed_rate": avg_seed_rate,
            "fert_min": crop.fert_sacks_min,
            "fert_max": crop.fert_sacks_max,
            "avg_fert": avg_fert,
            "ideal_seasons": crop.ideal_seasons,
            "description": crop.description,
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
    expenses = Expense.objects.filter(farmer=user)
    
    # Filtering functionality
    crop_filter = request.GET.get('crop', '')
    expense_type_filter = request.GET.get('expense_type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Apply filters
    if crop_filter:
        expenses = expenses.filter(crop_id=crop_filter)
    if expense_type_filter:
        expenses = expenses.filter(expense_type=expense_type_filter)
    if date_from:
        expenses = expenses.filter(date__gte=date_from)
    if date_to:
        expenses = expenses.filter(date__lte=date_to)
    
    # Sorting functionality
    sort_by = request.GET.get('sort', '-date')  # Default: newest first
    
    # Valid sort fields
    valid_sort_fields = {
        'date': 'date',
        '-date': '-date',
        'crop': 'crop__name',
        '-crop': '-crop__name',
        'type': 'expense_type',
        '-type': '-expense_type',
        'amount': 'amount',
        '-amount': '-amount',
        'description': 'description',
        '-description': '-description',
    }
    
    # Get the sort field or default to date descending
    sort_field = valid_sort_fields.get(sort_by, '-date')
    expenses = expenses.order_by(sort_field)
    
    form = ExpenseForm()

    if request.method == "POST" and "add_expense" in request.POST:
        form = ExpenseForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.farmer = user
            obj.save()
            # Preserve filters and sort when redirecting
            redirect_url = "expense_log"
            query_params = []
            if sort_by != '-date':
                query_params.append(f'sort={sort_by}')
            if crop_filter:
                query_params.append(f'crop={crop_filter}')
            if expense_type_filter:
                query_params.append(f'expense_type={expense_type_filter}')
            if date_from:
                query_params.append(f'date_from={date_from}')
            if date_to:
                query_params.append(f'date_to={date_to}')
            if query_params:
                redirect_url += '?' + '&'.join(query_params)
            return redirect(redirect_url)

    total = expenses.aggregate(Sum("amount"))["amount__sum"] or 0
    
    # Get all crops for filter dropdown
    crops = Crop.objects.all().order_by('name')
    
    # Calculate expense breakdown by type when a crop is selected
    expense_breakdown = None
    selected_crop_name = None
    if crop_filter:
        # Get the selected crop name
        try:
            selected_crop = Crop.objects.get(id=crop_filter)
            selected_crop_name = selected_crop.name
        except Crop.DoesNotExist:
            selected_crop_name = None
        
        # Calculate breakdown by expense type for the selected crop
        breakdown_data = expenses.values('expense_type').annotate(
            total_amount=Sum('amount')
        ).order_by('expense_type')
        
        # Convert to list of dictionaries for easier template usage
        expense_breakdown = []
        
        # Color mapping for expense types
        color_map = {
            'seed': '#10B981',      # green
            'fertilizer': '#3B82F6', # blue
            'labor': '#F59E0B',      # amber
            'pesticide': '#EF4444',  # red
            'fuel': '#8B5CF6',      # purple
            'other': '#6B7280',     # gray
        }
        
        # Type display names
        type_display = {
            'seed': 'Seed',
            'fertilizer': 'Fertilizer',
            'labor': 'Labor',
            'pesticide': 'Pesticide',
            'fuel': 'Fuel',
            'other': 'Other',
        }
        
        for item in breakdown_data:
            expense_type = item['expense_type']
            expense_breakdown.append({
                'label': type_display.get(expense_type, expense_type.title()),
                'amount': float(item['total_amount']),
                'color': color_map.get(expense_type, '#6B7280')
            })

    return render(request, "myApp/expense_log.html", {
        "expenses": expenses,
        "form": form,
        "total": total,
        "current_sort": sort_by,
        "crops": crops,
        "current_crop_filter": crop_filter,
        "current_expense_type_filter": expense_type_filter,
        "date_from": date_from,
        "date_to": date_to,
        "expense_breakdown": expense_breakdown,
        "selected_crop_name": selected_crop_name,
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
    
    # Get current sort parameters
    sort_by = request.GET.get('sort', '-date')
    valid_sort_fields = {
        'date': 'date',
        '-date': '-date',
        'crop': 'crop__name',
        '-crop': '-crop__name',
        'type': 'expense_type',
        '-type': '-expense_type',
        'amount': 'amount',
        '-amount': '-amount',
        'description': 'description',
        '-description': '-description',
    }
    sort_field = valid_sort_fields.get(sort_by, '-date')
    expenses = Expense.objects.filter(farmer=request.user).order_by(sort_field)
    
    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.farmer = request.user
            obj.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": True, "message": "Expense updated successfully."})
            messages.success(request, "Expense updated successfully.")
            # Preserve sort parameter in redirect
            redirect_url = "expense_log"
            if sort_by != '-date':
                redirect_url += f"?sort={sort_by}"
            return redirect(redirect_url)
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
    total = expenses.aggregate(Sum("amount"))["amount__sum"] or 0
    return render(request, "myApp/expense_log.html", {
        "form": form,
        "edit_expense": expense,
        "expenses": expenses,
        "total": total,
        "current_sort": sort_by,
    })


@login_required
def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, farmer=request.user)
    if request.method == "POST":
        expense.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": True, "message": "Expense deleted."})
        messages.success(request, "Expense deleted.")
        # Preserve sort parameter in redirect
        sort_by = request.GET.get('sort', '-date')
        redirect_url = "expense_log"
        if sort_by != '-date':
            redirect_url += f"?sort={sort_by}"
        return redirect(redirect_url)
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


# =====================================================
# 📊 REPORTS & EXPORTS
# =====================================================

@login_required
def reports_view(request):
    """Reports page with all export options."""
    user = request.user
    today = timezone.now().date()
    
    # Get summary statistics
    total_activities = Activity.objects.filter(farmer=user).count()
    total_expenses = Expense.objects.filter(farmer=user).aggregate(Sum("amount"))["amount__sum"] or 0
    total_forecasts = Forecast.objects.filter(farmer=user).count()
    
    return render(request, "myApp/reports.html", {
        "total_activities": total_activities,
        "total_expenses": total_expenses,
        "total_forecasts": total_forecasts,
        "today": today,
    })


# =====================================================
# 📚 CROP REFERENCE GUIDE
# =====================================================
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

# If you don't already have it:
# from .models import Crop

@login_required
def crop_reference_guide(request):
    today = timezone.now().date()
    current_month_name = today.strftime("%B")

    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    month_name_to_abbr = {
        "January":"Jan","February":"Feb","March":"Mar","April":"Apr",
        "May":"May","June":"Jun","July":"Jul","August":"Aug",
        "September":"Sep","October":"Oct","November":"Nov","December":"Dec"
    }
    current_month_abbr = month_name_to_abbr.get(current_month_name, current_month_name[:3])

    # ---------- helper: parse "Jun-Nov, Dec-Apr" -> set({"Jun","Jul"...}) ----------
    def parse_ideal_months(ideal_seasons: str) -> set:
        if not ideal_seasons:
            return set()

        ideal_seasons = ideal_seasons.strip()
        if not ideal_seasons:
            return set()

        parts = [p.strip() for p in ideal_seasons.split(",") if p.strip()]
        months_set = set()

        def add_range(start_abbr: str, end_abbr: str):
            if start_abbr not in month_order or end_abbr not in month_order:
                return
            s = month_order.index(start_abbr)
            e = month_order.index(end_abbr)
            if s <= e:
                for i in range(s, e + 1):
                    months_set.add(month_order[i])
            else:
                # wrap-around (e.g., Dec-Apr)
                for i in range(s, 12):
                    months_set.add(month_order[i])
                for i in range(0, e + 1):
                    months_set.add(month_order[i])

        for part in parts:
            # normalize possible full month names to abbr if present (optional)
            # (Your data already uses abbr, so this is mostly safety.)
            if "-" in part:
                a, b = [x.strip() for x in part.split("-", 1)]
                # convert full names to abbr if needed
                a = month_name_to_abbr.get(a, a[:3])
                b = month_name_to_abbr.get(b, b[:3])
                add_range(a, b)
            else:
                token = month_name_to_abbr.get(part, part[:3])
                if token in month_order:
                    months_set.add(token)

        return months_set

    # ---------- Hardcoded reference data (unchanged) ----------
    reference_crops = [
        dict(
            name="Rice - NSIC Rc216",
            description="NSIC Rc216 rice variety. Direct-seeded or transplanted (20x20 cm).",
            ideal_seasons="Jun-Nov, Dec-Apr",
            seed_rate_min_kg=40, seed_rate_max_kg=60,
            fert_sacks_min=4, fert_sacks_max=6,
            yield_t_min=4, yield_t_max=6,
            days_to_harvest_min=110, days_to_harvest_max=130,
            available=True,
        ),
        dict(
            name="Rice - NSIC Rc222",
            description="NSIC Rc222 rice variety. Direct-seeded or transplanted (20x20 cm).",
            ideal_seasons="Jun-Nov, Dec-Apr",
            seed_rate_min_kg=40, seed_rate_max_kg=60,
            fert_sacks_min=4, fert_sacks_max=6,
            yield_t_min=4, yield_t_max=6,
            days_to_harvest_min=110, days_to_harvest_max=130,
            available=True,
        ),
        dict(
            name="Yellow Corn (Hybrid)",
            description="Yellow corn hybrid variety. 75 cm rows x 25 cm hills.",
            ideal_seasons="Jan-Dec",
            seed_rate_min_kg=15, seed_rate_max_kg=20,
            fert_sacks_min=4, fert_sacks_max=6,
            yield_t_min=4, yield_t_max=5,
            days_to_harvest_min=90, days_to_harvest_max=120,
            available=True,
        ),
        dict(
            name="White Corn (Open Pollinated)",
            description="White corn open pollinated variety. 75 cm rows x 25 cm hills.",
            ideal_seasons="Jan-Dec",
            seed_rate_min_kg=15, seed_rate_max_kg=20,
            fert_sacks_min=4, fert_sacks_max=6,
            yield_t_min=4, yield_t_max=5,
            days_to_harvest_min=90, days_to_harvest_max=120,
            available=True,
        ),
        dict(
            name="Rice (Generic)",
            description="Palay. Direct-seeded or transplanted (20x20 cm).",
            ideal_seasons="Jun-Nov, Dec-Apr",
            seed_rate_min_kg=40, seed_rate_max_kg=60,
            fert_sacks_min=4, fert_sacks_max=6,
            yield_t_min=4, yield_t_max=6,
            days_to_harvest_min=110, days_to_harvest_max=130,
            available=False,
        ),
        dict(
            name="Corn (Generic)",
            description="75 cm rows x 25 cm hills.",
            ideal_seasons="Jan-Dec",
            seed_rate_min_kg=15, seed_rate_max_kg=20,
            fert_sacks_min=4, fert_sacks_max=6,
            yield_t_min=4, yield_t_max=5,
            days_to_harvest_min=90, days_to_harvest_max=120,
            available=False,
        ),
        dict(
            name="Mango",
            description="Carabao variety. ~10x10 m (~100 trees/ha). Bearing stage yields.",
            ideal_seasons="Dec-Apr",
            seed_rate_min_kg=0, seed_rate_max_kg=0,
            fert_sacks_min=1, fert_sacks_max=2,
            yield_t_min=3, yield_t_max=5,
            days_to_harvest_min=120, days_to_harvest_max=150,
            available=False,
        ),
        dict(
            name="Banana",
            description="~3x3 m (~1100 plants/ha). Perennial; window is for first cycle.",
            ideal_seasons="Jan-Dec",
            seed_rate_min_kg=0, seed_rate_max_kg=0,
            fert_sacks_min=10, fert_sacks_max=15,
            yield_t_min=20, yield_t_max=30,
            days_to_harvest_min=270, days_to_harvest_max=360,
            available=False,
        ),
        dict(
            name="Papaya",
            description="~2x2 m (~2500 plants/ha). Starts fruiting ~8 months.",
            ideal_seasons="Jan-Dec",
            seed_rate_min_kg=0, seed_rate_max_kg=0,
            fert_sacks_min=4, fert_sacks_max=6,
            yield_t_min=25, yield_t_max=40,
            days_to_harvest_min=240, days_to_harvest_max=300,
            available=False,
        ),
        dict(
            name="Guava",
            description="~5x5 m (~400 trees/ha). Yields assume bearing trees.",
            ideal_seasons="Jan-Dec",
            seed_rate_min_kg=0, seed_rate_max_kg=0,
            fert_sacks_min=4, fert_sacks_max=8,
            yield_t_min=10, yield_t_max=15,
            days_to_harvest_min=540, days_to_harvest_max=720,
            available=False,
        ),
        dict(
            name="Sweet Potato",
            description="Vines; ~20,000 cuttings/ha.",
            ideal_seasons="Jan-Dec",
            seed_rate_min_kg=0, seed_rate_max_kg=0,
            fert_sacks_min=2, fert_sacks_max=4,
            yield_t_min=8, yield_t_max=12,
            days_to_harvest_min=90, days_to_harvest_max=120,
            available=False,
        ),
        dict(
            name="Cassava",
            description="Stem cuttings; 10–12k cuttings/ha.",
            ideal_seasons="Jan-Dec",
            seed_rate_min_kg=0, seed_rate_max_kg=0,
            fert_sacks_min=3, fert_sacks_max=5,
            yield_t_min=20, yield_t_max=30,
            days_to_harvest_min=270, days_to_harvest_max=360,
            available=False,
        ),
        dict(
            name="Vegetables",
            description="Generic bucket (eggplant, tomato, okra, ampalaya).",
            ideal_seasons="Jan-Dec",
            seed_rate_min_kg=1, seed_rate_max_kg=6,
            fert_sacks_min=4, fert_sacks_max=6,
            yield_t_min=10, yield_t_max=20,
            days_to_harvest_min=70, days_to_harvest_max=120,
            available=False,
        ),
        dict(
            name="Onion",
            description="Bulb onion; seed 3–4 kg/ha (or bulbs 20–25 kg).",
            ideal_seasons="Nov-Feb",
            seed_rate_min_kg=3, seed_rate_max_kg=4,
            fert_sacks_min=5, fert_sacks_max=7,
            yield_t_min=8, yield_t_max=12,
            days_to_harvest_min=90, days_to_harvest_max=120,
            available=False,
        ),
        dict(
            name="Garlic",
            description="Cloves ~1000–1200 kg/ha.",
            ideal_seasons="Nov-Feb",
            seed_rate_min_kg=1000, seed_rate_max_kg=1200,
            fert_sacks_min=5, fert_sacks_max=7,
            yield_t_min=4, yield_t_max=6,
            days_to_harvest_min=150, days_to_harvest_max=180,
            available=False,
        ),
        dict(
            name="Sugarcane",
            description="Setts; 35–40k cuttings/ha. ~5–6 tons sugar per 60–80 tons cane.",
            ideal_seasons="Jan-Dec",
            seed_rate_min_kg=0, seed_rate_max_kg=0,
            fert_sacks_min=8, fert_sacks_max=12,
            yield_t_min=60, yield_t_max=80,
            days_to_harvest_min=300, days_to_harvest_max=420,
            available=False,
        ),
        dict(
            name="Tobacco",
            description="~50x60 cm spacing.",
            ideal_seasons="Dec-Mar",
            seed_rate_min_kg=0.5, seed_rate_max_kg=1.0,
            fert_sacks_min=4, fert_sacks_max=6,
            yield_t_min=1, yield_t_max=2,
            days_to_harvest_min=90, days_to_harvest_max=130,
            available=False,
        ),
    ]

    # crops actually usable in the system (DB)
    available_crop_names = set(Crop.objects.values_list("name", flat=True))

    processed_crops = []
    for crop in reference_crops:
        crop_name = crop["name"]

        # availability: keep hardcoded but validate vs DB names
        is_available = crop.get("available", False)
        if crop_name in available_crop_names:
            is_available = True
        elif not is_available:
            for available_name in available_crop_names:
                if crop_name in available_name or available_name in crop_name:
                    is_available = True
                    break

        ideal_months = parse_ideal_months(crop.get("ideal_seasons", ""))

        # season match for CURRENT month (used for “Recommended this month”)
        season_match = current_month_abbr in ideal_months if ideal_months else False

        # averages
        avg_seed_rate = (
            (crop["seed_rate_min_kg"] + crop["seed_rate_max_kg"]) / 2
            if (crop["seed_rate_min_kg"] + crop["seed_rate_max_kg"]) > 0 else 0
        )
        avg_fert = (
            (crop["fert_sacks_min"] + crop["fert_sacks_max"]) / 2
            if (crop["fert_sacks_min"] + crop["fert_sacks_max"]) > 0 else 0
        )
        avg_yield = (crop["yield_t_min"] + crop["yield_t_max"]) / 2
        avg_days = (crop["days_to_harvest_min"] + crop["days_to_harvest_max"]) / 2

        processed_crops.append({
            **crop,
            "available": is_available,
            "season_match": season_match,
            "ideal_months": sorted(list(ideal_months), key=lambda m: month_order.index(m)) if ideal_months else [],
            "avg_seed_rate": avg_seed_rate,
            "avg_fert": avg_fert,
            "avg_yield": avg_yield,
            "avg_days": int(avg_days),
        })

    available_count = sum(1 for c in processed_crops if c["available"])

    # Build year calendar: month -> crops ideal that month
    calendar = []
    for abbr in month_order:
        month_crops = []
        for c in processed_crops:
            # if no ideal_months, treat as "unknown" (you can choose to include or exclude)
            if c["ideal_months"] and abbr in c["ideal_months"]:
                month_crops.append(c)

        # optional: sort so “Available” appears first
        month_crops.sort(key=lambda x: (not x["available"], x["name"]))

        calendar.append({
            "abbr": abbr,
            "name": next((k for k,v in month_name_to_abbr.items() if v == abbr), abbr),
            "is_current": (abbr == current_month_abbr),
            "crops": month_crops,
        })

    return render(request, "myApp/crop_reference_guide.html", {
        "reference_crops": processed_crops,   # still useful for list view / fallback
        "calendar": calendar,                 # NEW: for year view
        "current_month": current_month_name,
        "current_month_abbr": current_month_abbr,
        "today": today,
        "available_count": available_count,
    })


@login_required
def export_expenses_csv(request):
    """Export expenses to CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Crop', 'Type', 'Amount', 'Description'])

    expenses = Expense.objects.filter(farmer=request.user).order_by("-date")

    for e in expenses:
        writer.writerow([
            e.date,
            e.crop.name if e.crop else "N/A",
            e.expense_type,
            e.amount,
            e.description
        ])

    return response


@login_required
def export_expenses_pdf(request):
    """Export expenses to PDF."""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="expenses.pdf"'

    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    expenses = Expense.objects.filter(
        farmer=request.user
    ).order_by("-date")

    today = timezone.now().date()
    y = 800
    p.drawString(50, y, "Expense Report")
    y -= 30
    p.drawString(50, y, f"Generated: {today.strftime('%B %d, %Y')}")
    y -= 40

    for e in expenses:
        crop_name = e.crop.name if e.crop else "N/A"
        line = f"{e.date} - {crop_name} - {e.expense_type} - ₱{e.amount}"
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


# =====================================================
# 👑 ADMIN DASHBOARD
# =====================================================

@login_required
def admin_dashboard(request):
    """Admin dashboard showing assigned farmers and system stats"""
    if not request.user.is_admin():
        messages.error(request, "Access denied. Admin only.")
        return redirect("farmer_dashboard")
    
    # Get only farmers assigned to this admin
    farmers = User.objects.filter(role='farmer', assigned_admin=request.user).order_by('-date_joined')
    
    # Statistics for assigned farmers only
    total_farmers = farmers.count()
    total_technicians = User.objects.filter(role='technician').count()
    total_admins = User.objects.filter(role='admin').count()
    
    # Get assigned farmer IDs for filtering
    assigned_farmer_ids = farmers.values_list('id', flat=True)
    
    # Crop statistics (only for assigned farmers)
    total_activities = Activity.objects.filter(farmer_id__in=assigned_farmer_ids).count()
    total_plantings = Activity.objects.filter(
        activity_type='planting',
        farmer_id__in=assigned_farmer_ids
    ).count()
    total_crops = Crop.objects.count()  # Total crops available in system
    
    # Get crops planted by assigned farmers (with counts)
    crops_planted = Activity.objects.filter(
        activity_type='planting',
        farmer_id__in=assigned_farmer_ids
    ).values(
        'crop__name'
    ).annotate(
        count=Count('id'),
        total_area=Sum('area_ha')
    ).order_by('-count')[:10]
    
    # Get assigned farmers with most activities
    top_farmers = Activity.objects.filter(
        farmer_id__in=assigned_farmer_ids
    ).values(
        'farmer__username',
        'farmer__region'
    ).annotate(
        activity_count=Count('id')
    ).order_by('-activity_count')[:10]
    
    # Get recent activities from assigned farmers
    recent_activities = Activity.objects.filter(
        farmer_id__in=assigned_farmer_ids
    ).select_related(
        'farmer', 'crop'
    ).order_by('-date')[:10]
    
    # Total expenses from assigned farmers
    total_expenses = Expense.objects.filter(
        farmer_id__in=assigned_farmer_ids
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Forecasts statistics for assigned farmers
    total_forecasts = Forecast.objects.filter(
        farmer_id__in=assigned_farmer_ids
    ).count()
    
    # Upcoming harvests (for notification bell in header) - only for assigned farmers
    # Format similar to context processor for consistency
    today = date.today()
    five_days_from_now = today + timedelta(days=5)
    forecasts = Forecast.objects.filter(
        farmer_id__in=assigned_farmer_ids,
        harvest_start__gte=today,
        harvest_start__lte=five_days_from_now
    ).select_related('crop', 'farmer').order_by('harvest_start')[:10]
    
    upcoming_harvests = []
    for forecast in forecasts:
        days_until = (forecast.harvest_start - today).days
        upcoming_harvests.append({
            'crop': forecast.crop.name if forecast.crop else 'Unknown',
            'harvest_start': forecast.harvest_start,
            'days_until': days_until,
            'forecast': forecast,
        })
    
    context = {
        'farmers': farmers,
        'total_farmers': total_farmers,
        'total_technicians': total_technicians,
        'total_admins': total_admins,
        'total_activities': total_activities,
        'total_plantings': total_plantings,
        'total_crops': total_crops,
        'crops_planted': crops_planted,
        'top_farmers': top_farmers,
        'recent_activities': recent_activities,
        'total_expenses': total_expenses,
        'total_forecasts': total_forecasts,
        'upcoming_harvests': upcoming_harvests,
        'has_upcoming_harvests': len(upcoming_harvests) > 0,
    }
    
    return render(request, 'myApp/admin_dashboard.html', context)


@login_required
def admin_create_user(request):
    """Admin view to create new users"""
    if not request.user.is_admin():
        messages.error(request, "Access denied. Admin only.")
        return redirect("farmer_dashboard")
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" created successfully!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'myApp/admin_create_user.html', {'form': form})


# =====================================================
# 🔧 TECHNICIAN DASHBOARD
# =====================================================

@login_required
def technician_dashboard(request):
    """Technician dashboard with overview of all farmers"""
    if not request.user.is_technician():
        messages.error(request, "Access denied. Technician only.")
        return redirect("farmer_dashboard")
    
    # Get all farmers
    farmers = User.objects.filter(role='farmer').order_by('-date_joined')
    
    # Statistics
    total_farmers = farmers.count()
    total_activities = Activity.objects.count()
    total_plantings = Activity.objects.filter(activity_type='planting').count()
    
    # Upcoming harvests
    upcoming_harvests = Forecast.objects.filter(
        harvest_start__gte=date.today()
    ).order_by('harvest_start')[:10]
    
    # Recent activities across all farmers
    recent_activities = Activity.objects.select_related(
        'farmer', 'crop'
    ).order_by('-date')[:10]
    
    # Total expenses
    total_expenses = Expense.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Active crops (crops with recent plantings)
    active_crops = Activity.objects.filter(
        activity_type='planting',
        date__gte=timezone.now().date() - timedelta(days=90)
    ).values('crop__name').distinct().count()
    
    context = {
        'farmers': farmers,
        'total_farmers': total_farmers,
        'total_activities': total_activities,
        'total_plantings': total_plantings,
        'active_crops': active_crops,
        'upcoming_harvests': upcoming_harvests,
        'recent_activities': recent_activities,
        'total_expenses': total_expenses,
    }
    
    return render(request, 'myApp/technician_dashboard.html', context)


@login_required
def technician_farmers(request):
    """List of all farmers for technicians"""
    if not request.user.is_technician():
        messages.error(request, "Access denied. Technician only.")
        return redirect("farmer_dashboard")
    
    farmers = User.objects.filter(role='farmer').order_by('-date_joined')
    
    # Add statistics for each farmer
    farmers_with_stats = []
    for farmer in farmers:
        activity_count = Activity.objects.filter(farmer=farmer).count()
        active_forecasts = Forecast.objects.filter(farmer=farmer).count()
        last_activity = Activity.objects.filter(farmer=farmer).order_by('-date').first()
        
        farmers_with_stats.append({
            'farmer': farmer,
            'activity_count': activity_count,
            'active_forecasts': active_forecasts,
            'last_activity': last_activity,
        })
    
    context = {
        'farmers_with_stats': farmers_with_stats,
    }
    
    return render(request, 'myApp/technician_farmers.html', context)


@login_required
def technician_farmer_detail(request, farmer_id):
    """Read-only view of a specific farmer's dashboard"""
    if not request.user.is_technician():
        messages.error(request, "Access denied. Technician only.")
        return redirect("farmer_dashboard")
    
    farmer = get_object_or_404(User, id=farmer_id, role='farmer')
    
    # Get farmer's data (same as farmer_dashboard but read-only)
    today = timezone.now().date()
    
    # Reminders
    reminders = Reminder.objects.filter(farmer=farmer, due_date__gte=today).order_by('due_date')[:5]
    
    # Forecasts
    forecasts = Forecast.objects.filter(farmer=farmer).order_by('-forecast_date')[:5]
    
    # Recent activities
    recent_activities = Activity.objects.filter(farmer=farmer).order_by('-date')[:10]
    
    # Recent expenses
    recent_expenses = Expense.objects.filter(farmer=farmer).order_by('-date')[:10]
    
    # Statistics
    total_activities = Activity.objects.filter(farmer=farmer).count()
    total_expenses = Expense.objects.filter(farmer=farmer).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Crops
    crops = Crop.objects.all()
    
    context = {
        'farmer': farmer,
        'reminders': reminders,
        'forecasts': forecasts,
        'recent_activities': recent_activities,
        'recent_expenses': recent_expenses,
        'total_activities': total_activities,
        'total_expenses': total_expenses,
        'crops': crops,
        'is_readonly': True,  # Flag to indicate read-only mode
    }
    
    return render(request, 'myApp/technician_farmer_detail.html', context)


@login_required
def technician_activities(request):
    """View all farmers' activities for technicians"""
    if not request.user.is_technician():
        messages.error(request, "Access denied. Technician only.")
        return redirect("farmer_dashboard")
    
    # Get filter parameters
    farmer_id = request.GET.get('farmer')
    crop_id = request.GET.get('crop')
    activity_type = request.GET.get('activity_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Base query
    activities = Activity.objects.select_related('farmer', 'crop').order_by('-date')
    
    # Apply filters
    if farmer_id:
        activities = activities.filter(farmer_id=farmer_id)
    if crop_id:
        activities = activities.filter(crop_id=crop_id)
    if activity_type:
        activities = activities.filter(activity_type=activity_type)
    if date_from:
        activities = activities.filter(date__gte=date_from)
    if date_to:
        activities = activities.filter(date__lte=date_to)
    
    # Pagination
    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    farmers = User.objects.filter(role='farmer').order_by('username')
    crops = Crop.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'farmers': farmers,
        'crops': crops,
        'current_farmer_id': farmer_id,
        'current_crop_id': crop_id,
        'current_activity_type': activity_type,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'myApp/technician_activities.html', context)


@login_required
def technician_expenses(request):
    """View all farmers' expenses for technicians"""
    if not request.user.is_technician():
        messages.error(request, "Access denied. Technician only.")
        return redirect("farmer_dashboard")
    
    # Get filter parameters
    farmer_id = request.GET.get('farmer')
    crop_id = request.GET.get('crop')
    expense_type = request.GET.get('expense_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Base query
    expenses = Expense.objects.select_related('farmer', 'crop').order_by('-date')
    
    # Apply filters
    if farmer_id:
        expenses = expenses.filter(farmer_id=farmer_id)
    if crop_id:
        expenses = expenses.filter(crop_id=crop_id)
    if expense_type:
        expenses = expenses.filter(expense_type=expense_type)
    if date_from:
        expenses = expenses.filter(date__gte=date_from)
    if date_to:
        expenses = expenses.filter(date__lte=date_to)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(expenses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    expenses_by_type = expenses.values('expense_type').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Get filter options
    farmers = User.objects.filter(role='farmer').order_by('username')
    crops = Crop.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'farmers': farmers,
        'crops': crops,
        'current_farmer_id': farmer_id,
        'current_crop_id': crop_id,
        'current_expense_type': expense_type,
        'date_from': date_from,
        'date_to': date_to,
        'total_expenses': total_expenses,
        'expenses_by_type': expenses_by_type,
    }
    
    return render(request, 'myApp/technician_expenses.html', context)


@login_required
def technician_forecasts(request):
    """View all farmers' forecasts for technicians"""
    if not request.user.is_technician():
        messages.error(request, "Access denied. Technician only.")
        return redirect("farmer_dashboard")
    
    # Get filter parameters
    farmer_id = request.GET.get('farmer')
    crop_id = request.GET.get('crop')
    harvest_date_from = request.GET.get('harvest_date_from')
    harvest_date_to = request.GET.get('harvest_date_to')
    
    # Base query
    forecasts = Forecast.objects.select_related('farmer', 'crop').order_by('harvest_start')
    
    # Apply filters
    if farmer_id:
        forecasts = forecasts.filter(farmer_id=farmer_id)
    if crop_id:
        forecasts = forecasts.filter(crop_id=crop_id)
    if harvest_date_from:
        forecasts = forecasts.filter(harvest_start__gte=harvest_date_from)
    if harvest_date_to:
        forecasts = forecasts.filter(harvest_start__lte=harvest_date_to)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(forecasts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_forecasts = forecasts.count()
    upcoming_count = forecasts.filter(harvest_start__gte=date.today()).count()
    total_expected_yield = forecasts.aggregate(
        total=Sum('expected_yield_kg')
    )['total'] or 0
    
    # Get filter options
    farmers = User.objects.filter(role='farmer').order_by('username')
    crops = Crop.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'farmers': farmers,
        'crops': crops,
        'current_farmer_id': farmer_id,
        'current_crop_id': crop_id,
        'harvest_date_from': harvest_date_from,
        'harvest_date_to': harvest_date_to,
        'total_forecasts': total_forecasts,
        'upcoming_count': upcoming_count,
        'total_expected_yield': total_expected_yield,
    }
    
    return render(request, 'myApp/technician_forecasts.html', context)
