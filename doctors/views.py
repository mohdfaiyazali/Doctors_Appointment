from django.shortcuts import render, get_object_or_404, redirect
from .models import DoctorProfile, DoctorAvailability, DoctorBlockedDate
from django.db.models import Avg, Count
from django.utils.timezone import now
from appointments.models import Appointment
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import DoctorAvailabilityForm, DoctorBlockedDateForm


def doctor_list(request):
    doctors = DoctorProfile.objects.all()

    # 🔍 Search
    query = request.GET.get('q')
    if query:
        doctors = doctors.filter(user__username__icontains=query)

    # 🎯 Specialization
    specialization = request.GET.get('specialization')
    if specialization:
        doctors = doctors.filter(specialization__icontains=specialization)

    # 🎯 Experience
    min_exp = request.GET.get('min_exp')
    if min_exp:
        doctors = doctors.filter(experience__gte=min_exp)

    # ⭐ Ratings
    doctors = doctors.annotate(
        avg_rating=Avg('user__doctor_reviews__rating'),
        total_reviews=Count('user__doctor_reviews', distinct=True)
    ).order_by('-avg_rating')

    # Dropdown
    specializations = DoctorProfile.objects.values_list(
        'specialization', flat=True
    ).distinct()

    # 🔔 Reminder
    upcoming_appointment = None

    if request.user.is_authenticated:
        today = now().date()

        upcoming_appointment = Appointment.objects.filter(
            patient=request.user,
            date=today,
            status__in=['pending', 'confirmed']
        ).order_by('time').first()

    return render(request, 'doctors/doctor_list.html', {
        'doctors': doctors,
        'specializations': specializations,
        'upcoming_appointment': upcoming_appointment
    })


def doctor_profile(request, doctor_id):
    doctor = get_object_or_404(
        DoctorProfile.objects.annotate(
            avg_rating=Avg('user__doctor_reviews__rating'),
            total_reviews=Count('user__doctor_reviews', distinct=True)
        ),
        id=doctor_id
    )

    reviews = doctor.user.doctor_reviews.select_related('patient').order_by('-created_at')
    completed_appointments = Appointment.objects.filter(
        doctor=doctor.user,
        status='completed'
    ).count()

    return render(request, 'doctors/doctor_profile.html', {
        'doctor': doctor,
        'reviews': reviews,
        'completed_appointments': completed_appointments,
    })


@login_required
def manage_availability(request):
    if request.user.role != 'doctor':
        messages.error(request, "Only doctors can manage availability.")
        return redirect('doctor_list')

    availability_form = DoctorAvailabilityForm()
    blocked_form = DoctorBlockedDateForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_slot':
            availability_form = DoctorAvailabilityForm(request.POST)
            if availability_form.is_valid():
                slot = availability_form.save(commit=False)
                slot.doctor = request.user
                slot.save()
                messages.success(request, "Availability slot added.")
                return redirect('manage_availability')
        elif action == 'add_blocked_date':
            blocked_form = DoctorBlockedDateForm(request.POST)
            if blocked_form.is_valid():
                block = blocked_form.save(commit=False)
                block.doctor = request.user
                block.save()
                messages.success(request, "Blocked date added.")
                return redirect('manage_availability')

    slots = DoctorAvailability.objects.filter(doctor=request.user)
    blocked_dates = DoctorBlockedDate.objects.filter(doctor=request.user)
    return render(request, 'doctors/manage_availability.html', {
        'availability_form': availability_form,
        'blocked_form': blocked_form,
        'slots': slots,
        'blocked_dates': blocked_dates,
    })


@login_required
def delete_availability_slot(request, slot_id):
    slot = get_object_or_404(DoctorAvailability, id=slot_id, doctor=request.user)
    slot.delete()
    messages.success(request, "Availability slot deleted.")
    return redirect('manage_availability')


@login_required
def delete_blocked_date(request, blocked_id):
    blocked = get_object_or_404(DoctorBlockedDate, id=blocked_id, doctor=request.user)
    blocked.delete()
    messages.success(request, "Blocked date removed.")
    return redirect('manage_availability')
