from django import forms
from .models import Enquiry, INDIAN_STATES, REFERRAL_SOURCE_CHOICES
from apps.courses.models import Course


class EnquiryForm(forms.ModelForm):
    name = forms.CharField(
        label="Name",
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label="Phone",
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        label="Address",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    pincode = forms.CharField(
        label="Pincode",
        max_length=6,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    state = forms.ChoiceField(
        label="State",
        choices=[('', '---------')] + INDIAN_STATES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    city = forms.CharField(
        label="City",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    course = forms.ModelChoiceField(
        label="Course Interested",
        queryset=Course.objects.all().order_by('course_name'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    referral_source = forms.ChoiceField(
        label="How did you find us?",
        required=False,
        choices=[('', '---------')] + REFERRAL_SOURCE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    reference_registration_number = forms.CharField(
        label="Reference Student ID (if any)",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Enter the student ID of the person who referred you (if any)."
    )
    reference_name = forms.CharField(
        label="Reference Name (if not by student ID)",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Enter the name of the person who referred you (if not a student)."
    )
    message = forms.CharField(
        label="Message",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    class Meta:
        model = Enquiry
        fields = [
            'name', 'email', 'phone', 'address', 'pincode', 'state', 'city',
            'course', 'referral_source', 'reference_registration_number', 'reference_name', 'message'
        ]

    # No custom clean() method needed as email and reference fields are optional
