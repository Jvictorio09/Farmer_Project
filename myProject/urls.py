from django.contrib import admin
from django.urls import path, include
from myApp import views

urlpatterns = [
    # Admin dashboard routes (must come before Django admin to avoid conflicts)
    path('super-admin/dashboard/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/create-user/', views.admin_create_user, name='admin_create_user'),
    path(
        'admin/users/<int:user_id>/approve/',
        views.approve_user_registration,
        name='approve_user_registration',
    ),
    path(
        'admin/users/<int:user_id>/reject/',
        views.reject_user_registration,
        name='reject_user_registration',
    ),
    
    # Django admin (must come after custom admin routes)
    path('admin/', admin.site.urls),
    
    # App URLs
    path('', include("myApp.urls")),
]
