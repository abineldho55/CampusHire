from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# 1. USER PROFILE MODEL (Role Management)

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('COMPANY', 'Company Recruiter'),
        ('OFFICER', 'Placement Officer / Admin'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

# 2. STUDENT PROFILE MODEL


class StudentProfile(models.Model):
    BRANCH_CHOICES = (
        ('CSE', 'Computer Science & Engineering'),
        ('IT', 'Information Technology'),
        ('ECE', 'Electronics & Communication'),
        ('EEE', 'Electrical & Electronics'),
        ('MECH', 'Mechanical Engineering'),
        ('CIVIL', 'Civil Engineering'),
        ('AI_DS', 'AI & Data Science'),
        ('MCA', 'Master of Computer Applications'),
        ('MBA', 'Master of Business Administration'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    
    # Choose file for Student Profile Image
    profile_pic = models.ImageField(upload_to='student_profiles/', blank=True, null=True, help_text="Upload Profile Photo")
    full_name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=30, unique=True, help_text="e.g. 2024CS101")
    branch = models.CharField(max_length=20, choices=BRANCH_CHOICES, default='none')
    graduation_year = models.DateField(help_text="Expected Graduation Date (YYYY-MM-DD)")
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.00, help_text="CGPA out of 10.0 (e.g. 8.45)")
    backlogs = models.PositiveIntegerField(default=0, help_text="Active backlogs count")
    phone = models.CharField(max_length=15, blank=True)
    skills = models.TextField(blank=True, help_text="e.g. Python, Django, SQL, React, Git")
    
    # Choose file for Resume PDF / Document
    resume = models.FileField(upload_to='student_resumes/', blank=True, null=True, help_text="Upload Resume (PDF / DOC)")
    
    is_placed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
       return self.full_name or self.user.username


# 3. COMPANY PROFILE MODEL

class CompanyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    company_name = models.CharField(max_length=100, unique=True)
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, help_text="Brief description of the company")
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True, help_text="Upload Company Logo")
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    VERIFICATION_CHOICES = (
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified (Real Company)'),
        ('REJECTED', 'Rejected (Fake / Invalid)'),
    )

    is_verified = models.BooleanField(default=False, help_text="Verified by Placement Administrator")
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default='PENDING')
    verification_remarks = models.TextField(blank=True, help_text="Notes from Administrator regarding authenticity")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} ({self.get_verification_status_display()})"


# 4. JOB POSTING MODEL

class jobPost(models.Model):
    JOB_TYPE_CHOICES = (
        ('Full-Time', 'Full-Time Employment'),
        ('Internship', 'Internship'),
        ('Intern+FTE', 'Internship + Full-Time Placement'),
    )
    
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='job_postings')
    title = models.CharField(max_length=200, help_text="e.g. Graduate Software Engineer")
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='Full-Time')
    location = models.CharField(max_length=120, default='Hybrid / On-Site')
    package_lpa = models.DecimalField(max_digits=6, decimal_places=2, help_text="Annual CTC in LPA (e.g. 7.50)")
    description = models.TextField(help_text="Job roles & responsibilities")
    required_skills = models.CharField(max_length=255, help_text="e.g. Python, Django, MySQL, REST")
    
    # Eligibility criteria
    min_cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=6.00, help_text="Minimum CGPA required")
    max_backlogs = models.PositiveIntegerField(default=0, help_text="Maximum backlogs allowed")
    eligible_branches = models.CharField(max_length=255, default="All Branches")
    
    deadline = models.DateField(help_text="Application deadline")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.title} at {self.company.company_name}"


    @property
    def is_deadline_passed(self):
        return timezone.now().date() > self.deadline


# 5. APPLICATION MODEL


class Application(models.Model):
    STATUS_CHOICES = (
        ('APPLIED', 'Application Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('SHORTLISTED', 'Shortlisted for Interview'),
        ('INTERVIEW_SCHEDULED', 'Interview Scheduled'),
        ('SELECTED', 'Selected / Offer Extended'),
        ('REJECTED', 'Not Selected'),
    )

    job = models.ForeignKey(jobPost, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='APPLIED')
    cover_note = models.TextField(blank=True, help_text="Optional message / intro note")
    
    # Interview scheduling details
    interview_date = models.DateTimeField(null=True, blank=True)
    interview_location_or_link = models.CharField(max_length=255, blank=True)
    remarks = models.TextField(blank=True, help_text="Feedback or notes from recruiter")

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.student.full_name} applied for {self.job.title} at {self.job.company.company_name}"


 



