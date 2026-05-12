from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from .forms import RegisterForm
from appointments.models import Appointment

def register_view(request):
    form = RegisterForm()

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('doctor_list')

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('doctor_list')

    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    if request.user.role == 'doctor':
        appointments = Appointment.objects.filter(doctor=request.user)
    else:
        appointments = Appointment.objects.filter(patient=request.user)

    context = {
        'total_appointments': appointments.count(),
        'pending_count': appointments.filter(status='pending').count(),
        'confirmed_count': appointments.filter(status='confirmed').count(),
        'completed_count': appointments.filter(status='completed').count(),
        'cancelled_count': appointments.filter(status='cancelled').count(),
        'recent_appointments': appointments.order_by('-date', '-time')[:5],
    }

    if request.user.role == 'doctor':
        context['doctor_profile'] = getattr(request.user, 'doctorprofile', None)
        context.update(request.user.doctor_reviews.aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id')
        ))

    return render(request, 'users/profile.html', context)
