
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator


class Student(models.Model):

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    YEAR_CHOICES = [
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year'),
    ]

    student_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    department = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    year = models.CharField(max_length=20, choices=YEAR_CHOICES)
    address = models.TextField()
    profile_photo = models.ImageField(
        upload_to='student_photos/',
        blank=True,
        null=True
    )
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'


class FeeRecord(models.Model):

    SEMESTER_CHOICES = [
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),
        ('3', 'Semester 3'),
        ('4', 'Semester 4'),
        ('5', 'Semester 5'),
        ('6', 'Semester 6'),
        ('7', 'Semester 7'),
        ('8', 'Semester 8'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='fee_records'
    )

    fee_name = models.CharField(max_length=100)
    academic_year = models.CharField(max_length=9)

    semester = models.CharField(
        max_length=1,
        choices=SEMESTER_CHOICES
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.fee_name}"

    @property
    def amount_paid(self):
        total = self.payments.aggregate(
            total=models.Sum('amount')
        )['total']

        return total or Decimal('0.00')

    @property
    def balance(self):
        return self.total_amount - self.amount_paid

    @property
    def payment_status(self):
        if self.balance <= 0:
            return 'Paid'
        elif self.amount_paid > 0:
            return 'Partial'
        return 'Pending'

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'student',
                    'fee_name',
                    'academic_year',
                    'semester'
                ],
                name='unique_student_fee_record'
            )
        ]


class FeePayment(models.Model):

    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('UPI', 'UPI'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Card', 'Card'),
        ('Other', 'Other'),
    ]

    fee_record = models.ForeignKey(
        FeeRecord,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_date = models.DateField(
        default=timezone.localdate
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True
    )

    remarks = models.TextField(blank=True)

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fee_record.student.full_name} - ₹{self.amount}"

    class Meta:
        ordering = ['-payment_date', '-created_at']


class Attendance(models.Model):

    ATTENDANCE_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )

    date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=ATTENDANCE_CHOICES,
        default='Present'
    )

    remarks = models.CharField(
        max_length=255,
        blank=True
    )

    marked_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-date', 'student__full_name']

        constraints = [
            models.UniqueConstraint(
                fields=['student', 'date'],
                name='unique_student_attendance_per_day'
            )
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"


# STUDENT MARKS MODEL
class StudentMarks(models.Model):

    SEMESTER_CHOICES = [
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),
        ('3', 'Semester 3'),
        ('4', 'Semester 4'),
        ('5', 'Semester 5'),
        ('6', 'Semester 6'),
        ('7', 'Semester 7'),
        ('8', 'Semester 8'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='marks_records'
    )

    subject_code = models.CharField(max_length=20)

    subject_name = models.CharField(max_length=150)

    academic_year = models.CharField(max_length=9)

    semester = models.CharField(
        max_length=1,
        choices=SEMESTER_CHOICES
    )

    internal_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(30)
        ]
    )

    external_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(70)
        ]
    )

    credits = models.PositiveSmallIntegerField(
        default=3,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_marks(self):
        return self.internal_marks + self.external_marks

    @property
    def percentage(self):
        return self.total_marks

    @property
    def result(self):
        if self.total_marks >= 40:
            return 'Pass'
        return 'Fail'

    @property
    def grade(self):
        marks = self.total_marks

        if marks >= 90:
            return 'A+'
        elif marks >= 80:
            return 'A'
        elif marks >= 70:
            return 'B'
        elif marks >= 60:
            return 'C'
        elif marks >= 50:
            return 'D'
        elif marks >= 40:
            return 'E'
        return 'F'

    @property
    def grade_point(self):
        marks = self.total_marks

        if marks >= 90:
            return 10
        elif marks >= 80:
            return 9
        elif marks >= 70:
            return 8
        elif marks >= 60:
            return 7
        elif marks >= 50:
            return 6
        elif marks >= 40:
            return 5
        return 0

    def __str__(self):
        return f"{self.student.full_name} - {self.subject_name}"

    class Meta:
        ordering = ['student__full_name', 'semester', 'subject_name']

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'student',
                    'subject_code',
                    'academic_year',
                    'semester'
                ],
                name='unique_student_subject_marks'
            )
        ]
