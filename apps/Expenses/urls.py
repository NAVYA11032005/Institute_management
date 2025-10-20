from django.urls import path
from . import views

urlpatterns = [
    path('expense_list', views.expense_list, name='expense_list'),
    path('add/', views.expense_create, name='expense_create'),
]
