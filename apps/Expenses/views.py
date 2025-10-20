from django.shortcuts import render, redirect
from .models import Expense
from .forms import ExpenseForm

def expense_list(request):
    expenses = Expense.objects.all().order_by('-date')
    total_expense = sum(e.amount for e in expenses)
    return render(request, 'expenses/expense_list.html', {
        'expenses': expenses,
        'total_expense': total_expense,
        'sidebar_active': 'expense_list',  # Ensures sidebar highlighting
    })

def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'sidebar_active': 'expense_list',  # Ensures sidebar highlighting
    })
