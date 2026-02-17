from django.contrib import admin
from django.urls import path, include
from myApp import views

urlpatterns = [
    # Admin dashboard routes (must come before Django admin to avoid conflicts)
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/create-user/', views.admin_create_user, name='admin_create_user'),
    
    # Django admin (must come after custom admin routes)
    path('admin/', admin.site.urls),
    
    # App URLs
    path('', include("myApp.urls")),
]
