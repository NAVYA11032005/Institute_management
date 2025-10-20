from django.db import models
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from apps.courses.models import Course  # adjust if needed

# -------------------------------
# Choices
# -------------------------------

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

GENDER_CHOICES = [('male', 'Male'), ('female', 'Female'), ('other', 'Other')]

REFERRAL_SOURCE_CHOICES = [
    ('instagram', 'Instagram'), ('facebook', 'Facebook'), ('friend', 'Friend'),
    ('relative', 'Relative'), ('newspaper', 'Newspaper'), ('other', 'Other')
]

STATUS_CHOICES = [('active', 'Active'), ('deactive', 'Deactive'), ('completed', 'Completed')]

PAYMENT_METHOD_CHOICES = [
    ('one_time', 'One-Time'),
    ('monthly', 'Monthly'),
    ('installment', 'Installment')
]

PAYMENT_MODE_CHOICES = [
    ('cash', 'Cash'), ('card', 'Card'), ('upi', 'UPI'),
    ('bank_transfer', 'Bank Transfer'), ('online', 'Online')
]

# -------------------------------
# Soft Delete Mixin (for Trash)
# -------------------------------

class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    class Meta:
        abstract = True

# -------------------------------
# Student Model
# -------------------------------

class Student(SoftDeleteMixin, models.Model):
    student_id = models.CharField(max_length=20, primary_key=True, editable=False)
    full_name = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    email = models.EmailField(unique=True)
    dob = models.DateField()
    contact = models.CharField(max_length=15)
    emergency_contact_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True)
    state = models.CharField(max_length=50, choices=INDIAN_STATES)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    referral_source = models.CharField(max_length=20, choices=REFERRAL_SOURCE_CHOICES, blank=True, null=True)
    referred_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')
    referred_by_name = models.CharField(max_length=200, blank=True, null=True)
    photo = models.ImageField(upload_to='students/photos/', blank=True, null=True)
    documents = models.FileField(upload_to='students/documents/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.student_id:
            last = Student.objects.order_by('-student_id').first()
            next_id = int(last.student_id) + 1 if last and last.student_id.isdigit() else 25010001
            self.student_id = str(next_id)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.student_id})"

# -------------------------------
# Student Enrollment Model
# -------------------------------

class StudentEnrollment(SoftDeleteMixin, models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, to_field='student_id', related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    # Snapshots of Student info (denormalized fields)
    full_name = models.CharField(max_length=200, blank=True)
    father_name = models.CharField(max_length=200, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    email = models.EmailField(blank=True)
    dob = models.DateField(blank=True, null=True)
    contact = models.CharField(max_length=15, blank=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True)
    state = models.CharField(max_length=50, choices=INDIAN_STATES, blank=True)
    city = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=6, blank=True)
    referral_source = models.CharField(max_length=20, choices=REFERRAL_SOURCE_CHOICES, blank=True, null=True)
    referred_by = models.ForeignKey(Student, null=True, blank=True, on_delete=models.SET_NULL, related_name='enrollments_referred')
    referred_by_name = models.CharField(max_length=200, blank=True, null=True)

    # Finance fields
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_remaining = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES)
    payment_status = models.CharField(max_length=20, choices=[
        ('paid', 'Paid'), ('partial', 'Partial'), ('due', 'Due')
    ], default='due')

    total_installments = models.PositiveIntegerField(blank=True, null=True)
    batch_time = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    t_id = models.CharField(max_length=20, unique=True, editable=False, blank=True, null=True)
    certificate_number = models.CharField(max_length=20, unique=True, editable=False, blank=True, null=True)

    class Meta:
        unique_together = ('student', 'course')

    def save(self, *args, **kwargs):
        import re
        is_new = not self.pk

        if not self.enrollment_date:
            self.enrollment_date = timezone.now().date()

        if not self.due_date:
            self.due_date = self.enrollment_date + timezone.timedelta(days=30)

        actual_fee = Decimal(getattr(self.course, 'course_fee', 0) or 0)
        self.discount = Decimal(self.discount or 0)
        self.final_amount = max(actual_fee - self.discount, 0)

        paid = self.amount_paid
        remaining = max(self.final_amount - paid, 0)
        self.amount_remaining = remaining

        if self.payment_method == 'installment' and self.total_installments:
            per = self.final_amount / Decimal(self.total_installments)
        elif self.payment_method == 'monthly' and getattr(self.course, 'course_duration', None):
            duration = self.course.course_duration or 1
            per = self.final_amount / Decimal(duration)
        else:
            per = self.final_amount

        self.amount_due = 0 if paid >= self.final_amount else min(per, remaining)

        if remaining <= 0:
            self.payment_status = 'paid'
        elif paid > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'due'

        if is_new and not self.full_name and self.student:
            s = self.student
            self.full_name = s.full_name
            self.father_name = s.father_name
            self.gender = s.gender
            self.email = s.email
            self.dob = s.dob
            self.contact = s.contact
            self.emergency_contact_number = s.emergency_contact_number
            self.address = s.address
            self.state = s.state
            self.city = s.city
            self.pincode = s.pincode
            self.referral_source = s.referral_source
            self.referred_by = s.referred_by
            self.referred_by_name = s.referred_by_name

        if not self.t_id:
            last = StudentEnrollment.objects.exclude(t_id__isnull=True).exclude(t_id='').order_by('-id').first()
            next_number = 1
            if last and last.t_id and last.t_id[1:].isdigit():
                next_number = int(last.t_id[1:]) + 1
            self.t_id = f"E{next_number:04d}"

        if not self.certificate_number:
            last_cert = StudentEnrollment.objects.exclude(certificate_number__isnull=True).exclude(certificate_number='').order_by('-id').first()
            next_cert_num = 1
            if last_cert and last_cert.certificate_number:
                m = re.search(r'CP-CN-(\d+)', last_cert.certificate_number)
                if m:
                    next_cert_num = int(m.group(1)) + 1
            self.certificate_number = f"CP-CN-{next_cert_num:03d}"

        super().save(*args, **kwargs)

    @property
    def amount_paid(self):
        if not self.pk:
            return Decimal('0.00')
        result = self.payments.aggregate(total=Sum('amount_paid'))
        return Decimal(result['total'] or 0)

    def delete(self, *args, **kwargs):
        # Soft delete this enrollment
        self.is_deleted = True
        self.deleted_at = timezone.now()
        super().save(update_fields=['is_deleted', 'deleted_at'])

        # After soft-deleting this enrollment, check if all of the student's enrollments are deleted
        active_enrollments_count = StudentEnrollment.objects.filter(
            student=self.student,
            is_deleted=False
        ).count()
        if active_enrollments_count == 0:
            # Soft-delete the student
            self.student.is_deleted = True
            self.student.deleted_at = timezone.now()
            self.student.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        # Restore this enrollment
        self.is_deleted = False
        self.deleted_at = None
        super().save(update_fields=['is_deleted', 'deleted_at'])

        # If student is deleted, restore student as well
        if self.student.is_deleted:
            self.student.is_deleted = False
            self.student.deleted_at = None
            self.student.save(update_fields=['is_deleted', 'deleted_at'])

    def __str__(self):
        return f"[{self.t_id}] {self.student.full_name} - {self.course.course_name}"

# -------------------------------
# Payment Model
# -------------------------------

class Payment(models.Model):
    enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField(default=timezone.now)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES)
    payment_status = models.CharField(max_length=20, choices=[
        ('paid', 'Paid'), ('partial', 'Partial'), ('due', 'Due')
    ], default='partial')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.enrollment.save()  # To update enrollment aggregates when payment is saved

    def __str__(self):
        return f"₹{self.amount_paid} on {self.payment_date}"
