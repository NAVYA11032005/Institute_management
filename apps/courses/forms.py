from django import forms
from .models import Course

class CourseForm(forms.ModelForm):
    DURATION_TYPE_CHOICES = [
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ]

    duration_type = forms.ChoiceField(
        choices=DURATION_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial='months',
        label='Duration Type'
    )

    class Meta:
        model = Course
        fields = ['course_name', 'duration_type', 'course_duration', 'course_fee']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default: months
        duration_type = self.data.get('duration_type') or self.initial.get('duration_type', 'months')
        self._update_duration_field(duration_type)

        # If POST, update label/help text
        if 'duration_type' in self.data:
            self._update_duration_field(self.data['duration_type'])

    def _update_duration_field(self, duration_type):
        if duration_type == 'weeks':
            self.fields['course_duration'].label = 'Course Duration (weeks)'
            self.fields['course_duration'].help_text = 'Enter duration in weeks'
        else:
            self.fields['course_duration'].label = 'Course Duration (months)'
            self.fields['course_duration'].help_text = 'Enter duration in months'

    def save(self, commit=True):
        # Save duration_type to the model
        instance = super().save(commit=False)
        instance.duration_type = self.cleaned_data['duration_type']
        if commit:
            instance.save()
        return instance
