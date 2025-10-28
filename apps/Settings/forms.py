from django import forms
from .models import Setting

class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = ['admission_fee']
        widgets = {
            'admission_fee': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
