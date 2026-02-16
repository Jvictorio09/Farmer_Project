from django.utils import timezone
from datetime import timedelta
from .models import Forecast


def harvest_notifications(request):
    """
    Context processor to check for upcoming harvests (5 days before harvest_start).
    Returns a list of upcoming harvests for authenticated farmers.
    """
    upcoming_harvests = []
    
    if request.user.is_authenticated and request.user.role == 'farmer':
        today = timezone.now().date()
        # Check for harvests starting within the next 5 days
        five_days_from_now = today + timedelta(days=5)
        
        # Get forecasts where harvest_start is between today and 5 days from now
        forecasts = Forecast.objects.filter(
            farmer=request.user,
            harvest_start__gte=today,
            harvest_start__lte=five_days_from_now
        ).select_related('crop').order_by('harvest_start')
        
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

