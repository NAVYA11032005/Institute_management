from django.urls import path
from .views import setting_edit

urlpatterns = [
    path('edit/', setting_edit, name='setting_edit'),
]
