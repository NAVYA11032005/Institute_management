from django import forms
from django.utils import timezone
from decimal import Decimal
from .models import (
    Student,
    StudentEnrollment,
    Payment,
    REFERRAL_SOURCE_CHOICES,
    STATUS_CHOICES,
)
from apps.courses.models import Course


class StudentEnrollmentForm(forms.ModelForm):
    # Control to select new or existing student
    student_type = forms.ChoiceField(
        choices=[('new', 'New Student'), ('previous', 'Previous Student')],
        widget=forms.RadioSelect,
        initial='new',
        label='Student Type'
    )

    # Only show active (non-deleted) students in selection
    previous_student = forms.ModelChoiceField(
        queryset=Student.objects.filter(is_deleted=False),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Select Existing Student'
    )

    # Student details fields (used for new students)
    full_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    father_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    gender = forms.ChoiceField(
        choices=[('', '---')] + list(Student._meta.get_field('gender').choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    dob = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    contact = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    emergency_contact_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})
    )
    state = forms.ChoiceField(
        required=False,
        choices=[('', '---------')] + list(Student._meta.get_field('state').choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    pincode = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    photo = forms.ImageField(required=False)
    documents = forms.FileField(required=False)

    # Referral fields
    referral_source = forms.ChoiceField(
        required=False,
        choices=[('', '---------')] + list(REFERRAL_SOURCE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    referred_by_student_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Referred By Student ID'
    )
    referred_by_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Referred By Name'
    )

    # Enrollment fields
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    discount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    payment_method = forms.ChoiceField(
    choices=[('', '---------')] + list(StudentEnrollment._meta.get_field('payment_method').choices),
    widget=forms.Select(attrs={'class': 'form-select'})
)

    payment_mode = forms.ChoiceField(
        choices=Payment._meta.get_field('payment_mode').choices,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    total_installments = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    batch_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    enrollment_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date
    )
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=lambda: timezone.now().date() + timezone.timedelta(days=30)
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})
    )

    # Initial payment (optional)
    initial_payment = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    # Display certificate number as read-only (not saved directly)
    certificate_number_display = forms.CharField(
        label='Certificate Number',
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = StudentEnrollment
        exclude = [
            'student', 'referred_by', 'referred_by_name', 'payment_status',
            't_id', 'final_amount', 'amount_due', 'amount_remaining', 'certificate_number',
            'is_deleted', 'deleted_at'  # soft delete fields handled programmatically
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fill certificate number display if updating existing enrollment
        if self.instance and self.instance.pk and self.instance.certificate_number:
            self.fields['certificate_number_display'].initial = self.instance.certificate_number

    def clean(self):
        cleaned = super().clean()
        student_type = cleaned.get('student_type')
        email = cleaned.get('email')

        if student_type == 'new' and email:
            existing_qs = Student.objects.filter(email=email, is_deleted=False)
            if self.instance and getattr(self.instance, 'student', None):
                existing_qs = existing_qs.exclude(pk=self.instance.student.pk)
            if existing_qs.exists():
                self.add_error('email', 'A student with this email already exists.')

        return cleaned

    def save(self, commit=True):
        cleaned = self.cleaned_data
        student_type = cleaned.get('student_type')
        ref_id = cleaned.get('referred_by_student_id')
        referred_by = Student.objects.filter(student_id=ref_id, is_deleted=False).first() if ref_id else None

        if student_type == 'previous':
            student = cleaned.get('previous_student')
        else:
            # Create or update the student info
            student = getattr(self.instance, 'student', None) or Student()
            student.full_name = cleaned.get('full_name')
            student.father_name = cleaned.get('father_name')
            student.gender = cleaned.get('gender')
            student.email = cleaned.get('email')
            student.dob = cleaned.get('dob')
            student.contact = cleaned.get('contact')
            student.emergency_contact_number = cleaned.get('emergency_contact_number')
            student.address = cleaned.get('address')
            student.state = cleaned.get('state')
            student.city = cleaned.get('city')
            student.pincode = cleaned.get('pincode')
            student.referral_source = cleaned.get('referral_source')
            student.referred_by = referred_by
            student.referred_by_name = cleaned.get('referred_by_name')

            # Handle file fields - update only if file uploaded
            if self.files and self.files.get('photo'):
                student.photo = self.files['photo']
            if self.files and self.files.get('documents'):
                student.documents = self.files['documents']

            if commit:
                student.save()

        enrollment = self.instance or StudentEnrollment()
        enrollment.student = student
        enrollment.course = cleaned.get('course')
        enrollment.status = cleaned.get('status')
        enrollment.enrollment_date = cleaned.get('enrollment_date') or timezone.now().date()
        enrollment.due_date = cleaned.get('due_date') or (enrollment.enrollment_date + timezone.timedelta(days=30))
        enrollment.notes = cleaned.get('notes')
        enrollment.payment_method = cleaned.get('payment_method')
        enrollment.payment_mode = cleaned.get('payment_mode')
        enrollment.batch_time = cleaned.get('batch_time')
        enrollment.discount = cleaned.get('discount') or Decimal('0.00')
        enrollment.total_installments = cleaned.get('total_installments')
        enrollment.referred_by = referred_by
        enrollment.referred_by_name = cleaned.get('referred_by_name')
        enrollment.referral_source = cleaned.get('referral_source')

        if commit:
            enrollment.save()
            # Update certificate number display field after save
            self.fields['certificate_number_display'].initial = enrollment.certificate_number

        return enrollment
