from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    experience = models.IntegerField(help_text="Years of experience")

    def __str__(self):
        return self.user.username