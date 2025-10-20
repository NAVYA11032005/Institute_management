from django.db import models
from django.utils import timezone
from apps.courses.models import Course
from apps.students.models import Student

# State Choices
INDIAN_STATES = [
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Odisha', 'Odisha'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Tripura', 'Tripura'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal'),
    ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands'),
    ('Chandigarh', 'Chandigarh'),
    ('Dadra and Nagar Haveli and Daman and Diu', 'Dadra and Nagar Haveli and Daman and Diu'),
    ('Delhi', 'Delhi'),
    ('Jammu and Kashmir', 'Jammu and Kashmir'),
    ('Ladakh', 'Ladakh'),
    ('Lakshadweep', 'Lakshadweep'),
    ('Puducherry', 'Puducherry'),
]

REFERRAL_SOURCE_CHOICES = [
    ('instagram', 'Instagram'),
    ('facebook', 'Facebook'),
    ('friend', 'Friend'),
    ('relative', 'Relative'),
    ('newspaper', 'Newspaper'),
    ('other', 'Other'),
]

class Enquiry(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(max_length=254, blank=True, null=True)  # made optional
    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    state = models.CharField(max_length=50, choices=INDIAN_STATES)
    city = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    referral_source = models.CharField(
        max_length=20,
        choices=REFERRAL_SOURCE_CHOICES,
        verbose_name="How did you find us?",
        blank=True,
        null=True,
    )
    # Reference by Student Registration Number (optional)
    reference_registration_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,  # made optional
        help_text="Reference by Student Registration Number (if any)"
    )
    # Reference by Name (if not by registration number)
    reference_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Reference by Name (if not by registration number)"
    )
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def delete(self, *args, **kwargs):
        # Soft delete implementation
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        # Restore a soft-deleted enquiry
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def get_referral_source_display(self):
        return dict(REFERRAL_SOURCE_CHOICES).get(self.referral_source, self.referral_source or "-")

    def get_reference_student(self):
        """
        Returns the Student object if reference_registration_number matches a student.
        """
        if self.reference_registration_number:
            try:
                return Student.objects.get(student_id=self.reference_registration_number)
            except Student.DoesNotExist:
                return None
        return None

    def reference_student_data(self):
        """
        Returns a dictionary of the referenced student's data, or None if not found.
        """
        student = self.get_reference_student()
        if student:
            return {
                "full_name": student.full_name,
                "email": student.email,
                "contact": student.contact,
                "state": student.state,
                "city": student.city,
                "referral_source": student.get_referral_source_display(),
                "enrollments": list(student.enrollments.values(
                    "course__course_name", "enrollment_date", "status", "final_amount"
                )),
            }
        return None

    def __str__(self):
        return f"Enquiry from {self.name}" + (f" ({self.email})" if self.email else "")

    class Meta:
        ordering = ['-created_at']
