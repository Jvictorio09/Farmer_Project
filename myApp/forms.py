from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import (
    User,
    Activity,
    Crop,
    Expense,
    Forecast,
)

# ======================
# 🔐 USER REGISTRATION
# ======================

class CustomUserCreationForm(UserCreationForm):
    assigned_admin = forms.ModelChoiceField(
        queryset=User.objects.filter(role='admin').order_by('username'),
        required=False,
        empty_label="-- Select Admin (Optional) --",
        help_text="Select which admin will manage this farmer (only for farmers)"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'region', 'assigned_admin']
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        assigned_admin = cleaned_data.get('assigned_admin')
        
        # Only require/admin assignment for farmers
        if role != 'farmer' and assigned_admin:
            # Clear assigned_admin if role is not farmer
            cleaned_data['assigned_admin'] = None
        
        return cleaned_data


# ======================
# 📋 ACTIVITY FORM
# ======================

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = [
            'crop',
            'activity_type',
            'date',
            'notes',
            'area_ha',
            'seed_qty_kg',
            'fert_sacks',
            'spacing',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Optional notes (e.g. weather, pests, issues)',
                }
            ),
            'area_ha': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'seed_qty_kg': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'fert_sacks': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'spacing': forms.TextInput(attrs={'placeholder': 'e.g., 20x20 cm'}),
        }


# ======================
# 🌱 CROP FORM
# ======================

class CropForm(forms.ModelForm):
    class Meta:
        model = Crop
        fields = [
            'name',
            'description',
            'ideal_seasons',
            'days_to_harvest_min',
            'days_to_harvest_max',
            'seed_rate_min_kg',
            'seed_rate_max_kg',
            'fert_sacks_min',
            'fert_sacks_max',
            'yield_t_min',
            'yield_t_max',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Rice'}),
            'description': forms.Textarea(
                attrs={'rows': 2, 'placeholder': 'Brief crop description'}
            ),
            'ideal_seasons': forms.TextInput(
                attrs={'placeholder': 'e.g., Jan–Mar, Jul–Sep'}
            ),
            'days_to_harvest_min': forms.NumberInput(attrs={'min': '0'}),
            'days_to_harvest_max': forms.NumberInput(attrs={'min': '0'}),
            'seed_rate_min_kg': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'seed_rate_max_kg': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'fert_sacks_min': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'fert_sacks_max': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'yield_t_min': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'yield_t_max': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }


# ======================
# 💰 EXPENSE FORM
# ======================

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['crop', 'expense_type', 'amount', 'date', 'description']

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(
                attrs={'rows': 2, 'placeholder': 'Optional notes'}
            ),
        }


# ======================
# 📈 FORECAST FORM (OPTIONAL / ADMIN)
# ======================

class ForecastForm(forms.ModelForm):
    class Meta:
        model = Forecast
        fields = [
            'crop',
            'expected_yield_kg',
            'forecast_date',
            'notes',
        ]
