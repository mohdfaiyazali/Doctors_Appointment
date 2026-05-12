from django.urls import path
from .views import book_appointment, my_appointments, cancel_appointment, doctor_dashboard, update_status, add_review, edit_medical_notes

urlpatterns = [
    path('book/<int:doctor_id>/', book_appointment, name='book_appointment'),
    path('my/', my_appointments, name='my_appointments'),
    path('cancel/<int:appointment_id>/', cancel_appointment, name='cancel_appointment'),

    path('doctor/', doctor_dashboard, name='doctor_dashboard'),
    path('update/<int:appointment_id>/<str:status>/', update_status, name='update_status'),
    path('review/<int:appointment_id>/', add_review, name='add_review'),
    path('notes/<int:appointment_id>/', edit_medical_notes, name='edit_medical_notes'),
]
