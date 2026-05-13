from django import forms
from .models import DoctorAvailability, DoctorBlockedDate


class DoctorAvailabilityForm(forms.ModelForm):
    class Meta:
        model = DoctorAvailability
        fields = ['day_of_week', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class DoctorBlockedDateForm(forms.ModelForm):
    class Meta:
        model = DoctorBlockedDate
        fields = ['date', 'reason']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
