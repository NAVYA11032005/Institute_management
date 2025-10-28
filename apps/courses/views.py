from django.shortcuts import render, redirect, get_object_or_404
from .models import Course
from .forms import CourseForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# List all active courses
@login_required
def course_list(request):
    courses = Course.objects.filter(is_deleted=False).order_by('-id')
    context = {
        'courses': courses,
        'sidebar_active': 'courses',
    }
    return render(request, 'courses/course_list.html', context)

# List all deleted (trashed) courses
@login_required
def course_trash(request):
    courses = Course.objects.filter(is_deleted=True).order_by('-deleted_at')
    context = {
        'courses': courses,
        'sidebar_active': 'courses',
    }
    return render(request, 'courses/course_trash.html', context)

# Create a new course
@login_required
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Course created successfully.")
            return redirect('course_list')
    else:
        form = CourseForm()
    context = {
        'form': form,
        'sidebar_active': 'courses',
    }
    return render(request, 'courses/course_form.html', context)

# Update an existing course
@login_required
def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully.")
            return redirect('course_list')
    else:
        form = CourseForm(instance=course)
    context = {
        'form': form,
        'sidebar_active': 'courses',
        'course': course,
    }
    return render(request, 'courses/course_form.html', context)

# Move a course to trash (soft delete)
@login_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk, is_deleted=False)
    if request.method == 'POST':
        course.delete()  # Soft delete (sets is_deleted=True, deleted_at)
        messages.success(request, "Course moved to Trash.")
        return redirect('course_list')
    context = {
        'course': course,
        'sidebar_active': 'courses',
    }
    return render(request, 'courses/course_confirm_delete.html', context)

# Restore a course from trash
@login_required
def course_restore(request, pk):
    course = get_object_or_404(Course, pk=pk, is_deleted=True)
    if request.method == 'POST':
        course.restore()
        messages.success(request, "Course restored from Trash.")
        return redirect('course_list')
    context = {
        'course': course,
        'sidebar_active': 'courses',
    }
    return render(request, 'courses/course_restore_confirm.html', context)
