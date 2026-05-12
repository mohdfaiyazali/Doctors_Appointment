from django import forms
from .models import Review, Appointment

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']


class AppointmentMedicalNotesForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['diagnosis_summary', 'prescription_text', 'patient_notes', 'doctor_private_notes']
        widgets = {
            'diagnosis_summary': forms.Textarea(attrs={'rows': 3}),
            'prescription_text': forms.Textarea(attrs={'rows': 4}),
            'patient_notes': forms.Textarea(attrs={'rows': 3}),
            'doctor_private_notes': forms.Textarea(attrs={'rows': 4}),
        }
