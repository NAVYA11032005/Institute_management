import datetime
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q, Sum
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.db.models.functions import TruncMonth
from django.contrib.staticfiles import finders

from dateutil import relativedelta

from .models import Student, StudentEnrollment, Payment
from .forms import StudentEnrollmentForm
from apps.courses.models import Course
from apps.Expenses.models import Expense
from apps.Enquiries.models import Enquiry
from apps.Teams.models import Team

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from decimal import Decimal
from .models import Student, StudentEnrollment

def _annotate_enrollments(enrollments):
    for enrollment in enrollments:
        enrollment.admission_fee_display = enrollment.admission_fee
        enrollment.admission_fee_paid_display = enrollment.admission_fee_paid
        enrollment.admission_fee_remaining_display = enrollment.admission_fee_remaining
        course_fee = max(enrollment.course.course_fee - enrollment.discount, Decimal('0.00'))
        enrollment.course_fee_display = course_fee
        enrollment.course_fee_paid_display = enrollment.course_fee_paid
        enrollment.course_fee_remaining_display = enrollment.course_fee_remaining

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required

@login_required
def student_list(request):
    order = request.GET.get('order', 'desc')
    students = Student.objects.filter(is_deleted=False).order_by('-student_id')
    enrollments_qs = StudentEnrollment.objects.filter(is_deleted=False).select_related('student', 'course')
    enrollments_qs = enrollments_qs.order_by('enrollment_date' if order == 'asc' else '-enrollment_date')

    # Optional: annotate your enrollments if necessary
    _annotate_enrollments(enrollments_qs)

    paginator = Paginator(enrollments_qs, 10)  # 10 per page
    page_number = request.GET.get('page')
    try:
        enrollments = paginator.page(page_number)
    except PageNotAnInteger:
        enrollments = paginator.page(1)
    except EmptyPage:
        enrollments = paginator.page(paginator.num_pages)

    return render(request, 'students/student_list.html', {
        'students': students,
        'enrollments': enrollments,  # This must be the Page object, NOT a QuerySet
        'order': order,
        'sidebar': 'students',
        'page_obj': enrollments,
        'paginator': paginator,
    })



@login_required
def student_trash(request):
    students = Student.objects.filter(is_deleted=True).order_by('-deleted_at')
    enrollments = StudentEnrollment.objects.filter(is_deleted=True).select_related('student', 'course').order_by('-deleted_at')
    enquiries = Enquiry.objects.filter(is_deleted=True).order_by('created_at')
    courses = Course.objects.filter(is_deleted=True).order_by('-deleted_at')
    expenses = Expense.objects.filter(is_deleted=True).order_by('-deleted_at')
    teams = Team.objects.filter(is_deleted=True).order_by('-deleted_at')
    return render(request, 'students/student_trash.html', {
        'students': students,
        'enrollments': enrollments,
        'enquiries': enquiries,
        'courses': courses,
        'expenses': expenses,
        'teams': teams,
        'sidebar': 'trash',
    })


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, student_id=pk, is_deleted=False)
    enrollments = student.enrollments.filter(is_deleted=False).select_related('course')
    payments = Payment.objects.filter(enrollment__student=student)
    _annotate_enrollments(enrollments)
    for e in enrollments:
        e.total_paid = e.admission_fee_paid + e.course_fee_paid
        e.remaining_amount = e.admission_fee_remaining + e.course_fee_remaining
        e.status_display = e.get_status_display()
        e.payments_count = e.payments.count()
    return render(request, 'students/student_detail.html', {
        'student': student,
        'enrollments': enrollments,
        'payments': payments,
        'now': timezone.now(),
        'sidebar': 'students',
    })


@login_required
def student_form(request):
    if request.method == 'POST':
        form = StudentEnrollmentForm(request.POST, request.FILES)
        if form.is_valid():
            enrollment = form.save(commit=False)
            student = enrollment.student
            if not student.pk:
                student.save()
            enrollment.student = student
            enrollment.save()
            initial_payment = form.cleaned_data.get('initial_payment') or Decimal('0.00')
            payment_mode = enrollment.payment_mode or 'cash'
            enrollment.apply_initial_payment(initial_payment, payment_mode)
            messages.success(request, f"✅ Enrollment created for: {enrollment.student.full_name}")
            return redirect('student_detail', enrollment.student_id)
    else:
        form = StudentEnrollmentForm()
    return render(request, 'students/student_form.html', {
        'form': form,
        'courses': Course.objects.filter(is_deleted=False),
        'sidebar': 'students',
    })


@login_required
def student_edit(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk)

    if request.method == 'POST':
        form = StudentEnrollmentForm(request.POST, request.FILES, instance=enrollment)
        if form.is_valid():
            # Manually update student fields from POST data before saving enrollment
            student = enrollment.student
            student.full_name = request.POST.get('full_name', student.full_name)
            student.father_name = request.POST.get('father_name', student.father_name)
            student.gender = request.POST.get('gender', student.gender)
            student.dob = request.POST.get('dob', student.dob)
            student.email = request.POST.get('email', student.email)
            student.contact = request.POST.get('contact', student.contact)
            student.emergency_contact_number = request.POST.get('emergency_contact_number', student.emergency_contact_number)
            student.address = request.POST.get('address', student.address)
            student.state = request.POST.get('state', student.state)
            student.city = request.POST.get('city', student.city)
            student.pincode = request.POST.get('pincode', student.pincode)
            student.referral_source = request.POST.get('referral_source', student.referral_source)

            # Handle referred_by (ForeignKey)
            referred_by_id = request.POST.get('referred_by')
            if referred_by_id:
                try:
                    student.referred_by = Student.objects.get(pk=referred_by_id)
                except Student.DoesNotExist:
                    student.referred_by = None
            else:
                student.referred_by = None

            student.referred_by_name = request.POST.get('referred_by_name', student.referred_by_name)

            student.save()

            enrollment = form.save(commit=False)
            enrollment.student = student
            enrollment.save()

            messages.success(request, "✅ Enrollment updated successfully")
            return redirect('student_detail', enrollment.student_id)
    else:
        # Inject student fields into form initial data for pre-filling
        student = enrollment.student
        initial_student_data = {
            'full_name': student.full_name,
            'father_name': student.father_name,
            'gender': student.gender,
            'dob': student.dob,
            'email': student.email,
            'contact': student.contact,
            'emergency_contact_number': student.emergency_contact_number,
            'address': student.address,
            'state': student.state,
            'city': student.city,
            'pincode': student.pincode,
            'referral_source': student.referral_source,
            'referred_by': student.referred_by_id,
            'referred_by_name': student.referred_by_name,
        }
        form = StudentEnrollmentForm(instance=enrollment, initial=initial_student_data)

    courses = Course.objects.filter(is_deleted=False)  # For dropdown JS

    return render(request, 'students/student_form.html', {
        'form': form,
        'enrollment': enrollment,
        'sidebar': 'students',
        'courses': courses,
    })


@login_required
def student_delete(request, pk):
    student = get_object_or_404(Student, student_id=pk, is_deleted=False)
    if request.method == 'POST':
        student.delete()
        student.enrollments.filter(is_deleted=False).update(is_deleted=True, deleted_at=timezone.now())
        messages.success(request, "✅ Student and related enrollments moved to trash.")
        return redirect('student_list')
    return render(request, 'students/student_confirm_delete.html', {
        'student': student,
        'sidebar': 'students',
    })


@login_required
def enrollment_detail(request, pk):
    enrollment = get_object_or_404(StudentEnrollment.objects.select_related('student', 'course'), pk=pk, is_deleted=False)
    admission_pays = enrollment.payments.filter(remarks__iexact='Admission Fee')
    course_pays = enrollment.payments.filter(remarks__iexact='Course Fee')

    all_payments = []
    for e in enrollment.student.enrollments.all():
        all_payments.extend(e.payments.all())

    return render(request, 'students/enrollment_detail.html', {
        'enrollment': enrollment,
        'admission_payments': admission_pays,
        'course_payments': course_pays,
        'all_payments': all_payments,
        'sidebar': 'students',
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import StudentEnrollment
from .forms import StudentEnrollmentForm
from apps.courses.models import Course


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.courses.models import Course
from .forms import StudentEnrollmentForm
from .models import StudentEnrollment

@login_required
def enrollment_update(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk, is_deleted=False)

    if request.method == "POST":
        form = StudentEnrollmentForm(request.POST, request.FILES, instance=enrollment)
        if form.is_valid():
            enrollment = form.save(commit=False)
            # Save student if new
            if enrollment.student.pk is None:
                enrollment.student.save()
            enrollment.save()
            messages.success(request, "✅ Enrollment updated successfully")
            return redirect('student_detail', enrollment.student_id)
    else:
        # Manually prepare initial data for related student fields
        student = enrollment.student
        student_initial = {
            'full_name': student.full_name,
            'father_name': student.father_name,
            'gender': student.gender,
            'dob': student.dob,
            'email': student.email,
            'contact': student.contact,
            'emergency_contact_number': student.emergency_contact_number,
            'address': student.address,
            'state': student.state,
            'city': student.city,
            'pincode': student.pincode,
            'referral_source': student.referral_source,
            'referred_by': student.referred_by_id,
            'referred_by_name': student.referred_by_name,
            # Add any other student fields displayed in your form
        }
        form = StudentEnrollmentForm(instance=enrollment, initial=student_initial)

    courses = Course.objects.filter(is_deleted=False)

    return render(request, 'students/enrollment_form.html', {
        'form': form,
        'enrollment': enrollment,
        'courses': courses,
        'sidebar': 'students',
    })


@login_required
def enrollment_delete(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk)
    if enrollment.is_deleted:
        messages.warning(request, "Already deleted.")
        return redirect('student_trash')  # Make sure 'student_trash' url name exists
    if request.method == 'POST':
        enrollment.delete()
        remaining = StudentEnrollment.objects.filter(student=enrollment.student, is_deleted=False).count()
        if remaining == 0:
            messages.info(request, "No active enrollments left: student moved to trash.")
            return redirect('student_trash')  # Make sure url exists
        else:
            return redirect('student_detail', enrollment.student_id)
    return render(request, 'students/enrollment_confirm_delete.html', {
        'enrollment': enrollment,
        'sidebar': 'students',
    })


@login_required
def enrollment_restore(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk, is_deleted=True)
    if request.method == 'POST':
        enrollment.restore()
        messages.success(request, "✅ Enrollment restored")
        return redirect('student_detail', enrollment.student_id)
    return render(request, 'students/enrollment_restore_confirm.html', {
        'enrollment': enrollment,
        'sidebar': 'students',
    })


@require_POST
@login_required
def enrollment_toggle_status(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk, is_deleted=False)
    enrollment.status = 'deactive' if enrollment.status == 'active' else 'active'
    enrollment.save()
    return JsonResponse({
        "success": True,
        "new_status": enrollment.status,
        "display": enrollment.get_status_display(),
        "badge_class": "badge-success" if enrollment.status == "active" else "badge-danger",
    })


@require_POST
@login_required
def enrollment_mark_completed(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk, is_deleted=False)
    enrollment.status = 'completed'
    enrollment.save()
    return JsonResponse({
        'status': 'completed',
        'message': 'Enrollment marked as completed',
        'certificate_url': f'/students/{pk}/certificate/',
    })


@require_POST
@login_required
def add_payment(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk)
    try:
        amount = Decimal(request.POST.get('amount', '0'))
        if amount <= 0:
            raise ValueError('Amount must be positive.')

        payment_mode = request.POST.get('payment_mode')
        payment_type = request.POST.get('payment_type')
        payment_date_str = request.POST.get('payment_date')

        # Determine payment_date
        if payment_date_str:
            # If user submitted a payment date, parse that
             payment_date = enrollment.enrollment_date
        else:
            # If no date submitted, use current date as fallback
            payment_date = enrollment.enrollment_date

        # NEW LOGIC: If this is the FIRST payment on this enrollment,
        # override payment_date to enrollment.enrollment_date regardless of user input.
        existing_payments_count = enrollment.payments.count()
        if existing_payments_count == 0:
            payment_date = enrollment.enrollment_date

        # Validate amount against dues
        if payment_type == 'Admission Fee':
            due = enrollment.admission_fee_remaining
            if due <= 0:
                messages.error(request, 'Admission fee already settled.')
                return redirect('student_detail', enrollment.student_id)
            if amount > due:
                messages.error(request, f"Amount exceeds due admission fee of ₹{due}.")
                return redirect('student_detail', enrollment.student_id)

        elif payment_type == 'Course Fee':
            due = enrollment.course_fee_remaining
            if due <= 0:
                messages.error(request, 'Course fee already settled.')
                return redirect('student_detail', enrollment.student_id)
            if amount > due:
                messages.error(request, f"Amount exceeds due course fee of ₹{due}.")
                return redirect('student_detail', enrollment.student_id)
        else:
            messages.error(request, 'Invalid payment type.')
            return redirect('student_detail', enrollment.student_id)

        # Create payment with the determined payment_date
        Payment.objects.create(
            enrollment=enrollment,
            amount=amount,
            amount_paid=amount,
            payment_mode=payment_mode,
            payment_date=payment_date,
            remarks=payment_type,
            payment_status='paid',
        )

        enrollment.save()
        messages.success(request, 'Payment added successfully.')

    except Exception as e:
        messages.error(request, f"Error adding payment: {str(e)}")

    return redirect('student_detail', enrollment.student_id)



@login_required
def download_receipt(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk, is_deleted=False)
    logo_path = None
    logo_file = finders.find('assets/img/logo.png')
    if logo_file:
        logo_path = f'file://{logo_file}'

    student_photo = ''
    try:
        if enrollment.student.photo:
            student_photo = request.build_absolute_uri(enrollment.student.photo.url)
    except Exception:
        pass

    html = render_to_string('students/receipt_pdf.html', {
        'enrollment': enrollment,
        'student': enrollment.student,
        'now': timezone.now(),
        'logo_path': logo_path,
        'student_photo': student_photo,
    })
    return HttpResponse(html, content_type='text/html')


@login_required
def download_payment_receipt(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)
    html = render_to_string('students/payment_receipt_pdf.html', {
        'payment': payment,
        'student': payment.enrollment.student,
        'enrollment': payment.enrollment,
        'now': timezone.now(),
    })
    return HttpResponse(html, content_type='text/html')


from decimal import Decimal
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

@login_required
def payment_summary(request):
    selected_month = request.GET.get('month', None)
    search = request.GET.get('search', '').strip()
    pay_method = request.GET.get('payment_method')
    pay_mode = request.GET.get('payment_mode')

    # Base payments queryset on enrollments not deleted
    payments = Payment.objects.filter(enrollment__is_deleted=False).select_related(
        'enrollment', 'enrollment__student', 'enrollment__course'
    )
    expenses = Expense.objects.all()

    # Filter payments and expenses by selected month (payment_date & expense date)
    if selected_month:
        try:
            year, month = map(int, selected_month.split('-'))
            payments = payments.filter(payment_date__year=year, payment_date__month=month)
            expenses = expenses.filter(date__year=year, date__month=month)
        except Exception:
            pass

    # Additional search filters on payments
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

    # Use enrollment.enrollment_date for guidance if needed (example: filter payments after enrollment date)
    # Uncomment if required:
    # payments = payments.filter(payment_date__gte=F('enrollment__enrollment_date'))

    # Total sums
    total_collected = payments.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    net_total = max(total_collected - total_expenses, Decimal('0.00'))

    # Group payments and expenses by month for reports
    payments_by_month = payments.annotate(
        month=TruncMonth('payment_date')
    ).values('month').annotate(total=Sum('amount_paid')).order_by('month')

    expenses_by_month = expenses.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(total=Sum('amount')).order_by('month')

    return render(request, 'students/payment_summary.html', {
        'payments': payments,
        'expenses': expenses,
        'total_collected': total_collected,
        'total_expenses': total_expenses,
        'net_total': net_total,
        'payments_by_month': list(payments_by_month),
        'expenses_by_month': list(expenses_by_month),
        'selected_month': selected_month,
        'sidebar': 'payments',
    })


@login_required
def expense_summary(request):
    selected_month = request.GET.get('month')
    year = None
    month = None
    if selected_month:
        try:
            year, month = map(int, selected_month.split('-'))
        except Exception:
            year = month = None

    expenses = Expense.objects.all()
    payments = Payment.objects.filter(enrollment__is_deleted=False)

    if year and month:
        expenses = expenses.filter(date__year=year, date__month=month)
        payments = payments.filter(payment_date__year=year, payment_date__month=month)

    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_payments = payments.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    net_total = max(total_payments - total_expenses, Decimal('0.00'))

    return render(request, 'expenses/expense_summary.html', {
        'expenses': expenses.order_by('-date'),
        'total_expenses': total_expenses,
        'total_payments': total_payments,
        'net_total': net_total,
        'sidebar': 'expenses',
    })


@login_required
def yearly_summary(request):
    year = request.GET.get('year')
    current_year = timezone.now().year
    try:
        year = int(year)
    except Exception:
        year = current_year
    years_range = list(range(current_year - 5, current_year + 1))

    payments = Payment.objects.filter(enrollment__is_deleted=False, payment_date__year=year)
    expenses = Expense.objects.filter(date__year=year)

    total_collected = payments.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    net_total = max(total_collected - total_expenses, Decimal('0.00'))

    payments_by_month = payments.annotate(month=TruncMonth('payment_date')).values('month').annotate(total=Sum('amount_paid')).order_by('month')
    expenses_by_month = expenses.annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month')

    return render(request, 'students/yearly_summary.html', {
        'year': year,
        'years_range': years_range,
        'total_collected': total_collected,
        'total_expenses': total_expenses,
        'net_total': net_total,
        'payments_by_month': list(payments_by_month),
        'expenses_by_month': list(expenses_by_month),
        'sidebar': 'yearly',
    })


@login_required
def student_restore(request, pk):
    student = get_object_or_404(Student, student_id=pk, is_deleted=True)
    if request.method == 'POST':
        student.restore()
        student.enrollments.filter(is_deleted=True).update(is_deleted=False, deleted_at=None)
        messages.success(request, '✅ Student and related enrollments restored.')
        return redirect('student_detail', student.student_id)
    return render(request, 'students/restore_confirm.html', {
        'student': student,
        'sidebar': 'students',
    })

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import StudentEnrollment


@require_POST
@login_required
def enrollment_toggle_status(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk, is_deleted=False)
    enrollment.status = 'deactive' if enrollment.status == 'active' else 'active'
    enrollment.save()
    return JsonResponse({
        "success": True,
        "new_status": enrollment.status,
        "display": enrollment.get_status_display(),
        "badge_class": "badge-success" if enrollment.status == "active" else "badge-danger",
    })
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_list_or_404
from django.db.models import Q

from .models import Student

@login_required
def api_student_search(request):
    q = request.GET.get('q', '')
    if not q:
        return JsonResponse([], safe=False)

    students = Student.objects.filter(
        Q(full_name__icontains=q) |
        Q(email__icontains=q) |
        Q(contact__icontains=q) |
        Q(student_id__icontains=q),
        is_deleted=False
    )[:10]

    results = [{
        'student_id': s.student_id,
        'full_name': s.full_name,
        'email': s.email,
        'contact': s.contact,
        'father_name': s.father_name,
    } for s in students]

    return JsonResponse(results, safe=False)


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import Student

@login_required
def student_enrollments_api(request, student_id):
    student = get_object_or_404(Student, student_id=student_id, is_deleted=False)
    enrollments = student.enrollments.filter(is_deleted=False).select_related('course')

    data = {
        "enrollments": [
            {
                "id": e.id,
                "course": e.course.course_name,
                "final_amount": float(e.final_amount),
                "paid": float(e.admission_fee_paid + e.course_fee_paid),
                "due": float(e.admission_fee_remaining + e.course_fee_remaining),
                "due_date": e.due_date.strftime("%Y-%m-%d") if e.due_date else "",
                "status": e.get_status_display(),
            }
            for e in enrollments
        ]
    }
    return JsonResponse(data)
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from dateutil import relativedelta
import datetime

from .models import StudentEnrollment

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import datetime
import re
from dateutil import relativedelta
from .models import StudentEnrollment

@login_required
def view_certificate(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk, is_deleted=False)

    # Assign certificate number if none exists
    if not enrollment.certificate_number:
        last_cert = StudentEnrollment.objects.exclude(certificate_number__isnull=True)\
            .exclude(certificate_number='').order_by('-id').first()
        next_num = 1
        if last_cert:
            match = re.search(r"CP-CN-(\d+)", last_cert.certificate_number)
            if match:
                next_num = int(match.group(1)) + 1
        enrollment.certificate_number = f"CP-CN-{next_num:03d}"
        enrollment.save()

    # Use getattr with fallback to avoid AttributeError if 'duration' missing
    duration = getattr(enrollment.course, 'course_duration', 0) or 0
    dtype = getattr(enrollment.course, "duration_type", "months")

    if dtype == "months":
        end_date = enrollment.enrollment_date + relativedelta.relativedelta(months=duration)
    elif dtype == "weeks":
        end_date = enrollment.enrollment_date + datetime.timedelta(weeks=duration)
    elif dtype == "days":
        end_date = enrollment.enrollment_date + datetime.timedelta(days=duration)
    else:
        end_date = None

    return render(request, "students/certificate.html", {
        "student": enrollment.student,
        "enrollment": enrollment,
        "end_date": end_date,
        "now": timezone.now(),
    })
import datetime
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q, Sum
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.db.models.functions import TruncMonth
from django.contrib.staticfiles import finders

from dateutil import relativedelta

from .models import Student, StudentEnrollment, Payment
from .forms import StudentEnrollmentForm
from apps.courses.models import Course
from apps.Expenses.models import Expense
from apps.Enquiries.models import Enquiry
from apps.Teams.models import Team


def _annotate_enrollments(enrollments):
    for enrollment in enrollments:
        enrollment.admission_fee_display = enrollment.admission_fee
        enrollment.admission_fee_paid_display = enrollment.admission_fee_paid
        enrollment.admission_fee_remaining_display = enrollment.admission_fee_remaining

        course_fee = max(enrollment.course.course_fee - enrollment.discount, Decimal('0.00'))
        enrollment.course_fee_display = course_fee
        enrollment.course_fee_paid_display = enrollment.course_fee_paid
        enrollment.course_fee_remaining_display = enrollment.course_fee_remaining


@login_required
def student_list(request):
    order = request.GET.get('order', 'desc')
    students = Student.objects.filter(is_deleted=False).order_by('-student_id')
    enrollments = StudentEnrollment.objects.filter(is_deleted=False).select_related('student', 'course')
    enrollments = enrollments.order_by('student_id' if order == 'asc' else '-student_id')
    pending = enrollments.exclude(payment_status='paid')
    _annotate_enrollments(enrollments)
    _annotate_enrollments(pending)
    return render(request, 'students/student_list.html', {
        'students': students,
        'enrollments': enrollments,
        'pending': pending,
        'order': order,
        'sidebar': 'students',
    })

@login_required
def student_trash(request):
    students = Student.objects.filter(is_deleted=True).order_by('-deleted_at')
    enrollments = StudentEnrollment.objects.filter(is_deleted=True).select_related('student', 'course').order_by('-deleted_at')
    enquiries = Enquiry.objects.filter(is_deleted=True).order_by('created_at')
    courses = Course.objects.filter(is_deleted=True).order_by('-deleted_at')
    expenses = Expense.objects.filter(is_deleted=True).order_by('-deleted_at')
    teams = Team.objects.filter(is_deleted=True).order_by('-deleted_at')
    return render(request, 'students/student_trash.html', {
        'students': students,
        'enrollments': enrollments,
        'enquiries': enquiries,
        'courses': courses,
        'expenses': expenses,
        'teams': teams,
        'sidebar': 'trash',
    })

@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, student_id=pk, is_deleted=False)
    enrollments = student.enrollments.filter(is_deleted=False).select_related('course')
    payments = Payment.objects.filter(enrollment__student=student)
    _annotate_enrollments(enrollments)
    for e in enrollments:
        e.total_paid = e.admission_fee_paid + e.course_fee_paid
        e.remaining_amount = e.admission_fee_remaining + e.course_fee_remaining
        e.status_display = e.get_status_display()
        e.payments_count = e.payments.count()
    return render(request, 'students/student_detail.html', {
        'student': student,
        'enrollments': enrollments,
        'payments': payments,
        'now': timezone.now(),
        'sidebar': 'students',
    })

@login_required
def student_form(request):
    if request.method == 'POST':
        form = StudentEnrollmentForm(request.POST, request.FILES)
        if form.is_valid():
            enrollment = form.save(commit=False)
            student = enrollment.student
            if not student.pk:
                student.save()
            enrollment.student = student
            enrollment.save()
            initial_payment = form.cleaned_data.get('initial_payment') or Decimal('0.00')
            payment_mode = enrollment.payment_mode or 'cash'
            enrollment.apply_initial_payment(initial_payment, payment_mode)
            messages.success(request, f"✅ Enrollment created for: {enrollment.student.full_name}")
            return redirect('student_detail', enrollment.student_id)
    else:
        form = StudentEnrollmentForm()
    return render(request, 'students/student_form.html', {
        'form': form,
        'courses': Course.objects.filter(is_deleted=False),
        'sidebar': 'students',
    })

@login_required
def student_edit(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk)
    form = StudentEnrollmentForm(request.POST or None, request.FILES or None, instance=enrollment)
    if form.is_valid():
        enrollment = form.save(commit=False)
        if enrollment.student.pk is None:
            enrollment.student.save()
        enrollment.save()
        messages.success(request, "✅ Enrollment updated successfully")
        return redirect('student_detail', enrollment.student_id)
    return render(request, 'students/student_form.html', {
        'form': form,
        'enrollment': enrollment,
        'sidebar': 'students',
    })

@login_required
def enrollment_delete(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk)
    if enrollment.is_deleted:
        messages.warning(request, "Already deleted.")
        return redirect('student_trash')  # Make sure 'student_trash' url name exists
    if request.method == 'POST':
        enrollment.delete()
        remaining = StudentEnrollment.objects.filter(student=enrollment.student, is_deleted=False).count()
        if remaining == 0:
            messages.info(request, "No active enrollments left: student moved to trash.")
            return redirect('student_trash')  # Make sure url exists
        else:
            return redirect('student_detail', enrollment.student_id)
    return render(request, 'students/enrollment_confirm_delete.html', {
        'enrollment': enrollment,
        'sidebar': 'students',
    })

# ... Other views unchanged

@require_POST
@login_required
def add_payment(request, pk):
    enrollment = get_object_or_404(StudentEnrollment, pk=pk)
    try:
        amount = Decimal(request.POST.get('amount', '0'))
        if amount <= 0:
            raise ValueError('Amount must be positive.')
        payment_mode = request.POST.get('payment_mode')
        payment_type = request.POST.get('payment_type')
        payment_date_str = request.POST.get('payment_date')
        payment_date = timezone.datetime.strptime(payment_date_str, '%Y-%m-%d').date() if payment_date_str else timezone.now().date()
        if payment_type == 'Admission Fee':
            due = enrollment.admission_fee_remaining
            if due <= 0:
                messages.error(request, 'Admission fee already settled.')
                return redirect('student_detail', enrollment.student_id)
            if amount > due:
                messages.error(request, f"Amount exceeds due admission fee of ₹{due}.")
                return redirect('student_detail', enrollment.student_id)
        elif payment_type == 'Course Fee':
            due = enrollment.course_fee_remaining
            if due <= 0:
                messages.error(request, 'Course fee already settled.')
                return redirect('student_detail', enrollment.student_id)
            if amount > due:
                messages.error(request, f"Amount exceeds due course fee of ₹{due}.")
                return redirect('student_detail', enrollment.student_id)
        else:
            messages.error(request, 'Invalid payment type.')
            return redirect('student_detail', enrollment.student_id)
        Payment.objects.create(
            enrollment=enrollment,
            amount=amount,
            amount_paid=amount,
            payment_mode=payment_mode,
            payment_date=payment_date,
            remarks=payment_type,
            payment_status='paid',
        )
        enrollment.save()
        messages.success(request, 'Payment added successfully.')
    except Exception as e:
        messages.error(request, f"Error adding payment: {str(e)}")
    return redirect('student_detail', enrollment.student_id)
