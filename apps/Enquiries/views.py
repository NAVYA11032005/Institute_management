from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Enquiry, INDIAN_STATES, REFERRAL_SOURCE_CHOICES
from .forms import EnquiryForm
from apps.courses.models import Course
from apps.students.models import Student


@login_required
def enquiry_list(request):
    """
    List all enquiries with optional search/filter.
    """
    search_query = request.GET.get('q', '').strip()
    enquiries = Enquiry.objects.filter(is_deleted=False).select_related('course').all()
    if search_query:
        enquiries = enquiries.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(course__course_name__icontains=search_query)
        )
    context = {
        'sidebar_active': 'enquiries',
        'enquiries': enquiries.order_by('-created_at'),
        'search_query': search_query,
    }
    return render(request, 'enquiries/enquiry_list.html', context)


@login_required
def enquiry_create(request):
    """
    Create a new enquiry.
    """
    if request.method == 'POST':
        form = EnquiryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Enquiry submitted successfully.")
            return redirect('enquiry_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EnquiryForm()
    context = {
        'sidebar_active': 'enquiries',
        'form': form,
    }
    return render(request, 'enquiries/enquiry_form.html', context)


@login_required
def enquiry_edit(request, pk):
    """
    Edit an existing enquiry.
    """
    enquiry = get_object_or_404(Enquiry, pk=pk, is_deleted=False)
    if request.method == 'POST':
        form = EnquiryForm(request.POST, instance=enquiry)
        if form.is_valid():
            form.save()
            messages.success(request, "Enquiry updated successfully.")
            return redirect('enquiry_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EnquiryForm(instance=enquiry)
    context = {
        'sidebar_active': 'enquiries',
        'form': form,
        'enquiry': enquiry,
    }
    return render(request, 'enquiries/enquiry_form.html', context)


@login_required
def enquiry_delete(request, pk):
    """
    Soft delete an enquiry.
    """
    enquiry = get_object_or_404(Enquiry, pk=pk, is_deleted=False)
    if request.method == 'POST':
        enquiry.delete()  # Implements soft delete via model method
        messages.success(request, "Enquiry moved to Trash successfully.")
        return redirect('enquiry_list')
    return render(request, 'enquiries/enquiry_confirm_delete.html', {'enquiry': enquiry, 'sidebar_active': 'enquiries'})


@login_required
def enquiry_detail(request, pk):
    """
    View details of a single enquiry.
    """
    enquiry = get_object_or_404(Enquiry, pk=pk, is_deleted=False)
    referenced_student = enquiry.get_reference_student()
    context = {
        'sidebar_active': 'enquiries',
        'enquiry': enquiry,
        'referenced_student': referenced_student,
    }
    return render(request, 'enquiries/enquiry_detail.html', context)


@login_required
def enquiry_trash(request):
    """
    View list of soft-deleted enquiries (Trash).
    """
    enquiries = Enquiry.objects.filter(is_deleted=True).order_by('-deleted_at')
    context = {
        'sidebar_active': 'enquiries',
        'enquiries': enquiries,
    }
    return render(request, 'enquiries/enquiry_trash.html', context)


@login_required
def enquiry_restore(request, pk):
    """
    Restore a soft-deleted enquiry from Trash.
    """
    enquiry = get_object_or_404(Enquiry, pk=pk, is_deleted=True)
    if request.method == 'POST':
        enquiry.restore()
        messages.success(request, "✅ Enquiry restored from Trash.")
        return redirect('enquiry_list')
    return render(request, 'enquiries/enquiry_restore_confirm.html', {'enquiry': enquiry, 'sidebar_active': 'enquiries'})


@login_required
def enquiry_permanent_delete(request, pk):
    """
    Permanently delete an enquiry from database.
    """
    enquiry = get_object_or_404(Enquiry, pk=pk)
    if request.method == 'POST':
        enquiry.delete(hard=True)  # Assuming model supports hard delete with this parameter
        messages.success(request, "❌ Enquiry permanently deleted.")
        return redirect('enquiry_trash')
    return render(request, 'enquiries/enquiry_permanent_delete_confirm.html', {'enquiry': enquiry, 'sidebar_active': 'enquiries'})


@login_required
def api_enquiry_referral_lookup(request):
    """
    API endpoint to look up referral details by Student ID.
    """
    student_id = request.GET.get('student_id', '').strip()
    if not student_id:
        return JsonResponse({'error': 'No Student ID provided'}, status=400)
    try:
        student = Student.objects.get(student_id=student_id)
        data = {
            'student_id': student.student_id,
            'full_name': student.full_name,
            'email': student.email,
            'contact': student.contact,
            'state': student.state,
            'city': student.city,
        }
        return JsonResponse(data)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
