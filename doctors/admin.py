from django.contrib import admin
from .models import DoctorProfile, DoctorAvailability, DoctorBlockedDate

admin.site.register(DoctorProfile)
admin.site.register(DoctorAvailability)
admin.site.register(DoctorBlockedDate)
