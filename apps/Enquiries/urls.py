from django.urls import path
from . import views

urlpatterns = [
    # Enquiry CRUD
    path('', views.enquiry_list, name='enquiry_list'),
    path('create/', views.enquiry_create, name='enquiry_create'),
    path('edit/<int:pk>/', views.enquiry_edit, name='enquiry_edit'),
    path('delete/<int:pk>/', views.enquiry_delete, name='enquiry_delete'),
    path('detail/<int:pk>/', views.enquiry_detail, name='enquiry_detail'),

    # Trash and Restore
    path('trash/', views.enquiry_trash, name='enquiry_trash'),
    path('trash/<int:pk>/restore/', views.enquiry_restore, name='enquiry_restore'),
    path('trash/<int:pk>/permanent-delete/', views.enquiry_permanent_delete, name='enquiry_permanent_delete'),

    # API endpoint
    path('api/referral-lookup/', views.api_enquiry_referral_lookup, name='api_enquiry_referral_lookup'),
]
