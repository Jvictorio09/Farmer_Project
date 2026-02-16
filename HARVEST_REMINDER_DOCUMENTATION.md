# 🌾 Harvest Reminder System Documentation

## Overview

The Harvest Reminder System automatically notifies farmers when their crops are approaching harvest time. The system displays a notification bell icon in the navigation bar that shows upcoming harvests within the next 5 days.

---

## How It Works

### 1. **Forecast Generation (Automatic)**

When a farmer logs a **planting activity**, the system automatically creates a `Forecast` record:

**Location:** `myApp/models.py` (lines 206-226)

```python
@receiver(post_save, sender=Activity)
def generate_forecast(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.activity_type != 'planting':
        return
    
    data = compute_forecast(instance)
    Forecast.objects.create(...)
```

**Process:**
1. When a planting activity is saved, Django's signal handler triggers
2. The `compute_forecast()` function calculates:
   - Expected yield based on crop type, area, and inputs
   - **Harvest start date** = planting date + crop's `days_to_harvest_min`
   - **Harvest end date** = planting date + crop's `days_to_harvest_max`

**Example:**
- **Planting Date:** December 10, 2025
- **Crop:** Vegetables (70 days to harvest minimum)
- **Harvest Start:** February 18, 2026 (70 days later)

---

### 2. **Context Processor (Notification Detection)**

**Location:** `myApp/context_processors.py`

The context processor runs on **every page load** and checks for upcoming harvests:

```python
def harvest_notifications(request):
    upcoming_harvests = []
    
    if request.user.is_authenticated and request.user.role == 'farmer':
        today = timezone.now().date()
        five_days_from_now = today + timedelta(days=5)
        
        # Find forecasts with harvest_start within 5 days
        forecasts = Forecast.objects.filter(
            farmer=request.user,
            harvest_start__gte=today,
            harvest_start__lte=five_days_from_now
        ).select_related('crop').order_by('harvest_start')
        
        # Build notification data
        for forecast in forecasts:
            days_until = (forecast.harvest_start - today).days
            upcoming_harvests.append({
                'crop': forecast.crop.name,
                'harvest_start': forecast.harvest_start,
                'days_until': days_until,
                'forecast': forecast,
            })
    
    return {
        'upcoming_harvests': upcoming_harvests,
        'has_upcoming_harvests': len(upcoming_harvests) > 0,
    }
```

**What it does:**
- ✅ Only runs for authenticated farmers
- ✅ Checks if `harvest_start` is between **today** and **5 days from now**
- ✅ Calculates days remaining until harvest
- ✅ Returns data available in all templates

**Registered in:** `myProject/settings.py` (TEMPLATES → context_processors)

---

### 3. **UI Component (Notification Bell)**

**Location:** `myApp/templates/includes/header.html`

The notification bell appears in the navigation bar (before the logout button) when there are upcoming harvests:

```html
{% if has_upcoming_harvests %}
<div class="relative">
    <button id="notification-bell" onclick="toggleNotificationDropdown()">
        <!-- Bell icon with red badge showing count -->
        <span class="badge">{{ upcoming_harvests|length }}</span>
    </button>
    
    <!-- Dropdown panel (hidden by default) -->
    <div id="notification-dropdown" class="hidden">
        <!-- Shows each harvest with details -->
    </div>
</div>
{% endif %}
```

**Features:**
- 🔔 Bell icon with pulsing red indicator
- 🔴 Badge showing number of upcoming harvests
- 📋 Dropdown panel with detailed information
- ✨ Smooth animations and hover effects

---

### 4. **JavaScript Functionality**

**Location:** `myApp/templates/base.html`

```javascript
function toggleNotificationDropdown() {
    const dropdown = document.getElementById('notification-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('hidden');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const bell = document.getElementById('notification-bell');
    const dropdown = document.getElementById('notification-dropdown');
    
    if (dropdown && bell && !bell.contains(event.target) && !dropdown.contains(event.target)) {
        dropdown.classList.add('hidden');
    }
});
```

**Behavior:**
- Click bell icon → Opens/closes dropdown
- Click outside → Closes dropdown automatically
- Shows harvest details in a scrollable panel

---

## Data Flow Diagram

```
┌─────────────────┐
│  Farmer logs    │
│  Planting      │
│  Activity      │
└────────┬───────┘
         │
         ▼
┌─────────────────┐
│  Signal Handler │
│  (post_save)    │
└────────┬───────┘
         │
         ▼
┌─────────────────┐
│ compute_forecast │
│  calculates:    │
│  - harvest_start│
│  - harvest_end  │
└────────┬───────┘
         │
         ▼
┌─────────────────┐
│  Forecast Model │
│  (saved to DB)  │
└────────┬───────┘
         │
         ▼
┌─────────────────┐
│ Context         │
│ Processor       │
│ (every request) │
└────────┬───────┘
         │
         ▼
┌─────────────────┐
│  Template       │
│  (header.html)  │
│  Shows bell     │
└─────────────────┘
```

---

## Key Components

### Models

**Forecast Model** (`myApp/models.py`)
- `harvest_start`: Date when harvest can begin
- `harvest_end`: Date when harvest window ends
- `forecast_date`: Original planting date
- Linked to `farmer` and `crop`

**Crop Model** (`myApp/models.py`)
- `days_to_harvest_min`: Minimum days until harvest
- `days_to_harvest_max`: Maximum days until harvest

### Context Processor

**File:** `myApp/context_processors.py`
- Function: `harvest_notifications(request)`
- Returns: `upcoming_harvests` list and `has_upcoming_harvests` boolean
- Available in: All templates automatically

### Templates

**Header Template:** `myApp/templates/includes/header.html`
- Notification bell icon
- Dropdown panel with harvest details
- Status badges (Today, Tomorrow, Soon, Upcoming)

**Base Template:** `myApp/templates/base.html`
- JavaScript functions for dropdown interaction

---

## Configuration

### Notification Window

**Current Setting:** 5 days before harvest

To change the notification window, edit `myApp/context_processors.py`:

```python
# Change from 5 days to 7 days
five_days_from_now = today + timedelta(days=7)  # Changed from 5
```

### Who Sees Notifications

**Current:** Only farmers (`role == 'farmer'`)

To include other roles, edit `myApp/context_processors.py`:

```python
if request.user.is_authenticated and request.user.role == 'farmer':
    # Add other roles here if needed
```

---

## Example Scenarios

### Scenario 1: Single Harvest
- **Today:** February 16, 2026
- **Harvest Start:** February 18, 2026 (2 days away)
- **Display:** Bell shows "1" badge, dropdown shows Vegetables harvest details

### Scenario 2: Multiple Harvests
- **Today:** February 16, 2026
- **Harvest 1:** February 18, 2026 (Vegetables - 2 days)
- **Harvest 2:** February 20, 2026 (Corn - 4 days)
- **Display:** Bell shows "2" badge, dropdown shows both harvests

### Scenario 3: No Upcoming Harvests
- **Today:** February 16, 2026
- **Next Harvest:** March 1, 2026 (13 days away)
- **Display:** No notification bell (outside 5-day window)

---

## Status Badges

The system displays different badges based on days remaining:

- **"Today!"** (Red) - Harvest is today (0 days)
- **"Tomorrow"** (Orange) - Harvest is tomorrow (1 day)
- **"Soon"** (Amber) - Harvest in 2-3 days
- **"Upcoming"** (Green) - Harvest in 4-5 days

---

## Testing

To test the harvest reminder system:

1. **Create a demo account with upcoming harvest:**
   ```bash
   python seed_demo.py
   ```
   - Login as `farmer_carlos` (password: `demo12345`)
   - Has Vegetables harvest on February 18, 2026

2. **Create your own test:**
   - Log a planting activity with a date that results in harvest within 5 days
   - Example: If today is Feb 16, plant Vegetables on Dec 10, 2025

3. **Verify:**
   - Notification bell appears in navbar
   - Badge shows correct count
   - Dropdown shows harvest details
   - Status badges display correctly

---

## Troubleshooting

### Notification not showing?

1. **Check user role:** Must be `'farmer'`
2. **Check harvest date:** Must be within 5 days from today
3. **Check Forecast exists:** Verify `Forecast` record was created when planting activity was logged
4. **Check context processor:** Verify it's registered in `settings.py`

### Harvest date incorrect?

1. **Check planting date:** Verify the planting activity date is correct
2. **Check crop settings:** Verify `days_to_harvest_min` and `days_to_harvest_max` in Crop model
3. **Check forecast calculation:** Review `compute_forecast()` function in `models.py`

---

## Future Enhancements

Potential improvements:
- Email notifications for upcoming harvests
- SMS reminders
- Customizable notification window per farmer
- Harvest calendar view
- Integration with weather forecasts
- Mobile push notifications

---

## Files Reference

| File | Purpose |
|------|---------|
| `myApp/models.py` | Forecast model and auto-generation logic |
| `myApp/context_processors.py` | Notification detection |
| `myApp/templates/includes/header.html` | Notification bell UI |
| `myApp/templates/base.html` | JavaScript for dropdown |
| `myProject/settings.py` | Context processor registration |

---

**Last Updated:** February 2026
**Version:** 1.0

