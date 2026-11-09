
from decimal import Decimal

from django import forms

from .models import (
    Student,
    FeeRecord,
    FeePayment,
    Attendance,
    StudentMarks,
)


# STUDENT REGISTRATION FORM
class StudentForm(forms.ModelForm):

    class Meta:
        model = Student

        fields = [
            'student_id',
            'full_name',
            'email',
            'phone',
            'gender',
            'date_of_birth',
            'department',
            'course',
            'year',
            'address',
            'profile_photo',
        ]

        widgets = {
            'date_of_birth': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'address': forms.Textarea(
                attrs={'rows': 3}
            ),
        }


# FEE ASSIGNMENT FORM
class FeeRecordForm(forms.ModelForm):

    class Meta:
        model = FeeRecord

        fields = [
            'student',
            'fee_name',
            'academic_year',
            'semester',
            'total_amount',
        ]

        widgets = {
            'fee_name': forms.TextInput(
                attrs={'placeholder': 'Example: Tuition Fee'}
            ),
            'academic_year': forms.TextInput(
                attrs={'placeholder': 'Example: 2026-27'}
            ),
            'total_amount': forms.NumberInput(
                attrs={
                    'placeholder': 'Enter total fee',
                    'min': '0.01',
                    'step': '0.01'
                }
            ),
        }

    def clean_total_amount(self):
        amount = self.cleaned_data['total_amount']

        if amount <= Decimal('0.00'):
            raise forms.ValidationError(
                'Total fee must be greater than zero.'
            )

        return amount


# FEE PAYMENT FORM
class FeePaymentForm(forms.ModelForm):

    class Meta:
        model = FeePayment

        fields = [
            'fee_record',
            'amount',
            'payment_date',
            'payment_method',
            'transaction_id',
            'remarks',
        ]

        widgets = {
            'amount': forms.NumberInput(
                attrs={
                    'placeholder': 'Enter payment amount',
                    'min': '0.01',
                    'step': '0.01'
                }
            ),
            'payment_date': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'transaction_id': forms.TextInput(
                attrs={'placeholder': 'Optional transaction ID'}
            ),
            'remarks': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Optional payment remarks'
                }
            ),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        fee_record = self.cleaned_data.get('fee_record')

        if amount <= Decimal('0.00'):
            raise forms.ValidationError(
                'Payment amount must be greater than zero.'
            )

        if fee_record and amount > fee_record.balance:
            formatted_balance = f"{fee_record.balance:,.2f}"

            raise forms.ValidationError(
                'Payment cannot exceed the outstanding balance '
                f'of ₹{formatted_balance}.'
            )

        return amount


# ATTENDANCE FORM
class AttendanceForm(forms.ModelForm):

    class Meta:
        model = Attendance

        fields = [
            'student',
            'date',
            'status',
            'remarks',
        ]

        widgets = {
            'date': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'remarks': forms.TextInput(
                attrs={'placeholder': 'Optional remarks'}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        student = cleaned_data.get('student')
        date = cleaned_data.get('date')

        if student and date:

            existing = Attendance.objects.filter(
                student=student,
                date=date
            )

            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError(
                    'Attendance has already been marked '
                    'for this student on this date.'
                )

        return cleaned_data


# STUDENT MARKS FORM
class StudentMarksForm(forms.ModelForm):

    class Meta:
        model = StudentMarks

        fields = [
            'student',
            'subject_code',
            'subject_name',
            'academic_year',
            'semester',
            'internal_marks',
            'external_marks',
            'credits',
        ]

        widgets = {
            'subject_code': forms.TextInput(
                attrs={'placeholder': 'Example: CS301'}
            ),
            'subject_name': forms.TextInput(
                attrs={'placeholder': 'Example: Data Structures'}
            ),
            'academic_year': forms.TextInput(
                attrs={'placeholder': 'Example: 2026-27'}
            ),
            'internal_marks': forms.NumberInput(
                attrs={
                    'placeholder': 'Out of 30',
                    'min': '0',
                    'max': '30',
                    'step': '0.5'
                }
            ),
            'external_marks': forms.NumberInput(
                attrs={
                    'placeholder': 'Out of 70',
                    'min': '0',
                    'max': '70',
                    'step': '0.5'
                }
            ),
            'credits': forms.NumberInput(
                attrs={
                    'min': '1',
                    'max': '10'
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        student = cleaned_data.get('student')
        subject_code = cleaned_data.get('subject_code')
        academic_year = cleaned_data.get('academic_year')
        semester = cleaned_data.get('semester')

        if student and subject_code and academic_year and semester:

            existing = StudentMarks.objects.filter(
                student=student,
                subject_code=subject_code,
                academic_year=academic_year,
                semester=semester
            )

            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError(
                    'Marks for this student and subject '
                    'already exist in this semester.'
                )

        return cleaned_data
