
from django.urls import path
from . import views


urlpatterns = [

    # DASHBOARD
    path('', views.dashboard, name='dashboard'),

    # AUTHENTICATION
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # STUDENT MANAGEMENT
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/', views.edit_student, name='edit_student'),
    path('students/<int:pk>/delete/', views.delete_student, name='delete_student'),

    # FEES MANAGEMENT
    path('fees/', views.fee_dashboard, name='fee_dashboard'),
    path('fees/assign/', views.assign_fee, name='assign_fee'),
    path('fees/payment/add/', views.record_payment, name='record_payment'),
    path('fees/<int:pk>/', views.fee_detail, name='fee_detail'),
    path('payments/', views.payment_history, name='payment_history'),

    # ATTENDANCE MANAGEMENT
    path('attendance/', views.attendance_dashboard, name='attendance_dashboard'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/records/', views.attendance_list, name='attendance_list'),
    path(
        'attendance/student/<int:pk>/',
        views.student_attendance,
        name='student_attendance'
    ),

    # REPORTS & ANALYTICS
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/students/', views.student_reports, name='student_reports'),
    path('reports/fees/', views.fee_reports, name='fee_reports'),
    path('reports/attendance/', views.attendance_reports, name='attendance_reports'),

    # CSV EXPORTS
    path(
        'reports/export/students/',
        views.export_student_report,
        name='export_student_report'
    ),
    path(
        'reports/export/fees/',
        views.export_fee_report,
        name='export_fee_report'
    ),
    path(
        'reports/export/attendance/',
        views.export_attendance_report,
        name='export_attendance_report'
    ),

    # STUDENT MARKS MANAGEMENT
    path('marks/', views.marks_dashboard, name='marks_dashboard'),
    path('marks/add/', views.add_student_marks, name='add_student_marks'),
    path('marks/results/', views.semester_results, name='semester_results'),
    path('marks/performance/', views.performance_analysis, name='performance_analysis'),
    path('marks/reports/', views.marks_reports, name='marks_reports'),

    # INDIVIDUAL STUDENT MARKSHEET
    path(
        'marks/student/<int:pk>/',
        views.student_marksheet,
        name='student_marksheet'
    ),

    # MARKS CSV EXPORT
    path(
        'marks/export/',
        views.export_marks_report,
        name='export_marks_report'
    ),
]
