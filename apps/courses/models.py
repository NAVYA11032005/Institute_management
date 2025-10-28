from django.db import models
from django.utils import timezone

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

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def delete(self, *args, **kwargs):
        """
        Soft delete - mark as deleted with a timestamp.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """
        Restore soft-deleted course.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def __str__(self):
        return self.course_name
