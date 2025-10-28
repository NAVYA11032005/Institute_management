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
        't_id',  # Enrollment transaction ID
        'get_full_name', 'get_father_name', 'get_gender', 'get_email', 'get_contact',
        'get_emergency_contact',
        'get_city', 'get_state',
        'amount_paid', 'amount_due', 'amount_remaining', 'get_payment_status',
        'batch_time', 'get_referred_by_display', 'get_referral_source_display',
        'get_payment_method', 'get_payment_mode', 'enrollment_date', 'due_date', 'status',
        'view_certificate_link',
    )
    list_filter = (
        'course', 'status', 'payment_status', 'batch_time', 'payment_method', 'payment_mode'
    )
    search_fields = (
        'student__full_name', 'student__father_name', 'student__email', 'student__contact', 'course__course_name'
    )
    inlines = [PaymentInline]

    # Related student fields display methods
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

    def get_emergency_contact(self, obj):
        return obj.student.emergency_contact_number
    get_emergency_contact.short_description = "Emergency Contact"

    def get_city(self, obj):
        return obj.student.city
    get_city.short_description = "City"
    get_city.admin_order_field = 'student__city'

    def get_state(self, obj):
        return obj.student.state
    get_state.short_description = "State"
    get_state.admin_order_field = 'student__state'

    def get_referred_by_display(self, obj):
        if obj.referred_by:
            return obj.referred_by.full_name
        return obj.referred_by_name
    get_referred_by_display.short_description = "Referred By"

    def get_referral_source_display(self, obj):
        return obj.get_referral_source_display()
    get_referral_source_display.short_description = "Referral Source"

    def get_payment_method(self, obj):
        return obj.get_payment_method_display()
    get_payment_method.short_description = "Payment Method"

    def get_payment_mode(self, obj):
        return obj.get_payment_mode_display()
    get_payment_mode.short_description = "Payment Mode"

    def get_payment_status(self, obj):
        return obj.get_payment_status_display()
    get_payment_status.short_description = "Payment Status"

    def amount_paid(self, obj):
        return obj.course_fee_paid + obj.admission_fee_paid
    amount_paid.short_description = "Total Paid"

    def amount_due(self, obj):
        return obj.amount_due
    amount_due.short_description = "Due"

    def amount_remaining(self, obj):
        return obj.amount_remaining
    amount_remaining.short_description = "Remaining"

    def view_certificate_link(self, obj):
        url = f"{obj.pk}/certificate"
        return format_html('<a href="{}" target="_blank">View Certificate</a>', url)
    view_certificate_link.short_description = "Certificate"

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'full_name', 'father_name', 'gender', 'email', 'contact', 'state')
    search_fields = ('student_id', 'full_name', 'father_name', 'email', 'contact')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'payment_date', 'amount_paid', 'payment_mode', 'payment_status')
    search_fields = ('enrollment__student__full_name', 'enrollment__course__course_name')
    list_filter = ('payment_mode', 'payment_status')
