from django.shortcuts import render, redirect, get_object_or_404
from .models import Course
from .forms import CourseForm
from django.contrib.auth.decorators import login_required

# List all courses
@login_required
def course_list(request):
    courses = Course.objects.all()
    context = {
        'courses': courses,
        'sidebar_active': 'courses',
    }
    return render(request, 'courses/course_list.html', context)

# Create a new course
@login_required
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
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
            return redirect('course_list')
    else:
        # Pass initial duration_type for correct label/help text
        initial = {'duration_type': course.duration_type}
        form = CourseForm(instance=course, initial=initial)
    context = {
        'form': form,
        'sidebar_active': 'courses',
    }
    return render(request, 'courses/course_form.html', context)

# Delete a course
@login_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.delete()
        return redirect('course_list')
    context = {
        'course': course,
        'sidebar_active': 'courses',
    }
    return render(request, 'courses/course_confirm_delete.html', context)
