from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

User = settings.AUTH_USER_MODEL

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    experience = models.IntegerField(help_text="Years of experience")

    def __str__(self):
        return self.user.username


class DoctorAvailability(models.Model):
    WEEKDAY_CHOICES = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )

    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

    def __str__(self):
        return f"{self.doctor.username}: {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class DoctorBlockedDate(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_dates')
    date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('doctor', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.doctor.username}: blocked {self.date}"
