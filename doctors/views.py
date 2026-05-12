from django.shortcuts import render
from .models import DoctorProfile
from django.db.models import Avg, Count
from django.utils.timezone import now
from appointments.models import Appointment


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