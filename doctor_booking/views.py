from .decorators import doctor_required


@doctor_required
def doctor_dashboard(request):
    appointments = Appointment.objects.filter(doctor=request.user.doctor)

    return render(request, 'appointments/doctor_dashboard.html', {
        'appointments': appointments
    })
