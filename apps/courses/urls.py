from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list, name='courses'),  # This is the main courses page, e.g. /courses/
    path('course_list/', views.course_list, name='course_list'),
    path('create/', views.course_create, name='course_create'),
    path('update/<int:pk>/', views.course_update, name='course_update'),
    path('delete/<int:pk>/', views.course_delete, name='course_delete'),
]
