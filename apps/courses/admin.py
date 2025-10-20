from django.contrib import admin
from .models import Course

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_name', 'course_fee', 'course_duration', 'duration_type')
    list_filter = ('duration_type',)
    search_fields = ('course_name',)
