from django.urls import path
from . import views

urlpatterns = [
    path('team/list/', views.team_list, name='team_list'),
    path('team/add/', views.team_create, name='team_create'),
    path('team/<int:pk>/', views.team_member_detail, name='team_member_detail'),
    path('team/<int:pk>/edit/', views.team_update, name='team_update'),
    path('team/<int:pk>/delete/', views.team_delete, name='team_delete'),
    
    # Add this for restore from trash:
    path('team/<int:pk>/restore/', views.team_restore, name='team_restore'),
]
