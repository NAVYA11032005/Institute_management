import re
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.db.models import Sum
from django.core.exceptions import ValidationError

from apps.courses import models as course_models
from apps.Settings import models as setting_models


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
    ('instagram', 'Instagram'),
    ('facebook', 'Facebook'),
    ('friend', 'Friend'),
    ('relative', 'Relative'),
    ('newspaper', 'Newspaper'),
    ('other', 'Other'),
]

STATUS_CHOICES = [('active', 'Active'), ('deactive', 'Deactive'), ('completed', 'Completed')]

PAYMENT_METHOD_CHOICES = [
    ('one_time', 'One-Time'),
    ('monthly', 'Monthly'),
    ('installment', 'Installment'),
]

PAYMENT_MODE_CHOICES = [
    ('cash', 'Cash'),
    ('card', 'Card'),
    ('upi', 'UPI'),
    ('bank_transfer', 'Bank Transfer'),
    ('online', 'Online'),
]

class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self, *args, **kwargs):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    class Meta:
        abstract = True


class Student(SoftDeleteMixin):
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
            last_student = Student.objects.filter(student_id__regex=r'^\d+$').order_by('-student_id').first()
            new_id = 25010001
            if last_student and last_student.student_id.isdigit():
                new_id = int(last_student.student_id) + 1
            self.student_id = str(new_id)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.student_id})"


class StudentEnrollment(SoftDeleteMixin):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(course_models.Course, on_delete=models.CASCADE)
    enrollment_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    admission_fee = models.DecimalField(max_digits=10, decimal_places=2, default=None, null=True, blank=True)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    amount_remaining = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, blank=True, null=True)

    payment_status = models.CharField(max_length=20,
                                     choices=[('paid', 'Paid'), ('partial', 'Partial'), ('due', 'Due')],
                                     default='due')

    total_installments = models.PositiveIntegerField(blank=True, null=True)
    batch_time = models.TimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    t_id = models.CharField(max_length=20, unique=True, blank=True, null=True, editable=False)
    certificate_number = models.CharField(max_length=20, unique=True, blank=True, null=True, editable=False)

    class Meta:
        unique_together = ('student', 'course')

    def save(self, *args, **kwargs):
        if not self.enrollment_date:
            self.enrollment_date = timezone.now().date()
        if not self.due_date:
            self.due_date = self.enrollment_date + timezone.timedelta(days=30)

        # Use admission fee if set, else use default from settings
        if self.admission_fee is None:
            setting = setting_models.Setting.objects.first()
            self.admission_fee = setting.admission_fee if setting else Decimal('0.00')

        course_fee = getattr(self.course, 'course_fee', Decimal('0.00')) or Decimal('0.00')
        self.discount = self.discount or Decimal('0.00')
        discounted_course_fee = max(course_fee - self.discount, Decimal('0.00'))

        # Calculate final amount accurately
        self.final_amount = self.admission_fee + discounted_course_fee

        # Recalculate payment totals from payments, or zero without pk
        paid_admission_fee = self.admission_fee_paid if self.pk else Decimal('0.00')
        paid_course_fee = self.course_fee_paid if self.pk else Decimal('0.00')

        remaining_admission_fee = max(self.admission_fee - paid_admission_fee, Decimal('0.00'))
        remaining_course_fee = max(discounted_course_fee - paid_course_fee, Decimal('0.00'))

        self.amount_remaining = remaining_admission_fee + remaining_course_fee

        duration = getattr(self.course, 'course_duration', None) or 1

        if self.payment_method == 'installment' and self.total_installments:
            per_due = discounted_course_fee / Decimal(self.total_installments)
        elif self.payment_method == 'monthly' and duration:
            per_due = discounted_course_fee / Decimal(duration)
        else:
            per_due = discounted_course_fee

        self.amount_due = Decimal('0.00') if paid_course_fee >= discounted_course_fee else min(per_due, remaining_course_fee)

        if self.amount_remaining == Decimal('0.00'):
            self.payment_status = 'paid'
        elif paid_admission_fee > Decimal('0.00') or paid_course_fee > Decimal('0.00'):
            self.payment_status = 'partial'
        else:
            self.payment_status = 'due'

        # Generate unique t_id if missing
        if not self.t_id:
            last_enrollment = StudentEnrollment.objects.filter(t_id__isnull=False).exclude(t_id='').order_by('-id').first()
            next_id = 1
            if last_enrollment and last_enrollment.t_id and last_enrollment.t_id[1:].isdigit():
                next_id = int(last_enrollment.t_id[1:]) + 1
            self.t_id = f"E{next_id:04d}"

        # Generate certificate_number if missing
        if not self.certificate_number:
            last_cert = StudentEnrollment.objects.exclude(certificate_number__isnull=True).exclude(certificate_number='').order_by('-id').first()
            next_cert_num = 1
            if last_cert:
                match = re.search(r"CP-CN-(\d+)", last_cert.certificate_number)
                if match:
                    next_cert_num = int(match.group(1)) + 1
            self.certificate_number = f"CP-CN-{next_cert_num:03d}"

        super().save(*args, **kwargs)

    @property
    def admission_fee_paid(self):
        total = self.payments.filter(remarks__iexact='Admission Fee').aggregate(total=Sum('amount_paid'))['total']
        return Decimal(total or 0)

    @property
    def course_fee_paid(self):
        total = self.payments.filter(remarks__iexact='Course Fee').aggregate(total=Sum('amount_paid'))['total']
        return Decimal(total or 0)

    @property
    def admission_fee_remaining(self):
        rem = self.admission_fee - self.admission_fee_paid
        return rem if rem > Decimal('0.00') else Decimal('0.00')

    @property
    def course_fee_remaining(self):
        course_fee = getattr(self.course, 'course_fee', Decimal('0.00')) or Decimal('0.00')
        rem = max(course_fee - self.discount - self.course_fee_paid, Decimal('0.00'))
        return rem

    @property
    def total_amount_paid(self):
        total = self.admission_fee_paid + self.course_fee_paid
        return total if total > Decimal('0.00') else Decimal('0.00')

    @property
    def total_amount_remaining(self):
        remaining = self.final_amount - self.total_amount_paid
        return remaining if remaining > Decimal('0.00') else Decimal('0.00')

    def apply_initial_payment(self, initial_payment: Decimal, payment_mode='cash'):
        if not self.pk:
            raise ValidationError("Save enrollment before processing payments.")

        payments_created = []
        remaining_payment = initial_payment

        admission_due = self.admission_fee_remaining
        if admission_due > Decimal('0.00'):
            pay_amount = min(remaining_payment, admission_due)
            p = Payment.objects.create(
                enrollment=self,
                amount=admission_due,
                amount_paid=pay_amount,
                payment_mode=payment_mode,
                payment_status='paid' if pay_amount >= admission_due else 'partial',
                remarks='Admission Fee',
                payment_date=timezone.now().date(),
            )
            payments_created.append(p)
            remaining_payment -= pay_amount

        course_due = self.course_fee_remaining
        if remaining_payment > Decimal('0.00') and course_due > Decimal('0.00'):
            pay_amount = min(remaining_payment, course_due)
            p = Payment.objects.create(
                enrollment=self,
                amount=course_due,
                amount_paid=pay_amount,
                payment_mode=payment_mode,
                payment_status='paid' if pay_amount >= course_due else 'partial',
                remarks='Course Fee',
                payment_date=timezone.now().date(),
            )
            payments_created.append(p)
            remaining_payment -= pay_amount

        self.refresh_from_db()
        self.save(update_fields=['payment_status', 'amount_due', 'amount_remaining'])

        return payments_created

    def __str__(self):
        return f"{self.student.full_name} ({self.student.student_id}) - {self.course.course_name}"


class Payment(models.Model):
    enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES)
    payment_status = models.CharField(max_length=20,
                                      choices=[('paid', 'Paid'), ('partial', 'Partial'), ('due', 'Due')],
                                      default='due')
    remarks = models.CharField(max_length=255, blank=True, null=True)  # 'Admission Fee' or 'Course Fee'
    payment_date = models.DateField(default=timezone.now)

    def save(self, *args, **kwargs):
        if self.remarks:
            self.remarks = self.remarks.strip()
        super().save(*args, **kwargs)
        # After saving payment, update enrollment's payment status and amounts
        self.enrollment.save()

    def __str__(self):
        return f"{self.payment_date} - {self.enrollment.student.full_name} - ₹{self.amount_paid} ({self.remarks or 'Unknown'})"
