from django.urls import path
from . import views

urlpatterns = [
    path('', views.expense_list, name='expense_list'),                    # List all active expenses
    path('add/', views.expense_create, name='expense_create'),            # Add a new expense
    path('edit/<int:pk>/', views.expense_edit, name='expense_edit'),      # Edit an existing expense
    path('delete/<int:pk>/', views.expense_delete, name='expense_delete'),# Soft delete an expense

    path('trash/', views.expense_trash, name='expense_trash'),            # View trashed (soft deleted) expenses
    path('trash/<int:pk>/restore/', views.expense_restore, name='expense_restore'),  # Restore from trash

    # Optional permanent delete, implement view if needed
    # path('trash/<int:pk>/permanent-delete/', views.expense_permanent_delete, name='expense_permanent_delete'),
]
