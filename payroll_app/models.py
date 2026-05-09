from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('Karyawan', 'Karyawan'),
        ('Manajer', 'Manajer Karyawan'),
        ('HR', 'SDM/HR'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Karyawan')

class EmployeeProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.user.username} - {self.position}"

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('Present', 'Present'),
        ('Leave', 'Leave'),
        ('Absent', 'Absent'),
    )
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('employee', 'date')

    def __str__(self):
        return f"{self.employee.username} - {self.date} ({self.status})"

class Payroll(models.Model):
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payrolls')
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    total_salary = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('employee', 'month', 'year')

    def __str__(self):
        return f"Payroll {self.employee.username} - {self.month}/{self.year}"
