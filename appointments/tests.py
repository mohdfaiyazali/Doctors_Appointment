from django.test import TestCase
from django.urls import reverse
from datetime import timedelta
from django.utils.timezone import now

from users.models import User
from doctors.models import DoctorProfile
from doctors.models import DoctorAvailability, DoctorBlockedDate
from appointments.models import Appointment


class AppointmentFeatureTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            username='doctor1',
            password='pass12345',
            role='doctor',
            email='doctor@example.com',
        )
        self.patient = User.objects.create_user(
            username='patient1',
            password='pass12345',
            role='patient',
            email='patient@example.com',
        )
        self.other_patient = User.objects.create_user(
            username='patient2',
            password='pass12345',
            role='patient',
            email='patient2@example.com',
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor,
            specialization='Cardiology',
            experience=10,
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=now().date() - timedelta(days=1),
            time=now().time().replace(second=0, microsecond=0),
            status='completed',
        )

    def test_doctor_can_update_medical_notes(self):
        self.client.login(username='doctor1', password='pass12345')
        response = self.client.post(
            reverse('edit_medical_notes', args=[self.appointment.id]),
            data={
                'diagnosis_summary': 'Flu symptoms',
                'prescription_text': 'Paracetamol 500mg',
                'patient_notes': 'Drink warm fluids',
                'doctor_private_notes': 'Follow-up if fever > 3 days',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.diagnosis_summary, 'Flu symptoms')
        self.assertEqual(self.appointment.doctor_private_notes, 'Follow-up if fever > 3 days')

    def test_patient_cannot_access_edit_medical_notes(self):
        self.client.login(username='patient1', password='pass12345')
        response = self.client.get(reverse('edit_medical_notes', args=[self.appointment.id]))
        self.assertEqual(response.status_code, 403)

    def test_patient_dashboard_hides_doctor_private_notes(self):
        self.appointment.diagnosis_summary = 'Migraine'
        self.appointment.prescription_text = 'Ibuprofen'
        self.appointment.patient_notes = 'Take rest'
        self.appointment.doctor_private_notes = 'High stress case'
        self.appointment.save()

        self.client.login(username='patient1', password='pass12345')
        response = self.client.get(reverse('my_appointments'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Migraine')
        self.assertContains(response, 'Ibuprofen')
        self.assertContains(response, 'Take rest')
        self.assertNotContains(response, 'High stress case')

    def test_quick_rebook_shows_on_cancelled_appointments(self):
        cancelled = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=now().date() + timedelta(days=2),
            time=now().time().replace(second=0, microsecond=0),
            status='cancelled',
        )
        self.client.login(username='patient1', password='pass12345')
        response = self.client.get(reverse('my_appointments'))
        self.assertEqual(response.status_code, 200)
        quick_rebook_url = reverse('book_appointment', args=[cancelled.doctor.doctorprofile.id])
        self.assertContains(response, quick_rebook_url)

    def test_medical_notes_link_visible_for_todays_schedule(self):
        today_appointment = Appointment.objects.create(
            patient=self.other_patient,
            doctor=self.doctor,
            date=now().date(),
            time=now().time().replace(second=0, microsecond=0),
            status='confirmed',
        )
        self.client.login(username='doctor1', password='pass12345')
        response = self.client.get(reverse('doctor_dashboard'))
        self.assertEqual(response.status_code, 200)
        expected_url = reverse('edit_medical_notes', args=[today_appointment.id])
        self.assertContains(response, expected_url)

    def test_medical_notes_link_not_visible_when_no_today_appointments(self):
        self.client.login(username='doctor1', password='pass12345')
        response = self.client.get(reverse('doctor_dashboard'))
        self.assertEqual(response.status_code, 200)
        # setUp appointment is yesterday, so today's table should be empty
        yesterday_url = reverse('edit_medical_notes', args=[self.appointment.id])
        self.assertNotContains(response, yesterday_url)

    def test_doctor_cannot_edit_other_doctors_appointment_notes(self):
        doctor2 = User.objects.create_user(
            username='doctor2',
            password='pass12345',
            role='doctor',
            email='doctor2@example.com',
        )
        DoctorProfile.objects.create(user=doctor2, specialization='ENT', experience=8)
        other_appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=doctor2,
            date=now().date(),
            time=now().time().replace(second=0, microsecond=0),
            status='confirmed',
        )
        self.client.login(username='doctor1', password='pass12345')
        response = self.client.get(reverse('edit_medical_notes', args=[other_appointment.id]))
        self.assertEqual(response.status_code, 404)

    def test_booking_get_shows_only_available_slots_for_day(self):
        monday = now().date()
        while monday.weekday() != 0:
            monday += timedelta(days=1)
        DoctorAvailability.objects.create(
            doctor=self.doctor,
            day_of_week=0,
            start_time='10:00',
            end_time='11:00',
        )
        self.client.login(username='patient1', password='pass12345')
        response = self.client.get(reverse('book_appointment', args=[self.doctor_profile.id]), {'date': monday.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '10:00')
        self.assertContains(response, '10:30')
        self.assertNotContains(response, '11:00')

    def test_booking_post_rejects_time_outside_availability(self):
        monday = now().date()
        while monday.weekday() != 0:
            monday += timedelta(days=1)
        DoctorAvailability.objects.create(
            doctor=self.doctor,
            day_of_week=0,
            start_time='10:00',
            end_time='11:00',
        )
        self.client.login(username='patient1', password='pass12345')
        response = self.client.post(
            reverse('book_appointment', args=[self.doctor_profile.id]),
            data={'date': monday.isoformat(), 'time': '12:00'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "outside doctor")
        self.assertFalse(
            Appointment.objects.filter(
                patient=self.patient,
                doctor=self.doctor,
                date=monday,
                time='12:00'
            ).exists()
        )

    def test_booking_post_rejects_blocked_date(self):
        monday = now().date()
        while monday.weekday() != 0:
            monday += timedelta(days=1)
        DoctorAvailability.objects.create(
            doctor=self.doctor,
            day_of_week=0,
            start_time='10:00',
            end_time='11:00',
        )
        DoctorBlockedDate.objects.create(
            doctor=self.doctor,
            date=monday,
            reason='Holiday'
        )
        self.client.login(username='patient1', password='pass12345')
        response = self.client.post(
            reverse('book_appointment', args=[self.doctor_profile.id]),
            data={'date': monday.isoformat(), 'time': '10:00'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "outside doctor")
        self.assertFalse(
            Appointment.objects.filter(
                patient=self.patient,
                doctor=self.doctor,
                date=monday,
                time='10:00'
            ).exists()
        )

    def test_booking_post_allows_time_within_availability(self):
        monday = now().date()
        while monday.weekday() != 0:
            monday += timedelta(days=1)
        DoctorAvailability.objects.create(
            doctor=self.doctor,
            day_of_week=0,
            start_time='10:00',
            end_time='11:00',
        )
        self.client.login(username='patient1', password='pass12345')
        response = self.client.post(
            reverse('book_appointment', args=[self.doctor_profile.id]),
            data={'date': monday.isoformat(), 'time': '10:00'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Appointment.objects.filter(
                patient=self.patient,
                doctor=self.doctor,
                date=monday,
                time='10:00'
            ).exists()
        )
