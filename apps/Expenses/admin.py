from django.contrib import admin
from .models import Expense

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('expense_name', 'expense_by', 'amount', 'date')
    search_fields = ('expense_name', 'expense_by__name')
    list_filter = ('expense_by', 'date')
