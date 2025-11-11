from django.urls import path, reverse_lazy
from django.contrib.auth.views import (
    LoginView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from . import views

urlpatterns = [
    path('login/', LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.farmer_dashboard, name='farmer_dashboard'),
    path('', views.role_redirect_view, name='home'),
    path('messages/flash/', views.flash_messages, name='flash_messages'),
    path('password-reset/', PasswordResetView.as_view(
        template_name='auth/password_reset.html',
        email_template_name='auth/password_reset_email.txt',
        success_url=reverse_lazy('password_reset_done')
    ), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete')
    ), name='password_reset_confirm'),
    path('password-reset/complete/', PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'
    ), name='password_reset_complete'),

    path('reminders/add/', views.add_reminder, name='add_reminder'),
    path('reminders/edit/', views.edit_reminder, name='edit_reminder'),
    path('reminders/delete/', views.delete_reminder, name='delete_reminder'),
    path('reminders/refresh/', views.refresh_reminders, name='refresh_reminders'),

    path('activities/', views.activity_log_view, name='activity_log'),
    path('activities/<int:pk>/detail/', views.planting_detail_view, name='planting_detail'),
    path('expenses/', views.expense_log_view, name='expense_log'),
    path('expenses/chart/data/', views.chart_expenses_monthly, name='expense_chart_data'),

    path('expenses/export/csv/', views.export_expenses_csv, name='export_expenses_csv'),
    path('expenses/export/pdf/', views.export_expenses_pdf, name='export_expenses_pdf'),

      path("api/charts/expenses/monthly/", views.chart_expenses_monthly, name="chart_expenses_monthly"),
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
