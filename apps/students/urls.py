# students/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Student routes
    path('', views.student_list, name='student_list'),
    path('create/', views.student_form, name='student_create'),
    path('<int:pk>/detail/', views.student_detail, name='student_detail'),
    path('<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('<int:pk>/delete/', views.student_delete, name='student_delete'),
    # Optional update alias if needed; else remove duplicate below
    # path('<int:pk>/edit/', views.student_form, name='student_update'),

    # Enrollment routes
    path('trash/enrollment/<int:pk>/restore/', views.enrollment_restore, name='enrollment_restore'),
    path('<int:pk>/enrollment/', views.enrollment_detail, name='enrollment_detail'),
    path('<int:pk>/enrollment/update/', views.enrollment_update, name='enrollment_update'),
    path('<int:pk>/enrollment/delete/', views.enrollment_delete, name='enrollment_delete'),
    path('<int:pk>/enrollment/complete/', views.enrollment_mark_completed, name='enrollment_mark_completed'),
    path('<int:pk>/enrollment/toggle-status/', views.enrollment_toggle_status, name='enrollment_toggle_status'),

    # Payments routes
    path('<int:pk>/add-payment/', views.add_payment, name='add_payment'),

    # Trash & Restore routes
    path('trash/', views.student_trash, name='student_trash'),
    path('trash/<str:pk>/restore/', views.student_restore, name='student_restore'),

    # API endpoints
    path('api/student-search/', views.api_student_search, name='api_student_search'),
    path('api/student-enrollments/<str:student_id>/', views.student_enrollments_api, name='student_enrollments_api'),

    # Certificates & Receipts
    path('<int:pk>/certificate/', views.view_certificate, name='view_certificate'),
    path('<int:pk>/receipt/', views.download_receipt, name='download_receipt'),
    path('payment/<int:payment_id>/receipt/', views.download_payment_receipt, name='download_payment_receipt'),

    # Summary reports
    path('payments/summary/', views.payment_summary, name='payment_summary'),
    path('expenses/summary/', views.expense_summary, name='expense_summary'),
    path('yearly-summary/', views.yearly_summary, name='yearly_summary'),
]
