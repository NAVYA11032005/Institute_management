import os
import datetime
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models.functions import TruncMonth
from django.contrib.staticfiles import finders

from dateutil.relativedelta import relativedelta

from .models import Student, StudentEnrollment, Payment
from .forms import StudentEnrollmentForm
from apps.courses.models import Course
from apps.Expenses.models import Expense


# ----------------------------------------------
# STUDENT LIST, TRASH, RESTORE
# ----------------------------------------------

@login_required
def student_list(request):
    order = request.GET.get('order', 'desc')
    students = Student.objects.filter(is_deleted=False).order_by('-student_id')
    enrollments = StudentEnrollment.objects.filter(is_deleted=False).select_related('student', 'course').order_by(
        'enrollment_date' if order == 'asc' else '-enrollment_date'
    )
    pending_dues = enrollments.exclude(payment_status='paid')
    return render(request, 'students/student_list.html', {
        'students': students,
        'enrollments': enrollments,
        'pending_dues': pending_dues,
        'order': order,
        'sidebar_active': 'students',
    })


from apps.Enquiries.models import Enquiry   # Adjust if your enquiry app or model path differs

@login_required
def student_trash(request):
    students = Student.objects.filter(is_deleted=True).order_by('-deleted_at')
    enrollments = StudentEnrollment.objects.filter(is_deleted=True).select_related('student', 'course').order_by('-deleted_at')
    enquiries = Enquiry.objects.filter(is_deleted=True).order_by('-created_at')  # Add is_deleted support in model if not exists

    return render(request, 'students/student_trash.html', {
        'students': students,
        'enrollments': enrollments,
        'enquiries': enquiries,
        'sidebar_active': 'trash',
    })



@login_required
def student_restore(request, pk):
    student = get_object_or_404(Student, student_id=pk, is_deleted=True)
    if request.method == 'POST':
        student.restore()
        student.enrollments.filter(is_deleted=True).update(is_deleted=False, deleted_at=None)
        messages.success(request, "✅ Student and related enrollments restored from trash.")
        return redirect('student_detail', pk=student.student_id)
    return render(request, 'students/restore_confirm.html', {'student': student})


# ----------------------------------------------
# STUDENT DETAIL, CREATE, EDIT, DELETE
# ----------------------------------------------

@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, student_id=pk, is_deleted=False)
    enrollments = student.enrollments.filter(is_deleted=False).select_related('course')
    payments = Payment.objects.filter(enrollment__student=student)
    for enrollment in enrollments:
        enrollment.total_paid = enrollment.amount_paid
        enrollment.amount_remaining = enrollment.final_amount - enrollment.total_paid
        enrollment.status_display = enrollment.get_status_display()
        enrollment.payments_count = enrollment.payments.count()
    return render(request, 'students/student_detail.html', {
        'student': student,
        'enrollments': enrollments,
        'payments': payments,
        'now': timezone.now(),
        'sidebar_active': 'students',
    })


@login_required
def student_form(request):
    if request.method == 'POST':
        form = StudentEnrollmentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                enrollment = form.save(commit=True)
                initial_payment = form.cleaned_data.get('initial_payment')
                if initial_payment and Decimal(initial_payment) > 0:
                    Payment.objects.create(
                        enrollment=enrollment,
                        amount_paid=Decimal(initial_payment),
                        payment_mode=enrollment.payment_mode,
                        payment_date=enrollment.enrollment_date,
                        payment_status='paid' if Decimal(initial_payment) >= enrollment.final_amount else 'partial'
                    )
                messages.success(request, f"✅ Enrollment created for: {enrollment.student.full_name}")
                return redirect('student_detail', pk=enrollment.student.student_id)
            except Exception as e:
                form.add_error(None, f"❌ Error: {e}")
    else:
        form = StudentEnrollmentForm()
    return render(request, 'students/student_form.html', {
        'form': form,
        'courses': Course.objects.all(),
        'sidebar_active': 'students',
    })


@login_required
def student_edit(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk, is_deleted=False)
    form = StudentEnrollmentForm(request.POST or None, request.FILES or None, instance=enrollment)
    if form.is_valid():
        enrollment = form.save()
        return redirect('student_detail', pk=enrollment.student.student_id)
    return render(request, 'students/student_form.html', {'form': form, 'enrollment': enrollment})


@login_required
def student_delete(request, pk):
    student = get_object_or_404(Student, student_id=pk, is_deleted=False)
    if request.method == 'POST':
        student.delete()
        student.enrollments.filter(is_deleted=False).update(is_deleted=True, deleted_at=timezone.now())
        messages.success(request, "✅ Student and related enrollments moved to trash.")
        return redirect('student_list')
    return render(request, 'students/student_confirm_delete.html', {'student': student})


# ----------------------------------------------
# ENROLLMENT VIEWS: DETAIL, UPDATE, DELETE, TRASH, RESTORE
# ----------------------------------------------

@login_required
def enrollment_detail(request, pk):
    enrollment = get_object_or_404(StudentEnrollment.objects.filter(is_deleted=False).select_related('student', 'course'), pk=pk)
    return render(request, 'students/enrollment_detail.html', {'enrollment': enrollment})


@login_required
def enrollment_update(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk, is_deleted=False)
    initial = {
        'referred_by_student_id': enrollment.referred_by.student_id if enrollment.referred_by else '',
        'referred_by_name': enrollment.referred_by_name or '',
    }
    form = StudentEnrollmentForm(request.POST or None, request.FILES or None, instance=enrollment, initial=initial)
    if request.method == 'POST' and form.is_valid():
        updated = form.save()
        messages.success(request, "✅ Enrollment updated.")
        return redirect('student_detail', pk=updated.student.student_id)
    return render(request, 'students/enrollment_form.html', {
        'form': form,
        'enrollment': enrollment,
        'courses': Course.objects.all(),
        'sidebar_active': 'students',
    })


@login_required
def enrollment_delete(request, pk):
    # Try to get enrollment regardless of is_deleted status
    enrollment = get_object_or_404(StudentEnrollment, pk=pk)

    if enrollment.is_deleted:
        messages.warning(request, "Enrollment is already deleted.")
        # Redirecting to enrollment trash or student detail page
        return redirect('student_trash')  # or 'student_detail' if preferred

    student_id = enrollment.student.student_id

    if request.method == 'POST':
        enrollment.delete()  # soft delete
        # Check if student still active
        student_active = enrollment.student.is_deleted == False
        if student_active:
            return redirect('student_detail', pk=student_id)
        else:
            messages.info(request, "Enrollment deleted. The associated student was also moved to Trash.")
            return redirect('student_trash')

    return render(request, 'students/enrollment_confirm_delete.html', {'enrollment': enrollment})


@login_required
def enrollment_trash(request):
    enrollments = StudentEnrollment.objects.filter(is_deleted=True).select_related('student', 'course').order_by('-deleted_at')
    return render(request, 'students/enrollment_trash.html', {
        'enrollments': enrollments,
        'sidebar_active': 'trash',
    })


@login_required
def enrollment_restore(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk, is_deleted=True)
    if request.method == 'POST':
        enrollment.restore()
        messages.success(request, "✅ Enrollment restored from Trash.")
        return redirect('student_detail', pk=enrollment.student.student_id)
    return render(request, 'students/enrollment_restore_confirm.html', {'enrollment': enrollment})


# ----------------------------------------------
# ENROLLMENT: STATUS TOGGLE & MARK COMPLETED
# ----------------------------------------------

@require_POST
@login_required
def enrollment_toggle_status(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk, is_deleted=False)
    enrollment.status = 'deactive' if enrollment.status == 'active' else 'active'
    enrollment.save()
    return JsonResponse({
        'success': True,
        'new_status': enrollment.status,
        'display': enrollment.get_status_display(),
        'badge_class': 'bg-success' if enrollment.status == 'active' else 'bg-danger',
    })


@require_POST
@login_required
def enrollment_mark_completed(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk, is_deleted=False)
    enrollment.status = 'completed'
    enrollment.save()
    return JsonResponse({
        'status': 'completed',
        'certificate_url': f"/students/{enrollment.pk}/certificate/"
    })


# ----------------------------------------------
# PAYMENT VIEW
# ----------------------------------------------

@login_required
def add_payment(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk, is_deleted=False)
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', 0))
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
            payment_mode = request.POST.get('payment_mode')
            payment_date = request.POST.get('payment_date') or timezone.now().date()
            payment = Payment(
                enrollment=enrollment,
                amount_paid=amount,
                payment_mode=payment_mode,
                payment_date=payment_date
            )
            payment.save()
            messages.success(request, "✅ Payment added successfully.")
        except Exception as e:
            messages.error(request, f"❌ Payment failed: {str(e)}")
    return redirect('student_detail', pk=enrollment.student.student_id)


# ----------------------------------------------
# PDF RECEIPTS & CERTIFICATES
# ----------------------------------------------

def fetch_resources(uri, rel=None):
    if uri.startswith(settings.STATIC_URL):
        path = finders.find(uri.replace(settings.STATIC_URL, ""))
        if path:
            return path
    elif uri.startswith(settings.MEDIA_URL):
        return os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, "").lstrip("/"))
    return None


@login_required
def download_receipt(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk, is_deleted=False)
    logo_file_path = finders.find('assets/img/avatars/LOGO_CP_FINAL.png')
    logo_path = f"file://{logo_file_path}" if logo_file_path else ""
    student_photo = ''
    try:
        if enrollment.student.photo:
            student_photo = request.build_absolute_uri(enrollment.student.photo.url)
    except Exception:
        student_photo = ''
    html = render_to_string('students/receipt_pdf.html', {
        'enrollment': enrollment,
        'student': enrollment.student,
        'now': timezone.now(),
        'logo_path': logo_path,
        'student_photo': student_photo
    })
    return HttpResponse(html, content_type='text/html')


@login_required
def download_payment_receipt(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)
    html = render_to_string('students/payment_receipt_pdf.html', {
        'payment': payment,
        'student': payment.enrollment.student,
        'enrollment': payment.enrollment,
        'now': timezone.now()
    })
    return HttpResponse(html, content_type='text/html')


@login_required
def view_certificate(request, pk):
    import re
    enrollment = get_object_or_404(StudentEnrollment, pk=pk, is_deleted=False)
    if not enrollment.certificate_number:
        last_cert = (
            StudentEnrollment.objects
            .exclude(certificate_number__isnull=True)
            .exclude(certificate_number='')
            .order_by('-id')
            .first()
        )
        next_cert_num = 1
        if last_cert and last_cert.certificate_number:
            match = re.search(r'CP-CN-(\d+)', last_cert.certificate_number)
            if match:
                next_cert_num = int(match.group(1)) + 1
        enrollment.certificate_number = f"CP-CN-{next_cert_num:03d}"
        enrollment.save()

    duration = enrollment.course.course_duration or 0
    dtype = getattr(enrollment.course, 'duration_type', 'months')
    if dtype == 'months':
        end_date = enrollment.enrollment_date + relativedelta(months=duration)
    elif dtype == 'weeks':
        end_date = enrollment.enrollment_date + datetime.timedelta(weeks=duration)
    elif dtype == 'days':
        end_date = enrollment.enrollment_date + datetime.timedelta(days=duration)
    else:
        end_date = None

    return render(request, 'students/certificate.html', {
        'student': enrollment.student,
        'enrollment': enrollment,
        'end_date': end_date,
        'now': timezone.now(),
    })


# ----------------------------------------------
# API / AJAX: Student Search & Enrollments
# ----------------------------------------------

@login_required
def api_student_search(request):
    q = request.GET.get('q', '')
    students = Student.objects.filter(
        Q(is_deleted=False),
        Q(full_name__icontains=q) |
        Q(email__icontains=q) |
        Q(contact__icontains=q) |
        Q(student_id__icontains=q)
    )[:10]
    results = [
        {
            'student_id': s.student_id,
            'full_name': s.full_name,
            'email': s.email,
            'contact': s.contact,
            'father_name': s.father_name,
        }
        for s in students
    ]
    return JsonResponse(results, safe=False)


@login_required
def student_enrollments_api(request, student_id):
    student = get_object_or_404(Student, student_id=student_id, is_deleted=False)
    enrollments = student.enrollments.filter(is_deleted=False).select_related('course')
    data = {
        "enrollments": [{
            "id": e.id,
            "course": e.course.course_name,
            "final_amount": float(e.final_amount),
            "amount_paid": float(e.amount_paid),
            "due_date": e.due_date.strftime('%Y-%m-%d') if e.due_date else '',
            "status": e.get_status_display(),
        } for e in enrollments]
    }
    return JsonResponse(data)


# ----------------------------------------------
# SUMMARY REPORTS: Payments, Expenses, Yearly
# ----------------------------------------------

@login_required
def payment_summary(request):
    selected_month = request.GET.get('month', '')
    search = request.GET.get('search', '').strip()
    pay_method = request.GET.get('payment_method', '')
    pay_mode = request.GET.get('payment_mode', '')

    payments = Payment.objects.select_related('enrollment__student', 'enrollment__course').filter(enrollment__is_deleted=False)
    expenses = Expense.objects.select_related('expense_by')

    if selected_month:
        year, month = map(int, selected_month.split('-'))
        payments = payments.filter(payment_date__year=year, payment_date__month=month)
        expenses = expenses.filter(date__year=year, date__month=month)

    if search:
        payments = payments.filter(
            Q(enrollment__student__full_name__icontains=search) |
            Q(enrollment__course__course_name__icontains=search) |
            Q(payment_mode__icontains=search)
        )

    if pay_method:
        payments = payments.filter(enrollment__payment_method=pay_method)

    if pay_mode:
        payments = payments.filter(payment_mode=pay_mode)

    total_payment_collected = payments.aggregate(total=Sum('amount_paid'))['total'] or 0
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    net_total = max(total_payment_collected - total_expenses, 0)

    return render(request, 'students/payment_summary.html', {
        'payments': payments,
        'expenses': expenses,
        'total_payment_collected': total_payment_collected,
        'total_expenses': total_expenses,
        'net_total': net_total,
        'sidebar_active': 'payments',
        'selected_month': selected_month,
    })


@login_required
def expense_summary(request):
    selected_month = request.GET.get('month', '')
    year, month = None, None
    try:
        year, month = map(int, selected_month.split('-'))
    except Exception:
        pass

    expenses = Expense.objects.all()
    payments = Payment.objects.select_related('enrollment', 'enrollment__student').filter(enrollment__is_deleted=False)

    if year and month:
        expenses = expenses.filter(date__year=year, date__month=month)
        payments = payments.filter(payment_date__year=year, payment_date__month=month)

    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_payments = payments.aggregate(total=Sum('amount_paid'))['total'] or 0
    net_total = max(total_payments - total_expenses, 0)

    return render(request, 'students/expense_summary.html', {
        'sidebar_active': 'expenses',
        'expenses': expenses.order_by('-date'),
        'total_expenses': total_expenses,
        'total_payment_collected': total_payments,
        'net_total': net_total,
        'selected_month': selected_month,
    })


@login_required
def yearly_summary(request):
    current_year = timezone.now().year
    year = int(request.GET.get("year", current_year))
    year_range = range(current_year - 5, current_year + 1)

    payments = Payment.objects.filter(payment_date__year=year, enrollment__is_deleted=False)
    expenses = Expense.objects.filter(date__year=year)

    total_payments = payments.aggregate(total=Sum('amount_paid'))['total'] or 0
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    net_total = max(total_payments - total_expenses, 0)

    payments_by_month = payments.annotate(month=TruncMonth('payment_date')).values('month').annotate(total=Sum('amount_paid')).order_by('month')
    expenses_by_month = expenses.annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month')

    return render(request, 'students/yearly_summary.html', {
        'sidebar_active': 'yearly',
        'year': year,
        'year_range': year_range,
        'yearly_payments': total_payments,
        'yearly_expenses': total_expenses,
        'yearly_net': net_total,
        'payments_by_month': list(payments_by_month),
        'expenses_by_month': list(expenses_by_month),
    })
