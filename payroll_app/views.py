from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .models import Attendance, Payroll, CustomUser, EmployeeProfile
from .forms import AttendanceForm, PayrollForm
from django.utils import timezone

def is_hr(user):
    return user.role == 'HR'

def is_karyawan(user):
    return user.role in ['Karyawan', 'Manajer']

def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            auth_login(request, user)
            if user.role == 'HR':
                return redirect('dashboard_hr')
            else:
                return redirect('dashboard_karyawan')
        else:
            messages.error(request, "Invalid username or password, or account locked.")
    return render(request, 'payroll_app/login.html')

@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('login')

@login_required
@user_passes_test(is_karyawan, login_url='/')
def dashboard_karyawan(request):
    payrolls = Payroll.objects.filter(employee=request.user).order_by('-year', '-month')
    return render(request, 'payroll_app/dashboard_karyawan.html', {'payrolls': payrolls})

@login_required
@user_passes_test(is_hr, login_url='/')
def dashboard_hr(request):
    employees = CustomUser.objects.filter(role__in=['Karyawan', 'Manajer'])
    all_payrolls = Payroll.objects.all().order_by('-year', '-month')
    return render(request, 'payroll_app/dashboard_hr.html', {
        'employees': employees,
        'all_payrolls': all_payrolls
    })

@login_required
@user_passes_test(is_karyawan, login_url='/')
def record_attendance(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.employee = request.user
            today = timezone.localdate()
            if Attendance.objects.filter(employee=request.user, date=today).exists():
                messages.error(request, "Attendance already recorded for today.")
            else:
                attendance.save()
                messages.success(request, "Attendance successfully recorded.")
        else:
            messages.error(request, "Invalid input data.")
    return redirect('dashboard_karyawan')

@login_required
@user_passes_test(is_hr, login_url='/')
def generate_payroll(request):
    if request.method == 'POST':
        form = PayrollForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data['employee']
            month = form.cleaned_data['month']
            year = form.cleaned_data['year']
            
            profile = getattr(employee, 'profile', None)
            if not profile:
                messages.error(request, "Employee profile not found.")
                return redirect('dashboard_hr')
                
            attendance_days = Attendance.objects.filter(
                employee=employee,
                date__year=year,
                date__month=month,
                status='Present'
            ).count()
            
            total_salary = (profile.base_salary / 20) * attendance_days
            
            Payroll.objects.update_or_create(
                employee=employee,
                month=month,
                year=year,
                defaults={'total_salary': total_salary}
            )
            messages.success(request, f"Payroll for {employee.username} generated.")
        else:
            messages.error(request, "Invalid input.")
    return redirect('dashboard_hr')
