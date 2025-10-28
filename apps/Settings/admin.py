from django.contrib import admin
from .models import Setting

@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('admission_fee', 'updated_at')
    readonly_fields = ('updated_at',)
