from django.core.management.base import BaseCommand
from faker import Faker
import random
from datetime import timedelta
from django.utils import timezone

from users.models import User
from doctors.models import DoctorProfile
from appointments.models import Appointment

fake = Faker()

class Command(BaseCommand):
    help = "Seed fake data"

    def handle(self, *args, **kwargs):

        # Create Doctors
        doctors = []
        for _ in range(10):
            user = User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password="password123",
                role="doctor"
            )

            profile = DoctorProfile.objects.create(
                user=user,
                specialization=random.choice(["Cardiology", "Dermatology", "General"]),
                experience=random.randint(1, 20)
            )

            doctors.append(user)

        # Create Patients
        patients = []
        for _ in range(50):
            user = User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password="password123",
                role="patient"
            )
            patients.append(user)

        # Create Appointments
        statuses = ["pending", "confirmed", "cancelled"]

        for _ in range(100):
            Appointment.objects.create(
                patient=random.choice(patients),
                doctor=random.choice(doctors),
                date=timezone.now().date() + timedelta(days=random.randint(-5, 5)),
                time=fake.time(),
                status=random.choice(statuses)
            )

        self.stdout.write(self.style.SUCCESS("✅ Data seeded successfully"))