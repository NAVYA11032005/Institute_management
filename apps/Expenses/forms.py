from django import forms
from .models import Expense

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['expense_name', 'expense_by', 'amount', 'remarks']
        widgets = {
            'expense_name': forms.TextInput(attrs={'class': 'form-control'}),
            'expense_by': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
