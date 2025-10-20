from django.db import models

class Course(models.Model):
    DURATION_TYPE_CHOICES = [
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ]
    course_name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Course Name"
    )
    course_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Course Fee (₹)"
    )
    course_duration = models.PositiveIntegerField(
        verbose_name="Course Duration"
    )
    duration_type = models.CharField(
        max_length=6,
        choices=DURATION_TYPE_CHOICES,
        default='months',
        verbose_name="Duration Type"
    )

    def __str__(self):
        return self.course_name
