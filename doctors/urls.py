from django.urls import path
from .views import doctor_list, doctor_profile

urlpatterns = [
    path('', doctor_list, name='doctor_list'),
    path('<int:doctor_id>/profile/', doctor_profile, name='doctor_profile'),
]
