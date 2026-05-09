from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, EmployeeProfile, Attendance, Payroll

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(EmployeeProfile)
admin.site.register(Attendance)
admin.site.register(Payroll)
