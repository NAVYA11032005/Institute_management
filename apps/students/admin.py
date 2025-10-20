from django.contrib import admin
from django.urls import path
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils.html import format_html
import re

from .models import Student, StudentEnrollment, Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ('payment_date', 'amount_paid', 'payment_mode', 'payment_status')
    readonly_fields = ('payment_date',)


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        't_id',  # Changed from 'enrollment_id' to 't_id'
        'get_full_name', 'get_father_name', 'get_gender', 'get_email', 'get_contact',
        'get_emergency_contact_number', 'course', 'get_city', 'get_state',
        'amount_paid', 'amount_due', 'amount_remaining', 'get_payment_status',
        'batch_time', 'get_referred_by_display', 'get_referral_source_display',
        'get_payment_method_display', 'get_payment_mode_display', 'enrollment_date', 'due_date', 'status',
        'view_certificate_link',  # Link column for viewing certificate
    )
    list_filter = (
        'course', 'status', 'payment_status', 'batch_time', 'payment_method', 'payment_mode'
    )
    search_fields = (
        'student__full_name', 'student__father_name', 'student__email', 'student__contact', 'course__course_name'
    )
    inlines = [PaymentInline]

    # Display methods for related student info
    def get_full_name(self, obj):
        return obj.student.full_name
    get_full_name.short_description = "Full Name"
    get_full_name.admin_order_field = 'student__full_name'

    def get_father_name(self, obj):
        return obj.student.father_name
    get_father_name.short_description = "Father's Name"
    get_father_name.admin_order_field = 'student__father_name'

    def get_gender(self, obj):
        return obj.student.get_gender_display()
    get_gender.short_description = "Gender"
    get_gender.admin_order_field = 'student__gender'

    def get_email(self, obj):
        return obj.student.email
    get_email.short_description = "Email"
    get_email.admin_order_field = 'student__email'

    def get_contact(self, obj):
        return obj.student.contact
    get_contact.short_description = "Contact"
    get_contact.admin_order_field = 'student__contact'

    def get_emergency_contact_number(self, obj):
        return obj.student.emergency_contact_number
    get_emergency_contact_number.short_description = "Emergency Contact"

    def get_city(self, obj):
        return obj.student.city
    get_city.short_description = "City"
    get_city.admin_order_field = 'student__city'

    def get_state(self, obj):
        return obj.student.state
    get_state.short_description = "State"
    get_state.admin_order_field = 'student__state'

    def get_referred_by_display(self, obj):
        # Return the full name of the referred_by if set; else fallback to referred_by_name
        if obj.referred_by:
            return obj.referred_by.full_name
        return obj.referred_by_name or "-"
    get_referred_by_display.short_description = "Referred By"

    def get_referral_source_display(self, obj):
        return obj.get_referral_source_display()
    get_referral_source_display.short_description = "Referral Source"

    def get_payment_method_display(self, obj):
        return obj.get_payment_method_display()
    get_payment_method_display.short_description = "Payment Method"

    def get_payment_mode_display(self, obj):
        return obj.get_payment_mode_display()
    get_payment_mode_display.short_description = "Payment Mode"

    def get_payment_status(self, obj):
        status_map = {'paid': 'Paid', 'partial': 'Partial', 'due': 'Due'}
        return status_map.get(obj.payment_status, obj.payment_status)
    get_payment_status.short_description = "Payment Status"

    def amount_paid(self, obj):
        return obj.amount_paid
    amount_paid.short_description = "Paid"

    def amount_due(self, obj):
        return obj.amount_due
    amount_due.short_description = "Due"

    def amount_remaining(self, obj):
        return obj.amount_remaining
    amount_remaining.short_description = "Remaining"

    # Custom column: View Certificate link
    def view_certificate_link(self, obj):
        url = f"{obj.pk}/view-certificate/"
        return format_html('<a class="button" href="{}">View Certificate</a>', url)
    view_certificate_link.short_description = 'Certificate'

    # Add custom admin url for view certificate
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:enrollment_id>/view-certificate/',
                self.admin_site.admin_view(self.view_certificate),
                name='studentenrollment_view_certificate',
            ),
        ]
        return custom_urls + urls

    def view_certificate(self, request, enrollment_id):
        enrollment = get_object_or_404(StudentEnrollment, pk=enrollment_id)

        # Generate certificate_number if it doesn't exist
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

        # Render a simple HTML response for the certificate; you can replace this by more advanced rendering
        return HttpResponse(
            f"<h1>Certificate for Enrollment {enrollment.t_id}</h1>"
            f"<p><strong>Certificate Number:</strong> {enrollment.certificate_number}</p>"
            f"<p><strong>Student:</strong> {enrollment.student.full_name}</p>"
            f"<p><strong>Course:</strong> {enrollment.course.course_name}</p>"
            f"<p><strong>Enrollment Date:</strong> {enrollment.enrollment_date}</p>"
        )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'full_name', 'father_name', 'gender', 'email', 'contact', 'state', 'city')
    search_fields = ('student_id', 'full_name', 'father_name', 'email', 'contact')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'payment_date', 'amount_paid', 'payment_mode', 'payment_status')
    search_fields = ('enrollment__student__full_name', 'enrollment__course__course_name')
    list_filter = ('payment_mode', 'payment_status')
