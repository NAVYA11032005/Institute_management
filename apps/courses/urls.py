from django.urls import path
from . import views

urlpatterns = [
    # List all active courses (main page: /courses/)
    path('', views.course_list, name='courses'),
    # Alternate list route if you want to use it elsewhere (optional)
    path('course_list/', views.course_list, name='course_list'),
    # Create a new course
    path('create/', views.course_create, name='course_create'),
    # Update an existing course
    path('update/<int:pk>/', views.course_update, name='course_update'),
    # Soft delete (move to trash)
    path('delete/<int:pk>/', views.course_delete, name='course_delete'),

    # Trash (trashed/soft-deleted records)
    path('trash/', views.course_trash, name='course_trash'),
    # Restore a soft-deleted course from trash
    path('trash/<int:pk>/restore/', views.course_restore, name='course_restore'),

    # Optional: Permanent delete from trash (if you add such view)
    # path('trash/<int:pk>/permanent-delete/', views.course_perm_delete, name='course_perm_delete'),
]
