from django import forms
from .models import Team, INDIAN_STATES

class TeamForm(forms.ModelForm):
    employee_code = forms.CharField(
        label="Employee Code",
        required=False,
        disabled=True
    )
    state = forms.ChoiceField(
        choices=[('', 'Select state')] + INDIAN_STATES,
        required=True,
        label="State"
    )
    # city will be rendered manually in the template

    class Meta:
        model = Team
        fields = [
            'name', 'designation', 'phone', 'email', 'image',
             'state', 'city', 'pincode'
        ]
