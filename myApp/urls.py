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

    # AUTH
    path('login/', LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('', views.role_redirect_view, name='home'),

    # DASHBOARD
    path('dashboard/', views.farmer_dashboard, name='farmer_dashboard'),

    # 👇 INSERT MO DITO
    path('messages/flash/', views.flash_messages, name='flash_messages'),

    # PASSWORD RESET
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

    # ACTIVITIES
    path('activities/', views.activity_log_view, name='activity_log'),
    path('activities/<int:pk>/detail/', views.planting_detail_view, name='planting_detail'),

    # EXPORT ACTIVITIES
    path('activities/export/csv/', views.export_activities_csv, name='export_activities_csv'),
    path('activities/export/pdf/', views.export_activities_pdf, name='export_activities_pdf'),
    
    # ACTIVITY CHARTS
    path('charts/activities/monthly/', views.chart_activities_monthly, name='chart_activities_monthly'),
    path('charts/activities/by-type/', views.chart_activities_by_type, name='chart_activities_by_type'),
    path('charts/activities/by-crop/', views.chart_activities_by_crop, name='chart_activities_by_crop'),
    
    # EXPENSES
    path('expenses/', views.expense_log_view, name='expense_log'),
    path('charts/expenses/by-crop/', views.chart_expenses_by_crop, name='chart_expenses_by_crop'),
 
    # REMINDERS
    path('reminders/add/', views.add_reminder, name='add_reminder'),
    path('reminders/delete/', views.delete_reminder, name='delete_reminder'),
    path('reminders/update/', views.update_reminder, name='update_reminder'),
    
    # ACTIVITY UPDATE/DELETE
    path('activities/<int:pk>/update/', views.update_activity, name='update_activity'),
    path('activities/<int:pk>/delete/', views.delete_activity, name='delete_activity'),
    
    # EXPENSE UPDATE/DELETE
    path('expenses/<int:pk>/update/', views.update_expense, name='update_expense'),
    path('expenses/<int:pk>/delete/', views.delete_expense, name='delete_expense'),
    
    # CROP UPDATE/DELETE
    path('crops/<int:pk>/update/', views.update_crop, name='update_crop'),
    path('crops/<int:pk>/delete/', views.delete_crop, name='delete_crop'),

]
