from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('doctors/', include('doctors.urls')),
    path('appointments/', include('appointments.urls')),
    path('users/', include('users.urls')),



]
