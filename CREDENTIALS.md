# 🔐 Demo Account Credentials

## Overview

This document contains all demo account credentials for the Agrilog+ Farmer Project. These accounts are created when you run the seed script and are intended for **development and testing purposes only**.

---

## ⚠️ Security Warning

**DO NOT use these credentials in production!** These are demo accounts with weak passwords. Always use strong, unique passwords for production environments.

---

## Default Password

**All demo accounts use the same password:**
```
demo12345
```

---

## Demo Accounts

### 1. Admin Account

| Field | Value |
|-------|-------|
| **Username** | `admin` |
| **Password** | `demo12345` |
| **Email** | `admin@Agriplus.demo` |
| **Role** | `admin` |
| **Access** | Full system access + Django admin panel |
| **Staff Status** | ✅ Yes |

**Use Case:**
- Access Django admin panel at `/admin/`
- Full system administration
- Manage all users, crops, and data

---

### 2. Technician Account

| Field | Value |
|-------|-------|
| **Username** | `tech_ana` |
| **Password** | `demo12345` |
| **Email** | `tech@Agriplus.demo` |
| **Role** | `technician` |
| **First Name** | `Ana` |
| **Access** | Technician dashboard (can view farmer data) |

**Use Case:**
- View farmer dashboards
- Access technician-specific features
- Monitor farmer activities

---

### 3. Farmer Account - Ben

| Field | Value |
|-------|-------|
| **Username** | `farmer_ben` |
| **Password** | `demo12345` |
| **Email** | `ben@Agriplus.demo` |
| **Role** | `farmer` |
| **First Name** | `Ben` |
| **Region** | `Ilocos Norte` |
| **Access** | Farmer dashboard with sample data |

**Sample Data:**
- Activities from December 2025 - January 2026
- Expenses and forecasts
- Reminders
- Multiple crops (Rice, Corn, Mango)

---

### 4. Farmer Account - Rosa

| Field | Value |
|-------|-------|
| **Username** | `farmer_rosa` |
| **Password** | `demo12345` |
| **Email** | `rosa@Agriplus.demo` |
| **Role** | `farmer` |
| **First Name** | `Rosa` |
| **Region** | `Bukidnon` |
| **Access** | Farmer dashboard with sample data |

**Sample Data:**
- Activities from December 2025 - January 2026
- Expenses and forecasts
- Reminders
- Multiple crops (Rice, Corn, Mango)

---

### 5. Farmer Account - Carlos ⭐

| Field | Value |
|-------|-------|
| **Username** | `farmer_carlos` |
| **Password** | `demo12345` |
| **Email** | `carlos@Agriplus.demo` |
| **Role** | `farmer` |
| **First Name** | `Carlos` |
| **Region** | `Laguna` |
| **Access** | Farmer dashboard with **upcoming harvest** |

**Special Feature:**
- ✅ **Has harvest reminder notification!**
- Vegetables harvest scheduled for **February 18, 2026**
- Perfect for testing the harvest reminder system
- Shows notification bell in navbar when harvest is within 5 days

**Sample Data:**
- Planting activity: December 10, 2025 (Vegetables)
- Harvest start: February 18, 2026 (2 days from Feb 16, 2026)
- Watering activities throughout growing period

---

## Quick Reference Table

| Username | Password | Role | Special Features |
|----------|----------|------|------------------|
| `admin` | `demo12345` | Admin | Django admin access |
| `tech_ana` | `demo12345` | Technician | View farmer data |
| `farmer_ben` | `demo12345` | Farmer | Sample data (Ilocos Norte) |
| `farmer_rosa` | `demo12345` | Farmer | Sample data (Bukidnon) |
| `farmer_carlos` | `demo12345` | Farmer | **Upcoming harvest reminder** |

---

## Creating Demo Accounts

### Method 1: Seed Script (Recommended)

Run the seed script to create all demo accounts with sample data:

```bash
python seed_demo.py
```

**What it creates:**
- ✅ All 5 demo accounts
- ✅ Crop data
- ✅ Sample activities
- ✅ Sample expenses
- ✅ Forecasts (with harvest dates)
- ✅ Reminders
- ✅ Recommendations

### Method 2: Reset Passwords Only

If accounts already exist but passwords need resetting:

```bash
python reset_demo_passwords.py
```

**Note:** This script currently only resets passwords for 4 users (admin, tech_ana, farmer_ben, farmer_rosa). To include farmer_carlos, update the script.

---

## Login URL

All accounts can log in at:
```
http://localhost:8000/login/
```

Or your deployed URL:
```
https://your-domain.com/login/
```

---

## Role-Based Access

### Admin (`admin`)
- ✅ Access to Django admin panel (`/admin/`)
- ✅ Can manage all users, crops, and system data
- ✅ Full CRUD operations on all models

### Technician (`tech_ana`)
- ✅ Access to technician dashboard
- ✅ Can view farmer data
- ✅ Cannot modify farmer data
- ❌ No Django admin access

### Farmers (`farmer_ben`, `farmer_rosa`, `farmer_carlos`)
- ✅ Access to farmer dashboard
- ✅ Log activities (planting, watering, harvesting)
- ✅ Track expenses
- ✅ View forecasts and harvest reminders
- ✅ Manage reminders
- ❌ No Django admin access
- ❌ Cannot view other farmers' data

---

## Testing Scenarios

### Test Harvest Reminder System
1. Login as: `farmer_carlos` / `demo12345`
2. Navigate to any page
3. Look for notification bell in navbar (if today is Feb 16-21, 2026)
4. Click bell to see harvest details

### Test Admin Features
1. Login as: `admin` / `demo12345`
2. Navigate to: `/admin/`
3. Access Django admin panel

### Test Technician Features
1. Login as: `tech_ana` / `demo12345`
2. View technician dashboard
3. Access farmer data views

### Test Farmer Features
1. Login as: `farmer_ben` / `demo12345`
2. View dashboard with sample data
3. Log new activities
4. Track expenses

---

## Updating Passwords

### Change Password via Django Admin
1. Login as `admin`
2. Go to `/admin/`
3. Navigate to Users
4. Select user and change password

### Change Password via Code
Edit `seed_demo.py` line 58:
```python
user.set_password("your_new_password")
```

Then run:
```bash
python seed_demo.py
```

### Change Password via Django Shell
```python
python manage.py shell
>>> from myApp.models import User
>>> user = User.objects.get(username='admin')
>>> user.set_password('new_password')
>>> user.save()
```

---

## Account Status

All demo accounts are created with:
- ✅ `is_active = True` (can log in)
- ✅ `is_staff = True` (only for admin)
- ✅ Email addresses (for password reset functionality)

---

## Troubleshooting

### Can't log in?
1. **Verify account exists:**
   ```bash
   python manage.py shell
   >>> from myApp.models import User
   >>> User.objects.filter(username='admin').exists()
   ```

2. **Reset password:**
   ```bash
   python reset_demo_passwords.py
   ```

3. **Recreate accounts:**
   ```bash
   python seed_demo.py
   ```

### Account not showing in admin?
- Only `admin` account has `is_staff = True`
- Other accounts cannot access `/admin/` (by design)

### Missing farmer_carlos?
- Run `seed_demo.py` to create all accounts
- Check `seed_demo.py` line 42 for farmer_carlos definition

---

## Security Best Practices

### For Development:
- ✅ Use demo accounts for testing
- ✅ Keep passwords simple for easy access
- ✅ Document credentials (this file)

### For Production:
- ❌ **DO NOT** use these demo accounts
- ❌ **DO NOT** use weak passwords
- ✅ Create strong, unique passwords
- ✅ Use environment variables for sensitive data
- ✅ Enable two-factor authentication
- ✅ Regularly rotate passwords
- ✅ Use Django's password validators

---

## Files Reference

| File | Purpose |
|------|---------|
| `seed_demo.py` | Creates all demo accounts and sample data |
| `reset_demo_passwords.py` | Resets passwords for existing demo accounts |
| `myApp/models.py` | User model definition |
| `myProject/settings.py` | Authentication settings |

---

## Quick Login Commands

Copy-paste ready login credentials:

```bash
# Admin
Username: admin
Password: demo12345

# Technician
Username: tech_ana
Password: demo12345

# Farmer Ben
Username: farmer_ben
Password: demo12345

# Farmer Rosa
Username: farmer_rosa
Password: demo12345

# Farmer Carlos (with harvest reminder)
Username: farmer_carlos
Password: demo12345
```

---

**Last Updated:** February 2026  
**Version:** 1.0  
**Environment:** Development/Testing Only

