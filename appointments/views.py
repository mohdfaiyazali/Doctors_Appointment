from django.shortcuts import render, redirect, get_object_or_404
from .models import Appointment
from doctors.models import DoctorProfile
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import datetime, time, date
from .decorators import doctor_required
from django.utils.timezone import now
from .models import Review
from .forms import ReviewForm, AppointmentMedicalNotesForm
from django.db import transaction, IntegrityError
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction, IntegrityError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.db.models import Q

User = get_user_model()


@login_required
def add_review(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # ❌ Only allow if completed
    if appointment.status != 'completed':
        messages.error(request, "You can only review completed appointments")
        return redirect('my_appointments')

    # ❌ Prevent duplicate review
    if Review.objects.filter(appointment=appointment).exists():
        messages.error(request, "You already reviewed this appointment")
        return redirect('my_appointments')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.appointment = appointment
            review.doctor = appointment.doctor
            review.patient = request.user
            review.save()

            messages.success(request, "Review submitted!")
            return redirect('my_appointments')
    else:
        form = ReviewForm()

    return render(request, 'appointments/add_review.html', {'form': form})

@login_required
def doctor_dashboard(request):
    doctor = request.user
    today = now().date()
    appointments = Appointment.objects.filter(doctor=doctor).order_by('-date', '-time')

    # 📊 Stats
    total_appointments = appointments.count()

    today_appointments = appointments.filter(date=now().date()).count()

    pending_count = appointments.filter(status='pending').count()
    confirmed_count = appointments.filter(status='confirmed').count()
    completed_count = appointments.filter(status='completed').count()
    cancelled_count = appointments.filter(status='cancelled').count()

    today_schedule = appointments.filter(date=today).order_by('time')
    pending_appointments = appointments.filter(status='pending').order_by('date', 'time')
    recent_reviews = Review.objects.filter(doctor=doctor).order_by('-created_at')[:5]

    return render(request, 'appointments/doctor_dashboard.html', {
        'appointments': appointments,
        'today_schedule': today_schedule,
        'pending_appointments': pending_appointments,
        'recent_reviews': recent_reviews,
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
    })


@login_required
def update_status(request, appointment_id, status):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=request.user  # ensure doctor owns it
    )

    if status in ['confirmed', 'cancelled', 'completed']:
        appointment.status = status
        appointment.save()

    return redirect('doctor_dashboard')


@login_required
def my_appointments(request):
    today = now().date()
    appointments = Appointment.objects.filter(patient=request.user).order_by('date', 'time')
    upcoming_appointments = appointments.filter(Q(date__gt=today) | Q(date=today, status__in=['pending', 'confirmed']))
    past_appointments = appointments.filter(Q(date__lt=today) | Q(status='completed')).exclude(status='cancelled')
    cancelled_appointments = appointments.filter(status='cancelled')

    return render(request, 'appointments/my_appointments.html', {
        'appointments': appointments,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'cancelled_appointments': cancelled_appointments,
    })


@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    appointment.status = 'cancelled'
    appointment.save()
    return redirect('my_appointments')


@login_required
@doctor_required
def edit_medical_notes(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)

    if request.method == 'POST':
        form = AppointmentMedicalNotesForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, "Medical notes updated.")
            return redirect('doctor_dashboard')
    else:
        form = AppointmentMedicalNotesForm(instance=appointment)

    return render(request, 'appointments/edit_medical_notes.html', {
        'appointment': appointment,
        'form': form,
    })



def generate_time_slots():
    slots = []
    start_hour = 10
    end_hour = 17

    for hour in range(start_hour, end_hour):
        slots.append(time(hour, 0))
        slots.append(time(hour, 30))

    return slots


@login_required
def book_appointment(request, doctor_id):
    doctor_profile = get_object_or_404(DoctorProfile, id=doctor_id)
    doctor = doctor_profile.user

    selected_date = request.GET.get('date')

    booked_slots = []
    all_slots = generate_time_slots()

    # ✅ Convert selected_date to proper date object
    selected_date_obj = None

    # ✅ Handle GET (for showing booked slots)
    if selected_date:
        try:
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()

            booked_slots = list(
                Appointment.objects.filter(
                    doctor=doctor,
                    date=selected_date_obj
                ).values_list('time', flat=True)
            )

        except ValueError:
            selected_date_obj = None

    # ✅ Handle POST (Booking)
    if request.method == 'POST':
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')

        try:
            selected_date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            selected_time_obj = datetime.strptime(time_str, "%H:%M").time()
        except (ValueError, TypeError):
            messages.error(request, "Invalid date or time format")
            return redirect(request.path)

        # ❌ Past date check
        if selected_date_obj < date.today():
            messages.error(request, "Cannot book past dates")
            return redirect(request.path + f"?date={date_str}")

        # ❌ Past time check
        if selected_date_obj == date.today():
            current_time = datetime.now().time()
            if selected_time_obj < current_time:
                messages.error(request, "Cannot book past time")
                return redirect(request.path + f"?date={date_str}")

        # ✅ Concurrency-safe booking
        try:
            with transaction.atomic():
                Appointment.objects.create(
                    patient=request.user,
                    doctor=doctor,
                    date=selected_date_obj,
                    time=selected_time_obj
                )

            # ✅ Send emails AFTER saving
            try:
                # Patient email
                if request.user.email:
                    send_mail(
                        subject='Appointment Confirmed',
                        message=f'Your appointment with Dr. {doctor.username} is confirmed on {selected_date_obj} at {selected_time_obj}.',
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[request.user.email],
                        fail_silently=True,
                    )

                # Doctor email
                if doctor.email:
                    send_mail(
                        subject='New Appointment Booked',
                        message=f'New appointment booked by {request.user.username} on {selected_date_obj} at {selected_time_obj}.',
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[doctor.email],
                        fail_silently=True,
                    )

                # ✅ HTML email (optional enhancement)
                if request.user.email:
                    html_content = render_to_string('emails/appointment_confirm.html', {
                        'user': request.user,
                        'doctor': doctor,
                        'date': selected_date_obj,
                        'time': selected_time_obj,
                    })

                    email = EmailMultiAlternatives(
                        subject='Appointment Confirmed',
                        body='Your appointment is confirmed.',
                        from_email=settings.EMAIL_HOST_USER,
                        to=[request.user.email],
                    )

                    email.attach_alternative(html_content, "text/html")
                    email.send()

            except Exception as e:
                print("Email sending failed:", e)

            # ✅ Success message AFTER everything
            messages.success(request, "Appointment booked successfully!")
            return redirect('doctor_list')

        except IntegrityError:
            messages.error(request, "⚠️ This slot was just booked by someone else.")
            return redirect(request.path + f"?date={date_str}")

    return render(request, 'appointments/book_appointment.html', {
        'doctor': doctor,
        'booked_slots': booked_slots,
        'selected_date': selected_date,
        'all_slots': all_slots
    })
