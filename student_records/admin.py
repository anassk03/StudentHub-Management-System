
from django.contrib import admin
from .models import Student, FeeRecord, FeePayment, Attendance, StudentMarks


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'student_id', 'full_name', 'email', 'phone',
        'department', 'course', 'year', 'gender',
        'registration_date',
    )
    search_fields = (
        'student_id', 'full_name', 'email',
        'phone', 'department', 'course',
    )
    list_filter = ('gender', 'year', 'department', 'registration_date')
    ordering = ('full_name',)
    readonly_fields = ('registration_date',)
    list_per_page = 10


class FeePaymentInline(admin.TabularInline):
    model = FeePayment
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(FeeRecord)
class FeeRecordAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'fee_name', 'academic_year', 'semester',
        'total_amount', 'amount_paid', 'balance', 'payment_status',
    )
    search_fields = ('student__student_id', 'student__full_name', 'fee_name')
    list_filter = ('academic_year', 'semester')
    readonly_fields = ('amount_paid', 'balance', 'payment_status')
    inlines = [FeePaymentInline]
    list_per_page = 10


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = (
        'fee_record', 'amount', 'payment_date',
        'payment_method', 'transaction_id', 'recorded_by',
    )
    search_fields = (
        'fee_record__student__student_id',
        'fee_record__student__full_name',
        'transaction_id',
    )
    list_filter = ('payment_method', 'payment_date')
    readonly_fields = ('created_at',)
    list_per_page = 10


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'date', 'status', 'remarks', 'marked_at',
    )
    search_fields = (
        'student__student_id',
        'student__full_name',
    )
    list_filter = ('date', 'status', 'student__department')
    ordering = ('-date', 'student__full_name')
    readonly_fields = ('marked_at',)
    list_per_page = 20


@admin.register(StudentMarks)
class StudentMarksAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'subject_code',
        'subject_name',
        'semester',
        'internal_marks',
        'external_marks',
        'total_marks_display',
        'grade_display',
        'result_display',
    )

    search_fields = (
        'student__student_id',
        'student__full_name',
        'subject_code',
        'subject_name',
    )

    list_filter = (
        'semester',
        'academic_year',
        'student__department',
    )

    ordering = ('student__full_name', 'semester')
    readonly_fields = ('created_at',)
    list_per_page = 20

    @admin.display(description='Total Marks')
    def total_marks_display(self, obj):
        return obj.total_marks

    @admin.display(description='Grade')
    def grade_display(self, obj):
        return obj.grade

    @admin.display(description='Result')
    def result_display(self, obj):
        return obj.result
