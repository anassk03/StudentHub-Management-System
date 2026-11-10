
from decimal import Decimal
from functools import wraps
from datetime import date
import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Avg
from django.db import transaction
from django.utils import timezone

from .models import (
    Student,
    FeeRecord,
    FeePayment,
    Attendance,
    StudentMarks,
    StudentUserProfile,
)

from .forms import (
    StudentForm,
    FeeRecordForm,
    FeePaymentForm,
    AttendanceForm,
    StudentMarksForm,
)


# ==========================================
# ADMIN ACCESS CONTROL
# ==========================================

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect('login')

        if not (request.user.is_staff or request.user.is_superuser):
            return redirect('student_dashboard')

        return view_func(request, *args, **kwargs)

    return wrapper


# ==========================================
# LOGIN
# ==========================================

def login_view(request):

    # Redirect users who are already logged in.
    if request.user.is_authenticated:

        if request.user.is_staff or request.user.is_superuser:
            return redirect('dashboard')

        if StudentUserProfile.objects.filter(user=request.user).exists():
            return redirect('student_dashboard')

        # Accounts without an Admin role or Student profile cannot use the portal.
        logout(request)

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            # Admin login
            if user.is_staff or user.is_superuser:
                login(request, user)
                return redirect('dashboard')

            # Student login
            if StudentUserProfile.objects.filter(user=user).exists():
                login(request, user)
                return redirect('student_dashboard')

        messages.error(
            request,
            'Invalid username or password, or student account is not linked.'
        )

    return render(request, 'registration/login.html')


# ==========================================
# MAIN DASHBOARD
# ==========================================

@admin_required
def dashboard(request):

    students = Student.objects.all()

    context = {
        'total_students': students.count(),
        'male_students': students.filter(gender='Male').count(),
        'female_students': students.filter(gender='Female').count(),
        'total_departments': students.values('department').distinct().count(),
        'recent_students': students.order_by('-registration_date')[:5],
    }

    return render(request, 'students/dashboard.html', context)


# ==========================================
# STUDENT DASHBOARD
# ==========================================

@login_required(login_url='login')
def student_dashboard(request):

    if request.user.is_staff or request.user.is_superuser:
        return redirect('dashboard')

    profile = get_object_or_404(
        StudentUserProfile,
        user=request.user
    )

    student = profile.student

    attendance_records = Attendance.objects.filter(
        student=student
    )

    marks_records = StudentMarks.objects.filter(
        student=student
    )

    fee_records = FeeRecord.objects.filter(
        student=student
    )

    total_days = attendance_records.count()

    present_days = attendance_records.filter(
        status='Present'
    ).count()

    attendance_percentage = (
        round((present_days / total_days) * 100, 2)
        if total_days else 0
    )

    context = {
        'student': student,
        'attendance_records': attendance_records,
        'attendance_percentage': attendance_percentage,
        'marks_records': marks_records,
        'fee_records': fee_records,
    }

    return render(
        request,
        'students/student_dashboard.html',
        context
    )


# ==========================================
# STUDENT LIST
# ==========================================

@admin_required
def student_list(request):

    query = request.GET.get('q', '')

    students = Student.objects.all()

    if query:
        students = students.filter(
            Q(student_id__icontains=query) |
            Q(full_name__icontains=query) |
            Q(email__icontains=query) |
            Q(department__icontains=query) |
            Q(course__icontains=query)
        )

    return render(
        request,
        'students/student_list.html',
        {'students': students, 'query': query}
    )


# ==========================================
# ADD STUDENT
# ==========================================

@admin_required
def add_student(request):

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, 'Student added successfully!')
            return redirect('student_list')

    else:
        form = StudentForm()

    return render(
        request,
        'students/student_form.html',
        {'form': form, 'page_title': 'Add Student'}
    )


# ==========================================
# STUDENT DETAILS
# ==========================================

@admin_required
def student_detail(request, pk):

    student = get_object_or_404(Student, pk=pk)

    return render(
        request,
        'students/student_detail.html',
        {'student': student}
    )


# ==========================================
# EDIT STUDENT
# ==========================================

@admin_required
def edit_student(request, pk):

    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = StudentForm(
            request.POST,
            request.FILES,
            instance=student
        )

        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('student_list')

    else:
        form = StudentForm(instance=student)

    return render(
        request,
        'students/student_form.html',
        {
            'form': form,
            'page_title': 'Edit Student',
            'student': student,
        }
    )


# ==========================================
# DELETE STUDENT
# ==========================================

@admin_required
def delete_student(request, pk):

    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        student.delete()
        messages.success(request, 'Student deleted successfully!')
        return redirect('student_list')

    return render(
        request,
        'students/student_confirm_delete.html',
        {'student': student}
    )


# ==========================================
# FEES DASHBOARD
# ==========================================

@admin_required
def fee_dashboard(request):

    fee_records = FeeRecord.objects.select_related('student').all()

    total_fees = fee_records.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')

    total_collected = FeePayment.objects.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')

    total_pending = total_fees - total_collected

    context = {
        'fee_records': fee_records,
        'total_fees': total_fees,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'total_fee_records': fee_records.count(),
        'recent_payments': FeePayment.objects.select_related(
            'fee_record__student'
        )[:5],
    }

    return render(request, 'fees/fee_dashboard.html', context)


# ==========================================
# ASSIGN FEE
# ==========================================

@admin_required
def assign_fee(request):

    if request.method == 'POST':
        form = FeeRecordForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Fee assigned successfully!')
            return redirect('fee_dashboard')

    else:
        form = FeeRecordForm()

    return render(request, 'fees/assign_fee.html', {'form': form})


# ==========================================
# RECORD PAYMENT
# ==========================================

@admin_required
def record_payment(request):

    if request.method == 'POST':
        form = FeePaymentForm(request.POST)

        if form.is_valid():

            fee_record = form.cleaned_data['fee_record']
            amount = form.cleaned_data['amount']

            with transaction.atomic():

                fee_record = FeeRecord.objects.select_for_update().get(
                    pk=fee_record.pk
                )

                if amount <= 0 or amount > fee_record.balance:

                    formatted_balance = f"{fee_record.balance:,.2f}"

                    form.add_error(
                        'amount',
                        'Payment cannot exceed the outstanding '
                        f'balance of ₹{formatted_balance}.'
                    )

                else:
                    payment = form.save(commit=False)
                    payment.recorded_by = request.user
                    payment.save()

                    messages.success(
                        request,
                        'Payment recorded successfully!'
                    )

                    return redirect('fee_detail', pk=fee_record.pk)

    else:
        form = FeePaymentForm()

    form.fields['fee_record'].queryset = (
        FeeRecord.objects.select_related('student').order_by(
            'student__full_name'
        )
    )

    return render(request, 'fees/record_payment.html', {'form': form})


# ==========================================
# FEE DETAILS
# ==========================================

@admin_required
def fee_detail(request, pk):

    fee_record = get_object_or_404(
        FeeRecord.objects.select_related('student'),
        pk=pk
    )

    return render(
        request,
        'fees/fee_detail.html',
        {
            'fee_record': fee_record,
            'payments': fee_record.payments.all(),
        }
    )


# ==========================================
# PAYMENT HISTORY
# ==========================================

@admin_required
def payment_history(request):

    payments = FeePayment.objects.select_related(
        'fee_record__student'
    ).all()

    query = request.GET.get('q', '')

    if query:
        payments = payments.filter(
            Q(fee_record__student__student_id__icontains=query) |
            Q(fee_record__student__full_name__icontains=query) |
            Q(transaction_id__icontains=query)
        )

    return render(
        request,
        'fees/payment_history.html',
        {'payments': payments, 'query': query}
    )


# ==========================================
# ATTENDANCE DASHBOARD
# ==========================================

@admin_required
def attendance_dashboard(request):

    selected_date = request.GET.get('date')

    try:
        selected_date = (
            date.fromisoformat(selected_date)
            if selected_date else timezone.localdate()
        )
    except ValueError:
        selected_date = timezone.localdate()

    attendance_records = Attendance.objects.filter(
        date=selected_date
    ).select_related('student')

    total_students = Student.objects.count()
    present_count = attendance_records.filter(status='Present').count()
    absent_count = attendance_records.filter(status='Absent').count()
    late_count = attendance_records.filter(status='Late').count()
    marked_count = attendance_records.count()

    not_marked_count = max(total_students - marked_count, 0)

    attendance_percentage = (
        round((present_count / total_students) * 100, 2)
        if total_students else 0
    )

    context = {
        'selected_date': selected_date,
        'total_students': total_students,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'marked_count': marked_count,
        'not_marked_count': not_marked_count,
        'attendance_percentage': attendance_percentage,
        'recent_attendance': attendance_records[:10],
    }

    return render(
        request,
        'attendance/attendance_dashboard.html',
        context
    )


# ==========================================
# MARK ATTENDANCE
# ==========================================

@admin_required
def mark_attendance(request):

    if request.method == 'POST':
        form = AttendanceForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Attendance marked successfully!')
            return redirect('attendance_list')

    else:
        form = AttendanceForm(
            initial={'date': timezone.localdate()}
        )

    return render(
        request,
        'attendance/mark_attendance.html',
        {'form': form}
    )


# ==========================================
# ALL ATTENDANCE RECORDS
# ==========================================

@admin_required
def attendance_list(request):

    selected_date = request.GET.get('date')
    query = request.GET.get('q', '')

    try:
        selected_date = (
            date.fromisoformat(selected_date)
            if selected_date else timezone.localdate()
        )
    except ValueError:
        selected_date = timezone.localdate()

    attendance_records = Attendance.objects.filter(
        date=selected_date
    ).select_related('student')

    if query:
        attendance_records = attendance_records.filter(
            Q(student__student_id__icontains=query) |
            Q(student__full_name__icontains=query) |
            Q(student__department__icontains=query)
        )

    return render(
        request,
        'attendance/attendance_list.html',
        {
            'attendance_records': attendance_records,
            'selected_date': selected_date,
            'query': query,
        }
    )


# ==========================================
# INDIVIDUAL STUDENT ATTENDANCE HISTORY
# ==========================================

@admin_required
def student_attendance(request, pk):

    student = get_object_or_404(Student, pk=pk)

    attendance_records = Attendance.objects.filter(student=student)

    total_days = attendance_records.count()
    present_days = attendance_records.filter(status='Present').count()
    absent_days = attendance_records.filter(status='Absent').count()
    late_days = attendance_records.filter(status='Late').count()

    attendance_percentage = (
        round((present_days / total_days) * 100, 2)
        if total_days else 0
    )

    context = {
        'student': student,
        'attendance_records': attendance_records,
        'total_days': total_days,
        'present_days': present_days,
        'absent_days': absent_days,
        'late_days': late_days,
        'attendance_percentage': attendance_percentage,
    }

    return render(
        request,
        'attendance/student_attendance.html',
        context
    )


# ==========================================
# REPORTS DASHBOARD
# ==========================================

@admin_required
def reports_dashboard(request):

    total_students = Student.objects.count()

    total_fees = FeeRecord.objects.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')

    total_collected = FeePayment.objects.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')

    outstanding_fees = total_fees - total_collected

    total_attendance = Attendance.objects.count()

    present_count = Attendance.objects.filter(status='Present').count()

    attendance_percentage = (
        round((present_count / total_attendance) * 100, 1)
        if total_attendance else 0
    )

    context = {
        'total_students': total_students,
        'total_fees': total_fees,
        'total_collected': total_collected,
        'outstanding_fees': outstanding_fees,
        'total_attendance': total_attendance,
        'attendance_percentage': attendance_percentage,
    }

    return render(
        request,
        'reports/reports_dashboard.html',
        context
    )


# ==========================================
# STUDENT REPORTS
# ==========================================

@admin_required
def student_reports(request):

    students = Student.objects.all().order_by('full_name')

    selected_department = request.GET.get('department', '')
    selected_course = request.GET.get('course', '')
    selected_year = request.GET.get('year', '')

    if selected_department:
        students = students.filter(department=selected_department)

    if selected_course:
        students = students.filter(course=selected_course)

    if selected_year:
        students = students.filter(year=selected_year)

    departments = Student.objects.values_list(
        'department', flat=True
    ).distinct().order_by('department')

    courses = Student.objects.values_list(
        'course', flat=True
    ).distinct().order_by('course')

    years = Student.objects.values_list(
        'year', flat=True
    ).distinct().order_by('year')

    context = {
        'students': students,
        'departments': departments,
        'courses': courses,
        'years': years,
        'selected_department': selected_department,
        'selected_course': selected_course,
        'selected_year': selected_year,
        'total_students': students.count(),
    }

    return render(
        request,
        'reports/student_reports.html',
        context
    )


# ==========================================
# FEE REPORTS
# ==========================================

@admin_required
def fee_reports(request):

    fee_records = FeeRecord.objects.select_related(
        'student'
    ).all().order_by('student__full_name')

    selected_year = request.GET.get('academic_year', '')
    selected_semester = request.GET.get('semester', '')
    selected_status = request.GET.get('status', '')

    if selected_year:
        fee_records = fee_records.filter(academic_year=selected_year)

    if selected_semester:
        fee_records = fee_records.filter(semester=selected_semester)

    paid_count = partial_count = pending_count = 0

    total_assigned = Decimal('0.00')
    total_collected = Decimal('0.00')
    total_outstanding = Decimal('0.00')

    for fee in fee_records:

        total_assigned += fee.total_amount
        total_collected += fee.amount_paid
        total_outstanding += fee.balance

        if fee.payment_status == 'Paid':
            paid_count += 1
        elif fee.payment_status == 'Partial':
            partial_count += 1
        else:
            pending_count += 1

    if selected_status:
        fee_records = [
            fee for fee in fee_records
            if fee.payment_status == selected_status
        ]

    academic_years = FeeRecord.objects.values_list(
        'academic_year', flat=True
    ).distinct().order_by('-academic_year')

    semesters = FeeRecord.objects.values_list(
        'semester', flat=True
    ).distinct().order_by('semester')

    context = {
        'fee_records': fee_records,
        'academic_years': academic_years,
        'semesters': semesters,
        'selected_year': selected_year,
        'selected_semester': selected_semester,
        'selected_status': selected_status,
        'total_records': len(fee_records),
        'paid_count': paid_count,
        'partial_count': partial_count,
        'pending_count': pending_count,
        'total_assigned': total_assigned,
        'total_collected': total_collected,
        'total_outstanding': total_outstanding,
    }

    return render(
        request,
        'reports/fee_reports.html',
        context
    )


# ==========================================
# ATTENDANCE REPORTS
# ==========================================

@admin_required
def attendance_reports(request):

    attendance_records = Attendance.objects.select_related('student').all()

    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    if start_date:
        try:
            date.fromisoformat(start_date)
            attendance_records = attendance_records.filter(date__gte=start_date)
        except ValueError:
            start_date = ''

    if end_date:
        try:
            date.fromisoformat(end_date)
            attendance_records = attendance_records.filter(date__lte=end_date)
        except ValueError:
            end_date = ''

    total_records = attendance_records.count()
    present_count = attendance_records.filter(status='Present').count()
    absent_count = attendance_records.filter(status='Absent').count()
    late_count = attendance_records.filter(status='Late').count()

    attendance_percentage = (
        round((present_count / total_records) * 100, 2)
        if total_records else 0
    )

    context = {
        'attendance_records': attendance_records,
        'start_date': start_date,
        'end_date': end_date,
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'attendance_percentage': attendance_percentage,
    }

    return render(
        request,
        'reports/attendance_reports.html',
        context
    )


# ==========================================
# EXPORT STUDENT REPORT TO CSV
# ==========================================

@admin_required
def export_student_report(request):

    students = Student.objects.all().order_by('full_name')

    department = request.GET.get('department', '')
    course = request.GET.get('course', '')
    year = request.GET.get('year', '')

    if department:
        students = students.filter(department=department)

    if course:
        students = students.filter(course=course)

    if year:
        students = students.filter(year=year)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="student_report.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        'Student ID', 'Student Name', 'Email', 'Phone',
        'Gender', 'Department', 'Course', 'Year',
        'Date of Birth', 'Registration Date',
    ])

    for student in students:
        writer.writerow([
            student.student_id,
            student.full_name,
            student.email,
            student.phone,
            student.gender,
            student.department,
            student.course,
            student.year,
            student.date_of_birth,
            student.registration_date,
        ])

    return response


# ==========================================
# EXPORT FEE REPORT TO CSV
# ==========================================

@admin_required
def export_fee_report(request):

    fee_records = FeeRecord.objects.select_related(
        'student'
    ).all().order_by('student__full_name')

    academic_year = request.GET.get('academic_year', '')
    semester = request.GET.get('semester', '')
    status = request.GET.get('status', '')

    if academic_year:
        fee_records = fee_records.filter(academic_year=academic_year)

    if semester:
        fee_records = fee_records.filter(semester=semester)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="fee_report.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        'Student ID', 'Student Name', 'Fee Name',
        'Academic Year', 'Semester', 'Total Amount',
        'Amount Paid', 'Outstanding Balance', 'Payment Status',
    ])

    for fee in fee_records:

        if status and fee.payment_status != status:
            continue

        writer.writerow([
            fee.student.student_id,
            fee.student.full_name,
            fee.fee_name,
            fee.academic_year,
            fee.semester,
            fee.total_amount,
            fee.amount_paid,
            fee.balance,
            fee.payment_status,
        ])

    return response


# ==========================================
# EXPORT ATTENDANCE REPORT TO CSV
# ==========================================

@admin_required
def export_attendance_report(request):

    attendance_records = Attendance.objects.select_related('student').all()

    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    if start_date:
        try:
            date.fromisoformat(start_date)
            attendance_records = attendance_records.filter(date__gte=start_date)
        except ValueError:
            start_date = ''

    if end_date:
        try:
            date.fromisoformat(end_date)
            attendance_records = attendance_records.filter(date__lte=end_date)
        except ValueError:
            end_date = ''

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="attendance_report.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        'Student ID', 'Student Name', 'Department',
        'Date', 'Attendance Status', 'Remarks',
    ])

    for record in attendance_records:
        writer.writerow([
            record.student.student_id,
            record.student.full_name,
            record.student.department,
            record.date,
            record.status,
            record.remarks,
        ])

    return response


# ==========================================
# STUDENT MARKS DASHBOARD
# ==========================================

@admin_required
def marks_dashboard(request):

    marks_records = StudentMarks.objects.select_related('student').all()

    total_records = marks_records.count()

    passed_count = sum(
        1 for mark in marks_records if mark.result == 'Pass'
    )

    failed_count = total_records - passed_count

    average_marks = (
        sum(float(mark.total_marks) for mark in marks_records)
        / total_records
        if total_records else 0
    )

    context = {
        'total_records': total_records,
        'passed_count': passed_count,
        'failed_count': failed_count,
        'average_marks': round(average_marks, 2),
        'recent_marks': marks_records[:10],
    }

    return render(
        request,
        'marks/marks_dashboard.html',
        context
    )


# ==========================================
# ADD STUDENT MARKS
# ==========================================

@admin_required
def add_student_marks(request):

    if request.method == 'POST':
        form = StudentMarksForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Student marks added successfully!')
            return redirect('marks_dashboard')

    else:
        form = StudentMarksForm()

    return render(
        request,
        'marks/add_marks.html',
        {'form': form}
    )


# ==========================================
# SEMESTER RESULTS
# ==========================================

@admin_required
def semester_results(request):

    marks_records = StudentMarks.objects.select_related('student').all()

    selected_student = request.GET.get('student', '')
    selected_semester = request.GET.get('semester', '')
    selected_year = request.GET.get('academic_year', '')

    if selected_student:
        marks_records = marks_records.filter(
            student__student_id=selected_student
        )

    if selected_semester:
        marks_records = marks_records.filter(semester=selected_semester)

    if selected_year:
        marks_records = marks_records.filter(academic_year=selected_year)

    total_marks = sum(
        float(mark.total_marks) for mark in marks_records
    )

    total_subjects = marks_records.count()

    percentage = (
        round(total_marks / total_subjects, 2)
        if total_subjects else 0
    )

    total_credits = sum(mark.credits for mark in marks_records)

    weighted_points = sum(
        mark.grade_point * mark.credits
        for mark in marks_records
    )

    sgpa = (
        round(weighted_points / total_credits, 2)
        if total_credits else 0
    )

    passed_subjects = sum(
        1 for mark in marks_records if mark.result == 'Pass'
    )

    context = {
        'marks_records': marks_records,
        'students': Student.objects.all(),
        'selected_student': selected_student,
        'selected_semester': selected_semester,
        'selected_year': selected_year,
        'total_marks': round(total_marks, 2),
        'total_subjects': total_subjects,
        'percentage': percentage,
        'total_credits': total_credits,
        'sgpa': sgpa,
        'passed_subjects': passed_subjects,
        'failed_subjects': total_subjects - passed_subjects,
    }

    return render(
        request,
        'marks/semester_results.html',
        context
    )


# ==========================================
# PERFORMANCE ANALYSIS
# ==========================================

@admin_required
def performance_analysis(request):

    marks_records = StudentMarks.objects.select_related('student').all()

    selected_semester = request.GET.get('semester', '')

    if selected_semester:
        marks_records = marks_records.filter(semester=selected_semester)

    subject_data = (
        marks_records
        .values('subject_name')
        .annotate(
            average_internal=Avg('internal_marks'),
            average_external=Avg('external_marks'),
        )
        .order_by('subject_name')
    )

    subject_performance = []

    for subject in subject_data:
        average = (
            float(subject['average_internal'] or 0)
            + float(subject['average_external'] or 0)
        )

        subject_performance.append({
            'subject_name': subject['subject_name'],
            'average_marks': round(average, 2),
        })

    context = {
        'subject_performance': subject_performance,
        'selected_semester': selected_semester,
        'total_subjects': len(subject_performance),
    }

    return render(
        request,
        'marks/performance_analysis.html',
        context
    )


# ==========================================
# MARKS REPORTS
# ==========================================

@admin_required
def marks_reports(request):

    marks_records = StudentMarks.objects.select_related('student').all()

    selected_student = request.GET.get('student', '')
    selected_semester = request.GET.get('semester', '')
    selected_year = request.GET.get(
        'year',
        request.GET.get('academic_year', '')
    )

    if selected_student:
        marks_records = marks_records.filter(
            student__student_id=selected_student
        )

    if selected_semester:
        marks_records = marks_records.filter(semester=selected_semester)

    if selected_year:
        marks_records = marks_records.filter(academic_year=selected_year)

    total_records = marks_records.count()

    passed_count = sum(
        1 for mark in marks_records if mark.result == 'Pass'
    )

    failed_count = total_records - passed_count

    context = {
        'marks_records': marks_records,
        'students': Student.objects.all(),
        'selected_student': selected_student,
        'selected_semester': selected_semester,
        'selected_year': selected_year,
        'total_records': total_records,
        'passed_count': passed_count,
        'failed_count': failed_count,
    }

    return render(
        request,
        'marks/marks_reports.html',
        context
    )


# ==========================================
# EXPORT MARKS REPORT TO CSV
# ==========================================

@admin_required
def export_marks_report(request):

    marks_records = StudentMarks.objects.select_related(
        'student'
    ).all().order_by(
        'student__full_name',
        'semester',
        'subject_name'
    )

    selected_student = request.GET.get('student', '')
    selected_semester = request.GET.get('semester', '')
    selected_year = request.GET.get(
        'year',
        request.GET.get('academic_year', '')
    )

    # STUDENT FILTER
    if selected_student:
        marks_records = marks_records.filter(
            student__student_id=selected_student
        )

    # SEMESTER FILTER
    if selected_semester:
        marks_records = marks_records.filter(
            semester=selected_semester
        )

    # ACADEMIC YEAR FILTER
    if selected_year:
        marks_records = marks_records.filter(
            academic_year=selected_year
        )

    # CREATE CSV RESPONSE
    response = HttpResponse(
        content_type='text/csv; charset=utf-8'
    )

    response['Content-Disposition'] = (
        'attachment; filename="student_marks_report.csv"'
    )

    # SUPPORT EXCEL UTF-8
    response.write('\ufeff')

    writer = csv.writer(response)

    # CSV HEADINGS
    writer.writerow([
        'Student ID',
        'Student Name',
        'Subject Code',
        'Subject Name',
        'Semester',
        'Academic Year',
        'Internal Marks',
        'External Marks',
        'Total Marks',
        'Credits',
        'Grade',
        'Grade Point',
        'Result',
    ])

    # CSV DATA
    for mark in marks_records:

        writer.writerow([
            mark.student.student_id,
            mark.student.full_name,
            mark.subject_code,
            mark.subject_name,
            mark.semester,
            mark.academic_year,
            mark.internal_marks,
            mark.external_marks,
            mark.total_marks,
            mark.credits,
            mark.grade,
            mark.grade_point,
            mark.result,
        ])

    return response


# ==========================================
# INDIVIDUAL STUDENT MARKSHEET
# ==========================================

@admin_required
def student_marksheet(request, pk):

    student = get_object_or_404(Student, pk=pk)

    marks_records = StudentMarks.objects.filter(
        student=student
    ).order_by('semester', 'subject_name')

    selected_semester = request.GET.get('semester', '')
    selected_year = request.GET.get('year', '')

    # SEMESTER FILTER
    if selected_semester:
        marks_records = marks_records.filter(
            semester=selected_semester
        )

    # ACADEMIC YEAR FILTER
    if selected_year:
        marks_records = marks_records.filter(
            academic_year=selected_year
        )

    # TOTAL SUBJECTS
    total_subjects = marks_records.count()

    # TOTAL MARKS
    total_marks = sum(
        float(mark.total_marks)
        for mark in marks_records
    )

    # PERCENTAGE
    percentage = (
        round(total_marks / total_subjects, 2)
        if total_subjects else 0
    )

    # TOTAL CREDITS
    total_credits = sum(
        mark.credits
        for mark in marks_records
    )

    # SGPA CALCULATION
    weighted_points = sum(
        mark.grade_point * mark.credits
        for mark in marks_records
    )

    sgpa = (
        round(weighted_points / total_credits, 2)
        if total_credits else 0
    )

    # PASS AND FAIL COUNT
    passed_subjects = sum(
        1 for mark in marks_records
        if mark.result == 'Pass'
    )

    failed_subjects = total_subjects - passed_subjects

    # CONTEXT
    context = {
        'student': student,
        'marks_records': marks_records,
        'selected_semester': selected_semester,
        'selected_year': selected_year,
        'total_subjects': total_subjects,
        'total_marks': round(total_marks, 2),
        'percentage': percentage,
        'total_credits': total_credits,
        'sgpa': sgpa,
        'passed_subjects': passed_subjects,
        'failed_subjects': failed_subjects,
    }

    return render(
        request,
        'marks/student_marksheet.html',
        context
    )

# ==========================================
# LOGOUT
# ==========================================

@login_required(login_url='login')
def logout_view(request):

    if request.method == 'POST':
        logout(request)
        return redirect('login')

    return redirect('dashboard')
