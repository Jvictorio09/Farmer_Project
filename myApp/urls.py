from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path('login/', LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.farmer_dashboard, name='farmer_dashboard'),
    path('', views.role_redirect_view, name='home'),

    path('reminders/add/', views.add_reminder, name='add_reminder'),
    path('reminders/edit/', views.edit_reminder, name='edit_reminder'),
    path('reminders/delete/', views.delete_reminder, name='delete_reminder'),
    path('reminders/refresh/', views.refresh_reminders, name='refresh_reminders'),

    path('activities/', views.activity_log_view, name='activity_log'),
    path('expenses/', views.expense_log_view, name='expense_log'),
    path('expenses/chart/data/', views.expense_chart_data, name='expense_chart_data'),

    path('expenses/export/csv/', views.export_expenses_csv, name='export_expenses_csv'),
    path('expenses/export/pdf/', views.export_expenses_pdf, name='export_expenses_pdf'),

      path("api/charts/expenses/monthly/", views.expense_chart_data, name="chart_expenses_monthly"),
    path("api/charts/expenses/by-category/", views.expenses_by_category, name="chart_expenses_by_category"),
    path("api/charts/yield/by-crop/", views.yield_by_crop, name="chart_yield_by_crop"),
    path("api/charts/harvest/timeline/", views.harvest_timeline, name="chart_harvest_timeline"),

     path('charts/activities/monthly/', views.chart_activities_monthly, name='chart_activities_monthly'),
    path('charts/activities/type/', views.chart_activities_by_type, name='chart_activities_by_type'),
    path('charts/activities/crop/', views.chart_activities_by_crop, name='chart_activities_by_crop'),

    path('export/activities.csv', views.export_activities_csv, name='export_activities_csv'),
    path('export/activities.pdf', views.export_activities_pdf, name='export_activities_pdf'),


    path("charts/expenses-monthly/", views.chart_expenses_monthly, name="chart_expenses_monthly"),
    path("charts/expenses-by-category/", views.chart_expenses_by_category, name="chart_expenses_by_category"),
]
