from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Expense
from .forms import ExpenseForm


@login_required
def expense_list(request):
    # Show only active (non-deleted) expenses
    expenses = Expense.objects.filter(is_deleted=False).order_by('-date')
    total_expense = sum(e.amount for e in expenses)

    context = {
        'expenses': expenses,
        'total_expense': total_expense,
        'sidebar_active': 'expense',
    }
    return render(request, 'expenses/expense_list.html', context)


@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense added successfully.")
            return redirect('expense_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ExpenseForm()

    context = {
        'form': form,
        'sidebar_active': 'expense',
    }
    return render(request, 'expenses/expense_form.html', context)


@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk, is_deleted=False)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense updated successfully.")
            return redirect('expense_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ExpenseForm(instance=expense)

    context = {
        'form': form,
        'expense': expense,
        'sidebar_active': 'expense',
    }
    return render(request, 'expenses/expense_form.html', context)


@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk, is_deleted=False)

    if request.method == 'POST':
        # Soft delete: mark as deleted
        expense.is_deleted = True
        expense.deleted_at = timezone.now()
        expense.save()
        messages.success(request, "Expense moved to trash.")
        return redirect('expense_list')

    context = {
        'expense': expense,
        'sidebar_active': 'expense',
    }
    return render(request, 'expenses/expense_confirm_delete.html', context)


@login_required
def expense_trash(request):
    # Show expenses that are moved to trash
    expenses = Expense.objects.filter(is_deleted=True).order_by('-deleted_at')

    context = {
        'expenses': expenses,
        'sidebar_active': 'expense_trash',
    }
    return render(request, 'expenses/expense_list.html', context)


@login_required
def expense_restore(request, pk):
    expense = get_object_or_404(Expense, pk=pk, is_deleted=True)

    if request.method == 'POST':
        expense.is_deleted = False
        expense.deleted_at = None
        expense.save()
        messages.success(request, "Expense restored successfully.")
        return redirect('expense_list')

    context = {
        'expense': expense,
        'sidebar_active': 'expense_trash',
    }
    return render(request, 'expenses/expense_restore_confirm.html', context)

