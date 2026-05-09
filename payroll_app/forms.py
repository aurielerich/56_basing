from django import forms
from .models import Attendance, Payroll

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['status']
    
    def clean_status(self):
        status = self.cleaned_data.get('status')
        valid_statuses = ['Present', 'Leave']
        if status not in valid_statuses:
            raise forms.ValidationError("Invalid status selected.")
        return status

class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ['employee', 'month', 'year']
