from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomUserCreationForm
from django.db import models


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # or 'farmer_dashboard'
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/register.html', {'form': form})

# put this small helper near the top of views.py (once)
def _as_int(value):
    """
    Convert querystring value to int or return None for '', 'None', 'null', 'undefined', etc.
    """
    if value in (None, "", "None", "none", "null", "undefined"):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None



from django.shortcuts import render
from django.utils import timezone
from .models import Activity, Forecast, Expense, Reminder, Crop
from datetime import datetime

from collections import Counter
from django.db.models import Count

from django.utils import timezone
from django.db import models
from .models import Activity, Forecast, Expense, Reminder, Crop
from django.db.models import Count

def farmer_dashboard(request):
    user = request.user
    today = timezone.now()
    current_month = today.strftime("%B")

    # Crop and expense summary (unchanged)
    crop_count = Activity.objects.filter(
        farmer=user, date__month=today.month
    ).values('crop').distinct().count()

    expenses = Expense.objects.filter(farmer=user)
    total_expenses = expenses.filter(
        date__month=today.month, date__year=today.year
    ).aggregate(total=models.Sum('amount'))['total'] or 0

    most_common_expense = (
        expenses.filter(date__month=today.month, date__year=today.year)
        .values('expense_type')
        .annotate(count=Count('expense_type'))
        .order_by('-count')
        .first()
    )
    most_common_expense_label = (
        dict(Expense.EXPENSE_TYPES).get(most_common_expense['expense_type'])
        if most_common_expense else "—"
    )

    last_recorded_expense = expenses.order_by('-date').first()
    last_recorded_date = last_recorded_expense.date if last_recorded_expense else None

    # Recent activities & reminders (unchanged)
    recent_activities = Activity.objects.filter(farmer=user).order_by('-date')[:5]
    reminders = Reminder.objects.filter(
        farmer=user, due_date__gte=today.date()
    ).order_by('due_date')

    # 🔮 Forecasts (NEW) — prefer upcoming harvests, else show latest 3
    upcoming = Forecast.objects.filter(
        farmer=user,
        harvest_end__isnull=False,
        harvest_end__gte=today.date()
    ).order_by('harvest_start', '-created_at')

    if upcoming.exists():
        forecasts = list(upcoming[:3])
    else:
        # fallback: just show the latest few even if harvest window passed or missing
        forecasts = list(
            Forecast.objects.filter(farmer=user).order_by('-created_at')[:3]
        )

    return render(request, 'myApp/farmer_dashboard.html', {
        'crop_count': crop_count,
        'forecasts': forecasts,             # ⬅️ make sure this matches the template
        'total_expenses': total_expenses,
        'most_common_expense_label': most_common_expense_label,
        'last_recorded_date': last_recorded_date,
        'recent_activities': recent_activities,
        'reminders': reminders,
        'current_month': current_month,
    })


from django.shortcuts import redirect

def role_redirect_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('/admin/')
        elif request.user.role == 'technician':
            return redirect('dashboard')  # or a different view
        else:
            return redirect('farmer_dashboard')
    return redirect('login')



from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import Reminder
from django.utils import timezone

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from .models import Reminder

def add_reminder(request):
    if request.method == "POST":
        message = request.POST.get("message")
        due_date = request.POST.get("due_date")
        if message and due_date:
            Reminder.objects.create(farmer=request.user, message=message, due_date=due_date)

            if request.headers.get('HX-Request'):  # HTMX is calling
                return HttpResponse(status=204)  # Tell HTMX: success, no redirect
            return redirect('farmer_dashboard')  # Normal redirect
    return HttpResponseBadRequest("Invalid form")

def edit_reminder(request):
    if request.method == "POST":
        reminder_id = request.POST.get("reminder_id")
        reminder = Reminder.objects.filter(id=reminder_id, farmer=request.user).first()
        if reminder:
            reminder.message = request.POST.get("message")
            reminder.due_date = request.POST.get("due_date")
            reminder.save()
            if request.headers.get('HX-Request'):
                return HttpResponse(status=204)
            return redirect('farmer_dashboard')
    return HttpResponseBadRequest("Invalid form")

def delete_reminder(request):
    if request.method == "POST":
        reminder_id = request.POST.get("reminder_id")
        Reminder.objects.filter(id=reminder_id, farmer=request.user).delete()
        if request.headers.get('HX-Request'):
            return HttpResponse(status=204)
        return redirect('farmer_dashboard')
    return HttpResponseBadRequest("Invalid request")

def refresh_reminders(request):
    today = timezone.now().date()
    reminders = Reminder.objects.filter(farmer=request.user, due_date__gte=today).order_by('due_date')
    return render(request, 'partials/reminder_list.html', {'reminders': reminders})

from django.shortcuts import render, redirect
from .forms import ActivityForm
from .models import Activity, Crop
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Activity, Crop
from .forms import ActivityForm, CropForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone

from .models import Activity, Crop
from .forms import ActivityForm, CropForm

@login_required
def activity_log_view(request):
    user = request.user
    activities = Activity.objects.filter(farmer=user).order_by('-date')
    crops = Crop.objects.all()

    # --------------------------
    # Filters (crop + date range)
    # --------------------------
    crop_filter = request.GET.get('crop')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if crop_filter:
        activities = activities.filter(crop__id=crop_filter)
    if start_date:
        activities = activities.filter(date__gte=start_date)
    if end_date:
        activities = activities.filter(date__lte=end_date)

    # --------------------------
    # Forms
    # --------------------------
    activity_form = ActivityForm()
    crop_form = CropForm()

    # Helper to parse floats safely from POST
    def _f(name, default=None):
        v = request.POST.get(name, '')
        try:
            return float(v) if v not in (None, '',) else default
        except Exception:
            return default

    # --------------------------
    # POST Actions
    # --------------------------
    if request.method == 'POST':

        # ✅ Add new activity (auto-forecast if planting)
        if 'add_activity' in request.POST:
            activity_form = ActivityForm(request.POST)
            if activity_form.is_valid():
                new_activity = activity_form.save(commit=False)
                new_activity.farmer = user

                # Only for planting entries, capture extra forecasting inputs
                if new_activity.activity_type == 'planting':
                    # Expect these fields in the form/template:
                    # <input name="area_ha">, <input name="seed_qty_kg">,
                    # <input name="fert_sacks">, <input name="spacing">
                    new_activity.area_ha = _f('area_ha', 1.0)
                    new_activity.seed_qty_kg = _f('seed_qty_kg', None)
                    new_activity.fert_sacks = _f('fert_sacks', None)
                    new_activity.spacing = request.POST.get('spacing') or None

                new_activity.save()  # <-- post_save signal in models.py creates/updates Forecast
                messages.success(request, "Activity logged successfully. Forecast generated.")
                return redirect('activity_log')
            else:
                messages.error(request, "Please check the activity form and try again.")

        # ✅ Add new crop
        elif 'add_crop' in request.POST:
            crop_form = CropForm(request.POST)
            if crop_form.is_valid():
                crop_form.save()
                messages.success(request, "New crop added!")
                return redirect('activity_log')
            else:
                messages.error(request, "Please check the crop form and try again.")

        # ✅ Edit existing crop
        elif 'edit_crop' in request.POST:
            crop_id = request.POST.get('crop_id')
            crop = get_object_or_404(Crop, id=crop_id)
            form = CropForm(request.POST, instance=crop)
            if form.is_valid():
                form.save()
                messages.success(request, "Crop updated successfully!")
                return redirect('activity_log')
            else:
                messages.error(request, "Please check the crop form and try again.")

        # ✅ Delete crop
        elif 'delete_crop' in request.POST:
            crop_id = request.POST.get('crop_id')
            Crop.objects.filter(id=crop_id).delete()
            messages.success(request, "Crop deleted.")
            return redirect('activity_log')

    # --------------------------
    # Render
    # --------------------------
    return render(request, 'myApp/activity_log.html', {
        'form': activity_form,
        'crop_form': crop_form,
        'activities': activities,
        'crops': crops,
        'crop_filter': crop_filter,
        'start_date': start_date,
        'end_date': end_date,
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import Expense
from .forms import ExpenseForm
from datetime import datetime
import calendar


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime
import calendar

from .models import Expense
from .forms import ExpenseForm

# views.py (excerpt)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import datetime
import calendar

from .models import Expense
from .forms import ExpenseForm


@login_required
def expense_log_view(request):
    user = request.user
    form = ExpenseForm()

    # Base queryset
    expenses = Expense.objects.filter(farmer=user).order_by('-date')

    # ---- Filters (support month OR year OR both) ----
    month = request.GET.get('month')
    year = request.GET.get('year')
    if year:
        expenses = expenses.filter(date__year=year)
    if month:
        expenses = expenses.filter(date__month=month)

    # ---- POST actions ----
    if request.method == 'POST':
        # Add
        if 'add_expense' in request.POST:
            form = ExpenseForm(request.POST)
            if form.is_valid():
                e = form.save(commit=False)
                e.farmer = user
                e.save()
                messages.success(request, "Expense recorded.")
                return redirect('expense_log')

        # Edit
        elif 'edit_expense' in request.POST:
            expense_id = request.POST.get('expense_id')
            expense = get_object_or_404(Expense, id=expense_id, farmer=user)
            form = ExpenseForm(request.POST, instance=expense)
            if form.is_valid():
                form.save()
                messages.success(request, "Expense updated successfully.")
                return redirect('expense_log')

        # Delete
        elif 'delete_expense' in request.POST:
            expense_id = request.POST.get('expense_id')
            Expense.objects.filter(id=expense_id, farmer=user).delete()
            messages.success(request, "Expense deleted.")
            return redirect('expense_log')

    # ---- Stats based on the *filtered* queryset (drives the cards) ----
    agg = expenses.aggregate(
        total=Sum('amount'),
        avg=Avg('amount'),
        n=Count('id'),
    )
    total = agg['total'] or 0
    avg_expense = agg['avg'] or 0

    # “Most Spent On” = category with largest total amount in the filtered view
    top_cat = (
        expenses.values('expense_type')
        .annotate(total=Sum('amount'))
        .order_by('-total')
        .first()
    )
    if top_cat:
        label_map = dict(Expense.EXPENSE_TYPES)
        most_spent_on = label_map.get(top_cat['expense_type'], top_cat['expense_type'])
        most_spent_amount = float(top_cat['total'] or 0)
    else:
        most_spent_on = None
        most_spent_amount = 0.0

    # ---- Optional: current-month quick summary (if you still show this elsewhere) ----
    today = timezone.now()
    current_month_expenses = Expense.objects.filter(
        farmer=user, date__year=today.year, date__month=today.month
    )
    monthly_total = current_month_expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    most_common = (
        current_month_expenses.values('expense_type')
        .annotate(count=Count('expense_type'))
        .order_by('-count')
        .first()
    )
    most_common_expense = (
        dict(Expense.EXPENSE_TYPES).get(most_common['expense_type'], "N/A")
        if most_common else "N/A"
    )

    last_recorded = expenses.first().date if expenses.exists() else None

    # ---- Month/Year drop-down options ----
    months = [(str(i).zfill(2), calendar.month_name[i]) for i in range(1, 13)]
    current_year = datetime.now().year
    years = [str(y) for y in range(current_year - 2, current_year + 2)]

    return render(request, 'myApp/expense_log.html', {
        'form': form,
        'expenses': expenses,

        # Cards (filtered)
        'total': total,
        'avg_expense': avg_expense,
        'most_spent_on': most_spent_on,
        'most_spent_amount': most_spent_amount,

        # Filters
        'selected_month': month,
        'selected_year': year,
        'months': months,
        'years': years,

        # Optional extras you already used elsewhere
        'monthly_total': monthly_total,
        'most_common_expense': most_common_expense,
        'last_recorded': last_recorded,
    })


from django.http import JsonResponse
from django.db.models.functions import TruncMonth
from django.db.models import Sum

@login_required
def expense_chart_data(request):
    user = request.user

    # Monthly total expenses
    monthly_data = (
        Expense.objects.filter(farmer=user)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    labels = [entry['month'].strftime('%B %Y') for entry in monthly_data]
    data = [float(entry['total']) for entry in monthly_data]

    return JsonResponse({'labels': labels, 'data': data})



import csv
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from io import BytesIO

@login_required
def export_expenses_csv(request):
    user = request.user
    month = _as_int(request.GET.get('month'))
    year = _as_int(request.GET.get('year'))

    expenses = Expense.objects.filter(farmer=user)
    if month is not None:
        expenses = expenses.filter(date__month=month)
    if year is not None:
        expenses = expenses.filter(date__year=year)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Description', 'Amount'])
    for e in expenses:
        writer.writerow([e.date, e.get_expense_type_display(), e.description, e.amount])

    return response


@login_required
def export_expenses_pdf(request):
    user = request.user
    month = _as_int(request.GET.get('month'))
    year = _as_int(request.GET.get('year'))

    expenses = Expense.objects.filter(farmer=user)
    if month is not None:
        expenses = expenses.filter(date__month=month)
    if year is not None:
        expenses = expenses.filter(date__year=year)

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica", 12)
    p.drawString(100, 800, "Expense Report")

    y = 770
    for e in expenses:
        line = f"{e.date} - {e.get_expense_type_display()} - {e.description} - ₱{e.amount}"
        p.drawString(50, y, line)
        y -= 20
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 12)
            y = 800

    p.showPage()
    p.save()
    buffer.seek(0)

    resp = HttpResponse(buffer, content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="expenses.pdf"'
    return resp


# myApp/views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Max
from django.db.models.functions import TruncMonth
from django.utils import timezone
from .models import Expense, Forecast, Activity, Crop
from django.db import models
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone
from .models import Expense, Forecast, Crop
from django.db import models

@login_required
def expenses_by_category(request):
    user = request.user
    qs = (Expense.objects
          .filter(farmer=user)
          .values('expense_type')
          .annotate(total=Sum('amount'))
          .order_by('-total'))
    labels = [dict(Expense.EXPENSE_TYPES).get(x['expense_type'], x['expense_type']) for x in qs]
    data = [float(x['total']) for x in qs]
    return JsonResponse({"labels": labels, "data": data})

@login_required
def yield_by_crop(request):
    user = request.user
    # latest forecast per crop
    by_crop = {}
    for c in Crop.objects.all():
        f = (Forecast.objects
             .filter(farmer=user, crop=c)
             .order_by('-created_at')
             .first())
        if f:
            by_crop[c.name] = by_crop.get(c.name, 0.0) + (f.expected_yield_kg or 0.0)
    labels = list(by_crop.keys())
    data = [round(v, 2) for v in by_crop.values()]
    return JsonResponse({"labels": labels, "data": data})

@login_required
def harvest_timeline(request):
    """
    Return labels (crop names) + offsets/windows (days).
    UI renders scrollable chips (no big chart).
    """
    user = request.user
    today = timezone.now().date()
    rows = (Forecast.objects
            .filter(farmer=user, harvest_start__isnull=False, harvest_end__isnull=False)
            .order_by('harvest_start', 'crop__name')
            .select_related('crop'))

    labels, offsets, windows = [], [], []
    seen = set()
    for f in rows:
        if f.crop_id in seen:  # one upcoming per crop
            continue
        seen.add(f.crop_id)
        if f.harvest_end < today:
            continue
        start = f.harvest_start
        end = f.harvest_end
        labels.append(f.crop.name)
        offsets.append(max((start - today).days, 0))
        windows.append(max((end - start).days, 0))

    return JsonResponse({"labels": labels, "offsets": offsets, "windows": windows})


@login_required
def activities_month_counts(request):
    user = request.user
    now = timezone.now()
    month_start = now.replace(day=1).date()
    qs = (Activity.objects
          .filter(farmer=user, date__gte=month_start, date__lte=now.date())
          .values('activity_type')
          .annotate(n=models.Count('id'))
          .order_by('activity_type'))
    # map code -> label
    labels_map = dict(Activity.ACTIVITY_TYPES)
    labels = [labels_map.get(x['activity_type'], x['activity_type']) for x in qs]
    data = [x['n'] for x in qs]
    return JsonResponse({"labels": labels, "data": data})


# --- Add near your other imports ---
from django.http import JsonResponse
from django.db.models.functions import TruncMonth
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from datetime import datetime
import csv
from io import BytesIO
from reportlab.pdfgen import canvas

# Helper to optionally filter by date range
def _date_range(qs, request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)
    return qs

@login_required
def chart_activities_monthly(request):
    qs = Activity.objects.filter(farmer=request.user)
    qs = _date_range(qs, request)
    monthly = (qs.annotate(m=TruncMonth('date'))
                 .values('m')
                 .annotate(c=Count('id'))
                 .order_by('m'))
    labels = [x['m'].strftime('%b %Y') for x in monthly]
    data = [x['c'] for x in monthly]
    return JsonResponse({'labels': labels, 'data': data})

@login_required
def chart_activities_by_type(request):
    qs = Activity.objects.filter(farmer=request.user)
    qs = _date_range(qs, request)
    agg = (qs.values('activity_type')
             .annotate(c=Count('id'))
             .order_by())
    # Use display names
    type_map = dict(Activity.ACTIVITY_TYPES)
    labels = [type_map.get(x['activity_type'], x['activity_type']).title() for x in agg]
    data = [x['c'] for x in agg]
    return JsonResponse({'labels': labels, 'data': data})

@login_required
def chart_activities_by_crop(request):
    qs = Activity.objects.filter(farmer=request.user)
    qs = _date_range(qs, request)
    agg = (qs.values('crop__name')
             .annotate(c=Count('id'))
             .order_by('-c', 'crop__name'))[:8]  # cap to 8 for compact bar
    labels = [x['crop__name'] for x in agg]
    data = [x['c'] for x in agg]
    return JsonResponse({'labels': labels, 'data': data})

# --------- Exports ----------
@login_required
def export_activities_csv(request):
    qs = Activity.objects.filter(farmer=request.user).select_related('crop')
    qs = _date_range(qs, request)

    resp = HttpResponse(content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename="activities.csv"'
    w = csv.writer(resp)
    w.writerow(['Date', 'Crop', 'Type', 'Notes', 'Area(ha)', 'Seed(kg)', 'Fert(sacks)', 'Spacing'])
    for a in qs.order_by('-date'):
        w.writerow([
            a.date, a.crop.name, a.activity_type, a.notes or '',
            a.area_ha if a.activity_type=='planting' else '',
            a.seed_qty_kg if a.activity_type=='planting' else '',
            a.fert_sacks if a.activity_type=='planting' else '',
            a.spacing if a.activity_type=='planting' else '',
        ])
    return resp

@login_required
def export_activities_pdf(request):
    qs = Activity.objects.filter(farmer=request.user).select_related('crop')
    qs = _date_range(qs, request)

    buf = BytesIO()
    p = canvas.Canvas(buf)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 800, "Activity Report")
    p.setFont("Helvetica", 10)

    y = 780
    for a in qs.order_by('-date'):
        line = f"{a.date}  |  {a.crop.name}  |  {a.activity_type}"
        if a.activity_type == 'planting':
            line += f"  |  area {a.area_ha or ''} ha, seed {a.seed_qty_kg or ''} kg, fert {a.fert_sacks or ''}, spacing {a.spacing or ''}"
        if a.notes:
            line += f"  |  {a.notes[:70]}"
        p.drawString(50, y, line)
        y -= 16
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 10)
            y = 800

    p.showPage()
    p.save()
    buf.seek(0)
    return HttpResponse(buf, content_type='application/pdf')


# views_charts.py (or inside your existing views.py)
# views_charts.py  (or your views.py)

from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
import calendar

from .models import Expense

@login_required
def chart_expenses_monthly(request):
    """12 months for the selected or current year, filtered to this farmer."""
    user = request.user
    year = int(request.GET.get('year', timezone.now().year))

    qs = (
        Expense.objects
        .filter(farmer=user, date__year=year)
        .values('date__month')
        .annotate(total=Sum('amount'))
    )
    totals_by_month = {row['date__month']: float(row['total'] or 0) for row in qs}

    labels = [calendar.month_abbr[m] for m in range(1, 13)]
    data = [totals_by_month.get(m, 0) for m in range(1, 13)]
    return JsonResponse({"labels": labels, "data": data})

@login_required
def chart_expenses_by_category(request):
    """Sum by expense_type for the current month (or ?month=&year=)."""
    user = request.user
    now = timezone.now()
    month = int(request.GET.get('month', now.month))
    year = int(request.GET.get('year', now.year))

    qs = (
        Expense.objects
        .filter(farmer=user, date__year=year, date__month=month)
        .values('expense_type')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    type_map = dict(Expense.EXPENSE_TYPES)
    labels = [type_map.get(row['expense_type'], row['expense_type']) for row in qs]
    data = [float(row['total'] or 0) for row in qs]
    return JsonResponse({"labels": labels, "data": data})
