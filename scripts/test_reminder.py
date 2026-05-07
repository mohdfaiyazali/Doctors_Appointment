from django.contrib.auth import get_user_model
from appointments.models import Appointment
from django.utils.timezone import now
from datetime import time

User = get_user_model()

user = User.objects.first()
doctor = User.objects.last()

Appointment.objects.create(
    patient=user,
    doctor=doctor,
    date=now().date(),
    time=time(10, 0)
)

print("✅ Test appointment created")