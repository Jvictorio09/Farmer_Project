# 👥 Role-Based Access Documentation

## Overview

Agrilog+ has three user roles with different access levels and views. This document explains what each role can see and do in the system.

---

## 🔐 Admin Role

### Access Level
**Full system administration** with complete control over all data and users.

### What Admin Sees

#### 1. **Django Admin Panel** (`/admin/`)
When an admin logs in, they are automatically redirected to Django's admin interface.

**Available Models:**
- ✅ **Users** - View, create, edit, delete all users
  - Filter by: role, region
  - See: username, role, region, staff status
- ✅ **Crops** - Manage all crop definitions
  - Search by: crop name
  - See: name, ideal seasons, yield ranges
- ✅ **Activities** - View all farmer activities
  - Filter by: activity type, date
  - See: farmer, crop, activity type, date, area
- ✅ **Expenses** - View all expenses
  - Filter by: expense type, date
  - See: farmer, crop, expense type, amount, date
- ✅ **Forecasts** - View all yield forecasts
  - See: farmer, crop, expected yield, harvest dates
- ✅ **Reminders** - View all reminders
  - See: farmer, message, due date
- ✅ **Recommendations** - Manage crop recommendations
  - See: crop, region, month

#### 2. **Full CRUD Operations**
- Create, read, update, delete any record
- Manage user accounts and permissions
- Modify crop definitions
- View all farmer data across the system

#### 3. **System Configuration**
- Access to Django admin settings
- Can modify any system data
- No restrictions on data access

### Navigation
- **Login Redirect:** `/admin/` (Django admin panel)
- **Can Access:** All admin features, but typically stays in admin panel

### Demo Account
- **Username:** `admin`
- **Password:** `demo12345`
- **Access:** Full Django admin panel

---

## 🔧 Technician Role

### Access Level
**Read-only access** to farmer data with ability to view dashboards and monitor farmer activities.

### What Technician Sees

#### 1. **Farmer Dashboard** (Same as farmers)
Technicians are redirected to the same `farmer_dashboard` that farmers use, but with a **"Technician mode"** banner.

**Dashboard Features:**
- ✅ **Next Harvest** - View upcoming harvests
- ✅ **Forecast Snapshot** - See all forecasts
- ✅ **Expenses by Crop** - View expense breakdowns
- ✅ **Crop Cost Efficiency** - See cost per kg calculations
- ✅ **Recent Activities** - View latest activities
- ✅ **Reminders** - View and manage reminders
- ✅ **Recommended Crops** - See crop recommendations

**Note:** Currently, technicians see their own dashboard (which would be empty since they're not farmers). The system is designed for technicians to view farmer data, but the implementation needs to be completed.

#### 2. **Activity Log** (`/activities/`)
- ✅ Can view activity logs
- ✅ Can see all activities (currently shows technician's own activities)
- ✅ Can manage crops (add, edit, delete)

#### 3. **Expense Log** (`/expenses/`)
- ✅ Can view expense records
- ✅ Can see expense history
- ✅ Can filter and export expenses

#### 4. **Navigation Bar**
- Dashboard link
- Activities link
- Expenses link
- Logout button
- **Technician Mode Banner** - Green banner at bottom of header indicating technician mode

### Current Limitations
⚠️ **Important:** The technician role currently:
- Uses the same dashboard as farmers
- Sees their own (empty) data instead of farmer data
- Has a `technician_home.html` template but no view to render it
- Cannot view other farmers' data (needs implementation)

### Intended Functionality (Based on Template)
The `technician_home.html` template suggests technicians should see:
- **Latest Forecast Updates** - Recent forecasts from all farmers
- **Farmers to Check In With** - List of assigned farmers
- Links to access individual farmer dashboards

### Navigation
- **Login Redirect:** `/dashboard/` (Farmer dashboard)
- **Header Banner:** "Technician mode · farmer dashboards stay unchanged"
- **Can Access:** Dashboard, Activities, Expenses (same navigation as farmers)

### Demo Account
- **Username:** `tech_ana`
- **Password:** `demo12345`
- **Access:** Farmer dashboard with technician mode banner

---

## 🌾 Farmer Role

### Access Level
**Full access** to their own farm data with ability to log activities, track expenses, and view forecasts.

### What Farmer Sees

#### 1. **Farmer Dashboard** (`/dashboard/`)

**Key Sections:**

##### **Next Harvest**
- Shows the next upcoming harvest
- Displays expected yield in kg
- Shows harvest date range

##### **Forecast Snapshot**
- List of all crop forecasts
- Shows crop name, expected yield, harvest dates
- Organized by harvest start date

##### **Expenses by Crop**
- Breakdown of expenses per crop
- Total expenses per crop
- Individual expense items

##### **Crop Cost Efficiency**
- Cost per kg calculation
- Total expense vs expected yield
- Helps farmers understand profitability

##### **Recent Activities**
- Last 5 activities logged
- Shows activity type, crop, date

##### **Reminders**
- Upcoming reminders
- Can add, edit, delete reminders
- Shows due dates

##### **Recommended Crops**
- Crops recommended for current season
- Based on region and month
- Shows yield expectations

#### 2. **Activity Log** (`/activities/`)

**Features:**
- ✅ **Quick Log Form** - Fast activity entry
- ✅ **Activity History** - All past activities
- ✅ **Crop Management** - Add, edit, delete crops
- ✅ **Activity Types:**
  - Planting (auto-generates forecast)
  - Watering
  - Harvesting
- ✅ **Export Options:**
  - Export to CSV
  - Export to PDF
- ✅ **Charts:**
  - Activities by type
  - Monthly activities
  - Activities by crop

#### 3. **Expense Log** (`/expenses/`)

**Features:**
- ✅ **Add Expenses** - Log new expenses
- ✅ **Expense History** - All past expenses
- ✅ **Expense Types:**
  - Seed
  - Fertilizer
  - Labor
  - Pesticide
  - Fuel
  - Other
- ✅ **Crop Association** - Link expenses to crops
- ✅ **Filtering** - Filter by month/year
- ✅ **Charts:**
  - Monthly expenses
  - Expenses by category
  - Expenses by crop
- ✅ **Export Options:**
  - Export to CSV
  - Export to PDF

#### 4. **Harvest Reminder Notification**
- ✅ **Notification Bell** - Appears in navbar when harvest is within 5 days
- ✅ **Dropdown Panel** - Shows harvest details
- ✅ **Status Badges** - Today, Tomorrow, Soon, Upcoming
- ✅ **Harvest Information:**
  - Crop name
  - Harvest date
  - Days remaining
  - Expected yield

### Navigation
- **Login Redirect:** `/dashboard/` (Farmer dashboard)
- **Navigation Links:**
  - Dashboard
  - Activities
  - Expenses
  - Notification Bell (if harvests upcoming)
  - Logout

### Data Access
- ✅ Can only see their own data
- ✅ Cannot view other farmers' information
- ✅ Can create, edit, delete their own records
- ✅ Automatic forecast generation when planting activities are logged

### Demo Accounts
- **farmer_ben** / `demo12345` - Sample data (Ilocos Norte)
- **farmer_rosa** / `demo12345` - Sample data (Bukidnon)
- **farmer_carlos** / `demo12345` - Has upcoming harvest reminder (Laguna)

---

## 🔄 Role Routing Logic

### Login Flow (`role_redirect_view`)

```python
if user.role == "admin":
    → Redirect to /admin/ (Django admin panel)
else:
    → Redirect to /dashboard/ (Farmer dashboard)
```

**Current Behavior:**
- **Admin:** Goes to Django admin
- **Technician:** Goes to farmer dashboard (with technician banner)
- **Farmer:** Goes to farmer dashboard

---

## 📊 Data Visibility Matrix

| Feature | Admin | Technician | Farmer |
|---------|-------|------------|--------|
| **Django Admin** | ✅ Full Access | ❌ No Access | ❌ No Access |
| **Farmer Dashboard** | ❌ (Uses Admin) | ✅ (Own Data) | ✅ (Own Data) |
| **Activity Log** | ❌ (Uses Admin) | ✅ (Own Data) | ✅ (Own Data) |
| **Expense Log** | ❌ (Uses Admin) | ✅ (Own Data) | ✅ (Own Data) |
| **View All Users** | ✅ Yes | ❌ No | ❌ No |
| **View All Crops** | ✅ Yes | ✅ Yes | ✅ Yes |
| **View All Activities** | ✅ Yes | ❌ (Own Only) | ❌ (Own Only) |
| **View All Expenses** | ✅ Yes | ❌ (Own Only) | ❌ (Own Only) |
| **Create/Edit Crops** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Manage Users** | ✅ Yes | ❌ No | ❌ No |
| **Harvest Reminders** | ❌ (Uses Admin) | ❌ (No Data) | ✅ Yes |

---

## 🚧 Current Implementation Status

### ✅ Fully Implemented
- Admin role with Django admin access
- Farmer role with full dashboard functionality
- Role-based routing
- Technician mode banner

### ⚠️ Partially Implemented
- Technician role (has template but no dedicated view)
- Technician viewing farmer data (not implemented)

### 📝 Recommended Improvements

#### For Technician Role:
1. **Create Technician Dashboard View**
   - Show all farmers' forecasts
   - List assigned farmers
   - Aggregate statistics

2. **Farmer Data Access**
   - Allow technicians to view specific farmer dashboards
   - Filter activities/expenses by farmer
   - View all farmers' data in one place

3. **Technician-Specific Features**
   - Assign farmers to technicians
   - Notes/comments on farmer data
   - Activity approval workflow

#### For Admin Role:
1. **Custom Admin Dashboard** (Optional)
   - System-wide statistics
   - User management interface
   - Data export tools

---

## 🔍 How to Test Each Role

### Test Admin
```bash
# Login as admin
Username: admin
Password: demo12345

# You'll be redirected to /admin/
# Can access all models and manage everything
```

### Test Technician
```bash
# Login as technician
Username: tech_ana
Password: demo12345

# You'll be redirected to /dashboard/
# See technician mode banner
# Currently sees empty dashboard (no farmer data)
```

### Test Farmer
```bash
# Login as farmer
Username: farmer_ben
Password: demo12345

# You'll be redirected to /dashboard/
# See full dashboard with sample data
# Can log activities, track expenses
# See harvest reminders if applicable
```

---

## 📁 Related Files

| File | Purpose |
|------|---------|
| `myApp/models.py` | User model with role field |
| `myApp/views.py` | Role routing and dashboard views |
| `myApp/admin.py` | Django admin configuration |
| `myApp/templates/includes/header.html` | Technician mode banner |
| `myApp/templates/myApp/farmer_dashboard.html` | Farmer dashboard template |
| `myApp/templates/myApp/technician_home.html` | Technician template (not used) |

---

**Last Updated:** February 2026  
**Version:** 1.0

