from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from Institute_Management import views  # for login/logout

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.courses.urls')),      # <-- includes courses app URLs
    path('students/', include('apps.students.urls')),
    path('team/', include('apps.Teams.urls')),           # use lowercase if your folder is lowercase
    path('expenses/', include('apps.Expenses.urls')),    # use lowercase if your folder is lowercase
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('enqueries/', include('apps.Enquiries.urls')),  # Ensure this matches the folder name
    path('settings/', include('apps.Settings.urls')),  # Ensure this matches the folder name
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
