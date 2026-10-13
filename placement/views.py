from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import UserProfile, StudentProfile, CompanyProfile, jobPost, Application


# ==========================================
# AUTHENTICATION & REGISTRATION
# ==========================================

def user_login(request):
    """Handles user login using username/email/phone and password."""
    if request.user.is_authenticated:
        return redirect_dashboard(request.user)
        
    if request.method == 'POST':
        login_id = request.POST.get('username', '').strip()
        password = request.POST.get('password')
        username = login_id
        
        # Check if login_id is all digits (phone number attempt)
        if login_id.isdigit():
            if len(login_id) < 10:
                messages.error(request, "Phone number must be at least 10 digits to sign in.")
                return render(request, 'accounts/login.html')
            profile = UserProfile.objects.filter(phone=login_id).first()
            if profile:
                username = profile.user.username
        # Check if login_id is an email
        elif '@' in login_id:
            user_obj = User.objects.filter(email=login_id).first()
            if user_obj:
                username = user_obj.username
                
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check company verification status before allowing login
            if hasattr(user, 'company_profile'):
                company = user.company_profile
                if not company.is_verified:
                    if company.verification_status == 'REJECTED':
                        messages.error(request, f"Access Denied: The company '{company.company_name}' was flagged as fake / unverified by the Office Administrator. Remarks: {company.verification_remarks or 'Verification failed'}")
                    else:
                        messages.warning(request, f"Pending Verification: The company '{company.company_name}' has not yet been verified by the Office Administrator. You will be able to log in once verified as an authentic company.")
                    return render(request, 'accounts/login.html')

            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect_dashboard(user)
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'accounts/login.html')


def register_student(request):
    """Registers a new student user and creates their profile."""
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        roll_number = request.POST.get('roll_number', '').strip()
        branch = request.POST.get('branch', 'CSE')
        cgpa = request.POST.get('cgpa') or 0.00
        graduation_year_str = request.POST.get('graduation_year', '').strip()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        username = email or f"student_{roll_number}"

        # 1. Validate Phone Number (must be exactly 10 digits)
        if not phone:
            messages.error(request, "Phone number is required.")
            return render(request, 'accounts/student_register.html', {'form_data': request.POST})
        if not phone.isdigit() or len(phone) != 10:
            messages.error(request, "Phone number must be exactly 10 digits (digits only, no spaces or special characters).")
            return render(request, 'accounts/student_register.html', {'form_data': request.POST})

        # 2. Validate Graduation Date (must not be in the past)
        if not graduation_year_str:
            messages.error(request, "Expected graduation date is required.")
            return render(request, 'accounts/student_register.html', {'form_data': request.POST})
        try:
            graduation_date = datetime.strptime(graduation_year_str, '%Y-%m-%d').date()
            if graduation_date < timezone.now().date():
                messages.error(request, "Graduation date cannot be in the past (yesterday or earlier). Please select today or a future date.")
                return render(request, 'accounts/student_register.html', {'form_data': request.POST})
        except (ValueError, TypeError):
            messages.error(request, "Invalid graduation date format. Please select a valid date.")
            return render(request, 'accounts/student_register.html', {'form_data': request.POST})

        # 3. Validate Passwords Match
        if password and confirm_password and password != confirm_password:
            messages.error(request, "Passwords do not match. Please re-enter your password.")
            return render(request, 'accounts/student_register.html', {'form_data': request.POST})

        # 4. Check for existing username, email, or roll number
        if User.objects.filter(username=username).exists():
            messages.error(request, "An account with this email address already exists. Please log in.")
            return render(request, 'accounts/student_register.html', {'form_data': request.POST})

        if email and User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email address already exists. Please log in.")
            return render(request, 'accounts/student_register.html', {'form_data': request.POST})

        if roll_number and StudentProfile.objects.filter(roll_number=roll_number).exists():
            messages.error(request, "A student with this roll / register number already exists.")
            return render(request, 'accounts/student_register.html', {'form_data': request.POST})

        # 5. Create User and Profiles
        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user, role='STUDENT', phone=phone)
        
        student_profile = StudentProfile.objects.create(
            user=user,
            full_name=full_name,
            roll_number=roll_number,
            branch=branch,
            phone=phone,
            graduation_year=graduation_date,
            cgpa=cgpa
        )
        
        # Profile Picture & Resume handling
        if request.FILES.get('image'):
            student_profile.profile_pic = request.FILES['image']
            student_profile.save()
        elif request.FILES.get('profile_pic'):
            student_profile.profile_pic = request.FILES['profile_pic']
            student_profile.save()

        if request.FILES.get('resume'):
            student_profile.resume = request.FILES['resume']
            student_profile.save()
            
        messages.success(request, "Student registration successful! Please log in.")
        return redirect('login')
        
    return render(request, 'accounts/student_register.html')


def register_company(request):
    """Registers a new company recruiter and creates their profile."""
    if request.method == 'POST':
        company_name = request.POST.get('company_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        website = request.POST.get('website', '').strip()
        description = request.POST.get('description', '').strip()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        username = email or f"company_{company_name.lower().replace(' ', '_')}"

        # 1. Validate Phone Number (must be exactly 10 digits)
        if not phone:
            messages.error(request, "Phone number is required.")
            return render(request, 'accounts/company_register.html', {'form_data': request.POST})
        if not phone.isdigit() or len(phone) != 10:
            messages.error(request, "Phone number must be exactly 10 digits (digits only, no spaces or special characters).")
            return render(request, 'accounts/company_register.html', {'form_data': request.POST})

        # 2. Validate Passwords Match
        if password and confirm_password and password != confirm_password:
            messages.error(request, "Passwords do not match. Please re-enter your password.")
            return render(request, 'accounts/company_register.html', {'form_data': request.POST})

        # 3. Check for existing username, email, or company name
        if User.objects.filter(username=username).exists():
            messages.error(request, "An account with this email address already exists. Please log in.")
            return render(request, 'accounts/company_register.html', {'form_data': request.POST})

        if email and User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email address already exists. Please log in.")
            return render(request, 'accounts/company_register.html', {'form_data': request.POST})

        if company_name and CompanyProfile.objects.filter(company_name=company_name).exists():
            messages.error(request, "A company with this name is already registered.")
            return render(request, 'accounts/company_register.html', {'form_data': request.POST})

        # 4. Create User and CompanyProfile
        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user, role='COMPANY', phone=phone)
        company_profile = CompanyProfile.objects.create(
            user=user,
            company_name=company_name,
            contact_email=email,
            contact_phone=phone,
            website=website,
            description=description
        )
        
        # Company Logo handling
        if request.FILES.get('logo'):
            company_profile.logo = request.FILES['logo']
            company_profile.save()

        messages.success(request, "Company recruiter registered successfully! Your account is currently pending verification by the Office Administrator. Once verified as authentic, you will be able to log in.")
        return redirect('login')
        
    return render(request, 'accounts/company_register.html')


def user_logout(request):
    """Logs out the user."""
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('login')


def is_officer_or_admin(user):
    """Check if the user is a Placement Officer, Staff, or Superuser Administrator."""
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    try:
        return hasattr(user, 'profile') and user.profile.role == 'OFFICER'
    except Exception:
        return False


def redirect_dashboard(user):
    """Routes users to their correct dashboard based on their role."""
    if is_officer_or_admin(user):
        return redirect('officer_dashboard')
    try:
        if user.profile.role == 'STUDENT':
            return redirect('student_dashboard')
        elif user.profile.role == 'COMPANY':
            return redirect('company_dashboard')
        elif user.profile.role == 'OFFICER':
            return redirect('officer_dashboard')
    except (UserProfile.DoesNotExist, AttributeError):
        pass
    return redirect('login')


# ==========================================
# DASHBOARDS & JOB BROWSING
# ==========================================

@login_required
def student_dashboard(request):
    """Displays student profile, active jobs, and applications."""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('login')

    context = {
        'student': student,
        'active_jobs': jobPost.objects.filter(is_active=True, deadline__gte=timezone.now().date()),
        'applications': Application.objects.filter(student=student),
    }
    return render(request, 'student/student_dashboard.html', context)


@login_required
def company_dashboard(request):
    """Displays company jobs and received applications."""
    if is_officer_or_admin(request.user) and not hasattr(request.user, 'company_profile'):
        return redirect('officer_dashboard')

    try:
        company = request.user.company_profile
    except CompanyProfile.DoesNotExist:
        if is_officer_or_admin(request.user):
            return redirect('officer_dashboard')
        messages.error(request, "Company profile not found.")
        return redirect('login')

    if not company.is_verified:
        logout(request)
        messages.warning(request, "Your company account is pending verification by the Office Administrator. You can sign in once verified as an authentic company.")
        return redirect('login')

    context = {
        'company': company,
        'jobs': jobPost.objects.filter(company=company).order_by('-created_at'),
        'applications': Application.objects.filter(job__company=company).select_related('student', 'job'),
    }
    return render(request, 'company/company_dashboard.html', context)


def job_list(request):
    """Browse active job listings with a search filter."""
    query = request.GET.get('q', '').strip()
    jobs = jobPost.objects.filter(is_active=True).select_related('company')
    
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) | Q(required_skills__icontains=query) |
            Q(company__company_name__icontains=query) | Q(location__icontains=query)
        )
    return render(request, 'jobs/job_list.html', {'jobs': jobs, 'query': query})


# ==========================================
# JOB & APPLICATION ACTIONS
# ==========================================

@login_required
def job_detail(request, pk):
    """Shows details for a specific job."""
    job = get_object_or_404(jobPost, pk=pk)
    has_applied = False
    application = None
    if hasattr(request.user, 'student_profile'):
        application = Application.objects.filter(job=job, student=request.user.student_profile).first()
        has_applied = application is not None
    return render(request, 'jobs/job_detail.html', {'job': job, 'has_applied': has_applied, 'application': application})


@login_required
def apply_for_job(request, pk):
    """Allows a student to apply for a job if eligible."""
    job = get_object_or_404(jobPost, pk=pk)
    student = getattr(request.user, 'student_profile', None)
    
    if not student:
        messages.error(request, "Only students can apply for jobs.")
        return redirect('job_detail', pk=pk)

    if student.cgpa < job.min_cgpa:
        messages.error(request, f"Minimum CGPA required is {job.min_cgpa}.")
        return redirect('job_detail', pk=pk)
        
    if student.backlogs > job.max_backlogs:
        messages.error(request, f"Backlogs exceed allowed limit ({job.max_backlogs}).")
        return redirect('job_detail', pk=pk)

    if Application.objects.filter(job=job, student=student).exists():
        messages.warning(request, "You have already applied for this job.")
    else:
        Application.objects.create(job=job, student=student, cover_note=request.POST.get('cover_note', ''))
        messages.success(request, f"Successfully applied for {job.title}!")

    return redirect('student_dashboard')


@login_required
def post_job(request):
    """Allows a company recruiter to post a new job."""
    company = getattr(request.user, 'company_profile', None)
    if not company:
        messages.error(request, "Only companies can post jobs.")
        return redirect('company_dashboard')

    if request.method == 'POST':
        deadline_str = request.POST.get('deadline')
        if deadline_str:
            try:
                deadline_date = datetime.strptime(deadline_str, '%Y-%m-%d').date()
                if deadline_date < timezone.now().date():
                    messages.error(request, "Application deadline cannot be in the past (yesterday or earlier).")
                    return render(request, 'jobs/post_job.html')
            except (ValueError, TypeError):
                messages.error(request, "Invalid deadline date format.")
                return render(request, 'jobs/post_job.html')

        jobPost.objects.create(
            company=company,
            title=request.POST.get('title'),
            job_type=request.POST.get('job_type'),
            location=request.POST.get('location'),
            package_lpa=request.POST.get('package_lpa'),
            description=request.POST.get('description'),
            required_skills=request.POST.get('required_skills'),
            min_cgpa=request.POST.get('min_cgpa', 6.00),
            max_backlogs=request.POST.get('max_backlogs', 0),
            eligible_branches=request.POST.get('eligible_branches', 'All Branches'),
            deadline=deadline_str
        )
        messages.success(request, "Job posted successfully!")
        return redirect('company_dashboard')

    return render(request, 'jobs/post_job.html')


@login_required
def update_application_status(request, pk):
    """Allows companies or officers to update candidate application status, meeting link, and interview schedule."""
    application = get_object_or_404(Application, pk=pk)
    
    is_owner = hasattr(request.user, 'company_profile') and application.job.company == request.user.company_profile
    is_officer = is_officer_or_admin(request.user)
    
    if not (is_owner or is_officer):
        messages.error(request, "Permission denied.")
        return redirect('company_dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        interview_date_val = request.POST.get('interview_date')
        
        # Validate interview date if provided: cannot be in the past
        if interview_date_val:
            try:
                parsed_dt = datetime.strptime(interview_date_val[:16], '%Y-%m-%dT%H:%M')
                if timezone.is_naive(parsed_dt):
                    parsed_dt = timezone.make_aware(parsed_dt)
                if parsed_dt < timezone.now():
                    messages.error(request, "Interview date cannot be in the past (yesterday or earlier). Please select a current or future date and time.")
                    return render(request, 'jobs/update_application.html', {'application': application, 'is_officer': is_officer})
                application.interview_date = parsed_dt
            except (ValueError, TypeError):
                messages.error(request, "Invalid interview date and time format. Please select a valid date.")
                return render(request, 'jobs/update_application.html', {'application': application, 'is_officer': is_officer})
        else:
            application.interview_date = None

        application.status = new_status
        application.remarks = request.POST.get('remarks', '').strip()
        application.interview_location_or_link = request.POST.get('interview_location_or_link', '').strip()
        application.save()

        if application.status == 'SELECTED':
            student = application.student
            student.is_placed = True
            student.save()
        else:
            student = application.student
            if not Application.objects.filter(student=student, status='SELECTED').exclude(pk=application.pk).exists():
                student.is_placed = False
                student.save()

        if application.interview_location_or_link:
            messages.success(request, f"Application updated to {application.get_status_display()} with meeting details saved successfully!")
        else:
            messages.success(request, f"Application status updated to {application.get_status_display()}.")
            
        if is_officer:
            return redirect('officer_dashboard')
        return redirect('company_dashboard')

    return render(request, 'jobs/update_application.html', {'application': application, 'is_officer': is_officer})


@login_required
def delete_job(request, pk):
    """Allows owner company or admin to delete a job post."""
    job = get_object_or_404(jobPost, pk=pk)
    is_owner = hasattr(request.user, 'company_profile') and job.company == request.user.company_profile
    is_officer = is_officer_or_admin(request.user)
    
    if not (is_owner or is_officer):
        messages.error(request, "Permission denied.")
        return redirect('job_list')

    if request.method == 'POST':
        job.delete()
        messages.success(request, "Job deleted successfully.")
        if is_officer:
            return redirect('officer_dashboard')
        return redirect('company_dashboard')

    cancel_url = 'officer_dashboard' if is_officer else 'company_dashboard'
    return render(request, 'jobs/confirm_delete.html', {'item': job, 'cancel_url': cancel_url})


@login_required
def delete_application(request, pk):
    """Allows student to withdraw or company/officer to remove an application."""
    application = get_object_or_404(Application, pk=pk)
    is_student = hasattr(request.user, 'student_profile') and application.student == request.user.student_profile
    is_owner = hasattr(request.user, 'company_profile') and application.job.company == request.user.company_profile
    is_officer = is_officer_or_admin(request.user)
    
    if not (is_student or is_owner or is_officer):
        messages.error(request, "Permission denied.")
        return redirect('index')

    if request.method == 'POST':
        application.delete()
        messages.success(request, "Application removed.")
        if is_officer:
            return redirect('officer_dashboard')
        return redirect('student_dashboard' if is_student else 'company_dashboard')

    cancel_url = 'officer_dashboard' if is_officer else ('student_dashboard' if is_student else 'company_dashboard')
    return render(request, 'jobs/confirm_delete.html', {'item': application, 'cancel_url': cancel_url})


@login_required
def toggle_job_active(request, pk):
    """Allows Administrator or owning company to pause or activate a job posting."""
    job = get_object_or_404(jobPost, pk=pk)
    is_owner = hasattr(request.user, 'company_profile') and job.company == request.user.company_profile
    is_officer = is_officer_or_admin(request.user)
    
    if not (is_owner or is_officer):
        messages.error(request, "Permission denied.")
        return redirect('job_list')

    job.is_active = not job.is_active
    job.save()
    status_label = "Activated" if job.is_active else "Paused / Deactivated"
    messages.success(request, f"Job drive '{job.title}' has been {status_label}.")

    if is_officer:
        return redirect('officer_dashboard')
    return redirect('company_dashboard')


@login_required
def verify_company(request, pk, action):
    """
    Office Administrator action to verify company authenticity:
    - action='approve': marks verified (real company), unlocks login and drive postings.
    - action='reject': marks rejected (fake / fraudulent), locks account access.
    - action='reset': resets to pending verification.
    """
    if not is_officer_or_admin(request.user):
        messages.error(request, "Permission denied. Only Office Administrators can verify company authenticity.")
        return redirect('login')

    company = get_object_or_404(CompanyProfile, pk=pk)
    remarks = request.POST.get('remarks', '').strip() if request.method == 'POST' else request.GET.get('remarks', '').strip()

    if action == 'approve':
        company.is_verified = True
        company.verification_status = 'VERIFIED'
        if remarks:
            company.verification_remarks = remarks
        elif not company.verification_remarks or "fake" in company.verification_remarks.lower():
            company.verification_remarks = "Verified as authentic company by Placement Office."
        company.save()
        messages.success(request, f"✓ Company '{company.company_name}' successfully verified as REAL! The recruiter can now log in and conduct placement drives.")

    elif action == 'reject':
        company.is_verified = False
        company.verification_status = 'REJECTED'
        if remarks:
            company.verification_remarks = remarks
        elif not company.verification_remarks or "authentic" in company.verification_remarks.lower():
            company.verification_remarks = "Flagged as fake / unverified recruiter by Placement Office."
        company.save()
        messages.warning(request, f"⚠ Company '{company.company_name}' marked as FAKE / REJECTED. Recruiter access is blocked.")

    elif action == 'reset':
        company.is_verified = False
        company.verification_status = 'PENDING'
        if remarks:
            company.verification_remarks = remarks
        company.save()
        messages.info(request, f"Company '{company.company_name}' status reset to Pending Verification.")

    else:
        messages.error(request, "Invalid verification action.")

    return redirect('officer_dashboard')


@login_required
def officer_dashboard(request):
    """
    Office Administrator / Placement Officer Control Center:
    - Verifies whether companies are real or fake (approve/reject).
    - Monitors full operations and workflow of completed and ongoing placement projects.
    - Manages job drives, applications, interviews & candidate placements.
    """
    if not is_officer_or_admin(request.user):
        messages.error(request, "Access restricted to Office Administrators and Placement Officers.")
        return redirect_dashboard(request.user)

    # 1. Summary Statistics & KPI metrics
    total_students = StudentProfile.objects.count()
    placed_students = StudentProfile.objects.filter(is_placed=True).count()
    unplaced_students = total_students - placed_students
    placement_rate = round((placed_students / total_students * 100), 1) if total_students > 0 else 0

    total_companies = CompanyProfile.objects.count()
    pending_companies_count = CompanyProfile.objects.filter(verification_status='PENDING').count()
    verified_companies_count = CompanyProfile.objects.filter(verification_status='VERIFIED').count()
    rejected_companies_count = CompanyProfile.objects.filter(verification_status='REJECTED').count()

    total_jobs = jobPost.objects.count()
    active_jobs_count = jobPost.objects.filter(is_active=True).count()
    paused_jobs_count = total_jobs - active_jobs_count

    total_applications = Application.objects.count()
    applied_count = Application.objects.filter(status='APPLIED').count()
    review_count = Application.objects.filter(status='UNDER_REVIEW').count()
    shortlisted_count = Application.objects.filter(status='SHORTLISTED').count()
    interview_scheduled_count = Application.objects.filter(status='INTERVIEW_SCHEDULED').count()
    selected_count = Application.objects.filter(status='SELECTED').count()
    rejected_apps_count = Application.objects.filter(status='REJECTED').count()

    # 2. Company Management Data & Filtering
    company_filter = request.GET.get('company_status', 'all')
    q_company = request.GET.get('q_company', '').strip()
    
    companies_qs = CompanyProfile.objects.all().order_by('-created_at')
    if company_filter == 'pending':
        companies_qs = companies_qs.filter(verification_status='PENDING')
    elif company_filter == 'verified':
        companies_qs = companies_qs.filter(verification_status='VERIFIED')
    elif company_filter == 'rejected':
        companies_qs = companies_qs.filter(verification_status='REJECTED')
        
    if q_company:
        companies_qs = companies_qs.filter(
            Q(company_name__icontains=q_company) |
            Q(contact_email__icontains=q_company) |
            Q(contact_phone__icontains=q_company)
        )

    # 3. Job Drives Workflow Data & Filtering
    job_status_filter = request.GET.get('job_status', 'all')
    q_job = request.GET.get('q_job', '').strip()
    
    jobs_qs = jobPost.objects.all().select_related('company').order_by('-created_at')
    if job_status_filter == 'active':
        jobs_qs = jobs_qs.filter(is_active=True)
    elif job_status_filter == 'paused':
        jobs_qs = jobs_qs.filter(is_active=False)
        
    if q_job:
        jobs_qs = jobs_qs.filter(
            Q(title__icontains=q_job) |
            Q(company__company_name__icontains=q_job) |
            Q(location__icontains=q_job) |
            Q(required_skills__icontains=q_job)
        )

    # 4. Applications Workflow Data & Filtering
    app_status_filter = request.GET.get('app_status', 'all')
    q_app = request.GET.get('q_app', '').strip()
    
    apps_qs = Application.objects.all().select_related('student', 'job', 'job__company').order_by('-applied_at')
    if app_status_filter and app_status_filter != 'all':
        apps_qs = apps_qs.filter(status=app_status_filter)
        
    if q_app:
        apps_qs = apps_qs.filter(
            Q(student__full_name__icontains=q_app) |
            Q(student__roll_number__icontains=q_app) |
            Q(job__title__icontains=q_app) |
            Q(job__company__company_name__icontains=q_app)
        )

    # 5. Students Directory Data & Filtering
    student_status_filter = request.GET.get('student_status', 'all')
    q_student = request.GET.get('q_student', '').strip()
    
    students_qs = StudentProfile.objects.all().order_by('-created_at')
    if student_status_filter == 'placed':
        students_qs = students_qs.filter(is_placed=True)
    elif student_status_filter == 'unplaced':
        students_qs = students_qs.filter(is_placed=False)
        
    if q_student:
        students_qs = students_qs.filter(
            Q(full_name__icontains=q_student) |
            Q(roll_number__icontains=q_student) |
            Q(branch__icontains=q_student) |
            Q(skills__icontains=q_student)
        )

    context = {
        'total_students': total_students,
        'placed_students': placed_students,
        'unplaced_students': unplaced_students,
        'placement_rate': placement_rate,
        'total_companies': total_companies,
        'pending_companies_count': pending_companies_count,
        'verified_companies_count': verified_companies_count,
        'rejected_companies_count': rejected_companies_count,
        'total_jobs': total_jobs,
        'active_jobs_count': active_jobs_count,
        'paused_jobs_count': paused_jobs_count,
        'total_applications': total_applications,
        'applied_count': applied_count,
        'review_count': review_count,
        'shortlisted_count': shortlisted_count,
        'interview_scheduled_count': interview_scheduled_count,
        'selected_count': selected_count,
        'rejected_apps_count': rejected_apps_count,
        
        'companies': companies_qs,
        'company_filter': company_filter,
        'q_company': q_company,
        
        'jobs': jobs_qs,
        'job_status_filter': job_status_filter,
        'q_job': q_job,
        
        'applications': apps_qs,
        'app_status_filter': app_status_filter,
        'q_app': q_app,
        
        'students': students_qs,
        'student_status_filter': student_status_filter,
        'q_student': q_student,
        'active_tab': request.GET.get('tab', 'companies'),
    }
    return render(request, 'officer/officer_dashboard.html', context)


def index(request):
    """Landing page."""
    return render(request, 'index.html')