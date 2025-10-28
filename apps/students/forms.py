from django import forms
from django.utils import timezone
from decimal import Decimal

from .models import Student, StudentEnrollment, REFERRAL_SOURCE_CHOICES, STATUS_CHOICES, Payment
from apps.courses.models import Course
from apps.Settings.models import Setting


class StudentEnrollmentForm(forms.ModelForm):
    student_type = forms.ChoiceField(
        choices=[('new', 'New Student'), ('previous', 'Previous Student')],
        widget=forms.RadioSelect,
        initial='new',
        label='Student Type',
    )

    previous_student = forms.ModelChoiceField(
        queryset=Student.objects.filter(is_deleted=False),
        required=False,
        label='Select Existing Student',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    # New student fields
    full_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), label='Full Name')
    father_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), label="Father's Name")
    gender = forms.ChoiceField(
        required=False,
        choices=[('', '---')] + list(Student._meta.get_field('gender').choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    dob = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label='Date of Birth')
    contact = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), label='Contact Number')
    emergency_contact_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), label='Emergency Contact Number')
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}))
    state = forms.ChoiceField(
        required=False,
        choices=[('', '---------')] + list(Student._meta.get_field('state').choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    pincode = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    photo = forms.ImageField(required=False)
    documents = forms.FileField(required=False)

    referral_source = forms.ChoiceField(
        required=False,
        choices=[('', '---------')] + list(REFERRAL_SOURCE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    referred_by_student_id = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), label='Referred By (Student ID)')
    referred_by_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), label='Referred By (Name)')

    # Enrollment fields
    course = forms.ModelChoiceField(queryset=Course.objects.filter(is_deleted=False), widget=forms.Select(attrs={'class': 'form-select'}))
    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    discount = forms.DecimalField(required=False, min_value=0, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    admission_fee = forms.DecimalField(
        required=True,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Admission Fee',
    )
    payment_method = forms.ChoiceField(
        required=False,
        choices=[('', '---------')] + list(StudentEnrollment._meta.get_field('payment_method').choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    payment_mode = forms.ChoiceField(choices=Payment._meta.get_field('payment_mode').choices, widget=forms.Select(attrs={'class': 'form-select'}))
    total_installments = forms.IntegerField(required=False, min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    batch_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    enrollment_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), initial=timezone.now)
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=lambda: timezone.now().date() + timezone.timedelta(days=30),
    )
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}))

    # Initial payment field
    initial_payment = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Initial Payment (Admission + Course Fee)",
    )

    certificate_display = forms.CharField(
        label='Certificate Number',
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = StudentEnrollment
        exclude = [
            'student',
            'referred_by',
            'referred_by_name',
            'payment_status',
            't_id',
            'final_amount',
            'amount_due',
            'amount_remaining',
            'certificate_number',
            'is_deleted',
            'deleted_at',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set certificate number display if available
        if self.instance and self.instance.pk and self.instance.certificate_number:
            self.fields['certificate_display'].initial = self.instance.certificate_number

        # Set admission fee initial from settings if creating new enrollment
        if not (self.instance and self.instance.pk):
            setting = Setting.objects.first()
            default_adm_fee = setting.admission_fee if setting else Decimal('0.00')
            self.fields['admission_fee'].initial = default_adm_fee

    def clean(self):
        cleaned_data = super().clean()
        student_type = cleaned_data.get('student_type')
        email = cleaned_data.get('email')

        # For new student, email must be unique
        if student_type == 'new' and email:
            qs = Student.objects.filter(email=email, is_deleted=False)
            if self.instance and self.instance.pk and getattr(self.instance, 'student', None):
                qs = qs.exclude(pk=self.instance.student.pk)
            if qs.exists():
                self.add_error('email', 'A student with this email already exists.')
        return cleaned_data

    def save(self, commit=True):
        cleaned_data = self.cleaned_data
        student_type = cleaned_data.get('student_type')
        referred_by_student_id = cleaned_data.get('referred_by_student_id')
        referred_by_obj = None

        if referred_by_student_id:
            referred_by_obj = Student.objects.filter(student_id=referred_by_student_id, is_deleted=False).first()

        # Handle student creation or select previous student
        if student_type == 'previous':
            student = cleaned_data.get('previous_student')
            if not student:
                raise forms.ValidationError("Please select an existing student.")
        else:
            student = self.instance.student if self.instance.pk else Student()
            student.full_name = cleaned_data.get('full_name') or ''
            student.father_name = cleaned_data.get('father_name') or ''
            student.gender = cleaned_data.get('gender') or ''
            student.email = cleaned_data.get('email')
            student.dob = cleaned_data.get('dob')
            student.contact = cleaned_data.get('contact') or ''
            student.emergency_contact_number = cleaned_data.get('emergency_contact_number') or ''
            student.address = cleaned_data.get('address') or ''
            student.state = cleaned_data.get('state') or ''
            student.city = cleaned_data.get('city') or ''
            student.pincode = cleaned_data.get('pincode') or ''
            student.referral_source = cleaned_data.get('referral_source') or ''
            student.referred_by = referred_by_obj
            student.referred_by_name = cleaned_data.get('referred_by_name') or ''

            if self.files.get('photo'):
                student.photo = self.files['photo']
            if self.files.get('documents'):
                student.documents = self.files['documents']

            if commit:
                student.save()

        # Handle enrollment create/update
        enrollment = self.instance if self.instance.pk else StudentEnrollment()
        enrollment.student = student
        enrollment.course = cleaned_data.get('course')
        enrollment.status = cleaned_data.get('status')
        enrollment.enrollment_date = cleaned_data.get('enrollment_date') or timezone.now().date()
        enrollment.due_date = cleaned_data.get('due_date') or (enrollment.enrollment_date + timezone.timedelta(days=30))
        enrollment.notes = cleaned_data.get('notes')
        enrollment.payment_method = cleaned_data.get('payment_method')
        enrollment.payment_mode = cleaned_data.get('payment_mode')
        enrollment.total_installments = cleaned_data.get('total_installments')
        enrollment.batch_time = cleaned_data.get('batch_time')
        enrollment.discount = cleaned_data.get('discount') or Decimal('0.00')
        enrollment.admission_fee = cleaned_data.get('admission_fee') or Decimal('0.00')
        enrollment.referred_by = referred_by_obj
        enrollment.referred_by_name = cleaned_data.get('referred_by_name') or ''
        enrollment.referral_source = cleaned_data.get('referral_source') or ''

        if commit:
            enrollment.save()

        return enrollment
