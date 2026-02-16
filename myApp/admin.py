from django.contrib import admin
from .models import (
    User,
    Crop,
    Activity,
    Expense,
    Forecast,
    Reminder,
    Recommendation,
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "role", "region", "is_staff")
    list_filter = ("role", "region")

@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ("name", "ideal_seasons", "yield_t_min", "yield_t_max")
    search_fields = ("name",)

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("farmer", "crop", "activity_type", "date", "area_ha")
    list_filter = ("activity_type", "date")

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("farmer", "crop", "expense_type", "amount", "date")
    list_filter = ("expense_type", "date")

@admin.register(Forecast)
class ForecastAdmin(admin.ModelAdmin):
    list_display = ("farmer", "crop", "expected_yield_kg", "harvest_start", "harvest_end")

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("farmer", "message", "due_date")

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("crop", "region", "month")
