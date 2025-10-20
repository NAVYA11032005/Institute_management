from django.contrib import admin
from .models import Team

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'designation', 'phone', 'email', 'employee_code', 'city', 'state', 'pincode')
    search_fields = ('name', 'email', 'employee_code', 'city', 'state')
    list_filter = ('state', 'designation')
