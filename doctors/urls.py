from django.urls import path
from .views import (
    doctor_list,
    doctor_profile,
    manage_availability,
    delete_availability_slot,
    delete_blocked_date,
)

urlpatterns = [
    path('', doctor_list, name='doctor_list'),
    path('<int:doctor_id>/profile/', doctor_profile, name='doctor_profile'),
    path('availability/manage/', manage_availability, name='manage_availability'),
    path('availability/slot/<int:slot_id>/delete/', delete_availability_slot, name='delete_availability_slot'),
    path('availability/blocked/<int:blocked_id>/delete/', delete_blocked_date, name='delete_blocked_date'),
]
