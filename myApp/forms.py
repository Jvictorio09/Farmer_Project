from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'region']


# forms.py
from django import forms
from .models import Activity

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['crop', 'activity_type', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional notes...'}),
        }


from .models import Crop

class CropForm(forms.ModelForm):
    class Meta:
        model = Crop
        fields = ['name', 'description', 'ideal_seasons']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Eggplant'}),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Brief description of the crop'}),
            'ideal_seasons': forms.TextInput(attrs={'placeholder': 'e.g., Jan-Mar, Jul-Sep'}),
        }


from .models import Expense
from django import forms

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['expense_type', 'amount', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional notes...'}),
        }


# forms.py
from django import forms
from .models import Forecast

class ForecastForm(forms.ModelForm):
    class Meta:
        model = Forecast
        fields = ['crop', 'expected_yield_kg', 'forecast_date', 'notes']
