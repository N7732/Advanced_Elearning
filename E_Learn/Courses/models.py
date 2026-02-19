from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class Course(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    # Core fields
    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True, help_text="Brief summary for cards")
    
    # Status
    is_published = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Media
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    promo_video_url = models.URLField(blank=True, null=True, help_text="YouTube/Vimeo promo video")

    # Difficulty & Categorization
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner', db_index=True)
    
    # Instructor/Organization (simplified)
    instructor = models.ForeignKey(
        'Account.Instructor',
        on_delete=models.SET_NULL,  # Don't delete courses if instructor is deleted
        null=True,
        blank=True,
        related_name='courses_created'
    )
    
    partner = models.ForeignKey(
        'partner.Partner',  # Fixed typo
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )

    # Pricing (simplified)
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    
    # Statistics (denormalized for performance)
    total_enrollments = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    total_duration_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    # Prerequisites (keep as is but add through model)
    prerequisites = models.ManyToManyField(
        'self', 
        through='CoursePrerequisite', 
        symmetrical=False, 
        blank=True
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_published', 'difficulty_level']),
            models.Index(fields=['instructor', 'is_published']),
            models.Index(fields=['partner', 'is_published']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)
    
    def _generate_unique_slug(self):
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        while Course.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug
    
    def update_stats(self):
        """Update course statistics"""
        self.total_enrollments = self.enrollments.count()
        self.average_rating = self.reviews.aggregate(avg=models.Avg('rating'))['avg'] or 0
        self.total_reviews = self.reviews.count()
        self.save(update_fields=['total_enrollments', 'average_rating', 'total_reviews'])


class CoursePrerequisite(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='prerequisite_relations')
    prerequisite = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='dependent_relations')
    min_score = models.PositiveSmallIntegerField(default=70, validators=[MinValueValidator(0), MaxValueValidator(100)], 
                                                help_text="Minimum score % required")

    class Meta:
        unique_together = ('course', 'prerequisite')
        indexes = [
            models.Index(fields=['course']),
            models.Index(fields=['prerequisite']),
        ]

    def __str__(self):
        return f"{self.prerequisite.title} → {self.course.title} (min {self.min_score}%)"


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    # Stats
    total_lessons = models.PositiveIntegerField(default=0)
    total_duration_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ['course', 'order']
        indexes = [
            models.Index(fields=['course', 'order']),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.course.update_stats()
    
    def update_stats(self):
        self.total_lessons = self.lessons.count()
        self.save(update_fields=['total_lessons'])


class Lesson(models.Model):
    LESSON_TYPES = [
        ('text', 'Text'),
        ('video', 'Video'),
        ('code', 'Code Exercise'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
    ]

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='text', db_index=True)
    
    # Content (simplified - one content field with type-specific rendering)
    content = models.TextField(blank=True, help_text="Markdown/HTML content")
    
    # For video lessons
    video_url = models.URLField(blank=True, null=True)
    video_duration_minutes = models.PositiveIntegerField(default=0)
    
    # For code exercises
    code_initial = models.TextField(blank=True, help_text="Initial code for exercise")
    code_solution = models.TextField(blank=True, help_text="Solution code")
    code_test = models.TextField(blank=True, help_text="Test cases")
    code_language = models.CharField(max_length=50, default='python', blank=True)
    
    # Metadata
    order = models.PositiveIntegerField(default=0)
    is_free = models.BooleanField(default=False, help_text="Free preview available")
    is_published = models.BooleanField(default=False, db_index=True)
    estimated_time_minutes = models.PositiveIntegerField(default=5)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ['module', 'order']
        indexes = [
            models.Index(fields=['module', 'is_published']),
            models.Index(fields=['lesson_type']),
        ]

    def __str__(self):
        return self.title
    
    @property
    def has_code_exercise(self):
        return self.lesson_type == 'code' and self.code_initial
    
    @property
    def embed_url(self):
        """Get embeddable URL for videos"""
        if not self.video_url:
            return ''
        
        url = self.video_url.lower()
        if 'youtube.com/watch?v=' in url:
            return url.replace('watch?v=', 'embed/')
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[-1].split('?')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        elif 'vimeo.com/' in url:
            video_id = url.split('vimeo.com/')[-1].split('?')[0]
            return f"https://player.vimeo.com/video/{video_id}"
        return self.video_url


class Quiz(models.Model):  # Renamed from Quizes
    QUIZ_TYPES = [
        ('lesson', 'Lesson Quiz'),
        ('module', 'Module Test'),
        ('final', 'Final Exam'),
        ('practice', 'Practice Test'),
    ]

    # Single parent relationship (simplified)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPES, default='lesson')
    
    # Settings
    time_limit_minutes = models.PositiveIntegerField(default=10)
    max_attempts = models.PositiveIntegerField(default=1)
    passing_score = models.PositiveSmallIntegerField(default=70, validators=[MinValueValidator(0), MaxValueValidator(100)])
    shuffle_questions = models.BooleanField(default=True)
    show_answers = models.BooleanField(default=True, help_text="Show correct answers after submission")
    
    # Ordering within parent
    order = models.PositiveIntegerField(default=0)
    
    # Stats
    total_questions = models.PositiveIntegerField(default=0)
    total_attempts = models.PositiveIntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['module', 'quiz_type']),
        ]

    def __str__(self):
        if self.course:
            return f"{self.course.title} - {self.title}"
        elif self.module:
            return f"{self.module.title} - {self.title}"
        return self.title
    
    def update_stats(self):
        self.total_questions = self.questions.count()
        self.save(update_fields=['total_questions'])
class CourseExams(models.Model):
    """Final Exams at the end of the course required"""
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='course_exam', help_text="Each Course has exactly one final exam")
    title = models.CharField(max_length=50, default="Final Exams")
    description = models.CharField(max_length= 200, help_text ="Instructions for Exams",blank = True)

    #Exam Settings
    time_limit_minutes = models.PositiveBigIntegerField(default=60)
    max_attempts = models.PositiveBigIntegerField(default=2,help_text="Number of Attempts")
    passing_score = models.PositiveSmallIntegerField(default=80,validators=[MinValueValidator(0),MaxValueValidator(100)], help_text="Min and Max Marks")
    shuffle_questions = models.BooleanField(default=True)
    show_answer = models.BooleanField(default=False, help_text="Off answers to avoid Cheating")
    require_all_quizes_passed = models.BooleanField(default=False)

    #Statistics
    total_question = models.PositiveIntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2,default=0.00)
    pass_rate = models.PositiveIntegerField(default = 0)
    total_attempts = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Course Exam"
        verbose_name_plural = "Course Exams"

    def __str__(self):
        return f"Final Exams:{self.course.title}"
    def update_status(self):
        self.total_question = self.total_question
        # self.total_question = self.questions.count() # If questions matched this model
        self.save(update_fields=["total_question"])

class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    
    # Options (simplified to JSON for flexibility)
    options = models.JSONField(default=list, help_text='List of options like ["Option A", "Option B", ...]')
    correct_option = models.PositiveSmallIntegerField(help_text="Index of correct option (0-based)")
    
    explanation = models.TextField(blank=True, help_text="Explanation of correct answer")
    points = models.PositiveSmallIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['quiz', 'order']),
        ]

    def __str__(self):
        return f"Q{self.order+1}: {self.question_text[:50]}"


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('expired', 'Expired'),
    ]

    learner = models.ForeignKey('Account.LearnerProfile', on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    
    # For organizations/bootcamps (simplified cohort support)
    organization = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments')
    cohort_name = models.CharField(max_length=100, blank=True, help_text="For bootcamp/organization cohorts")
    
    # Status & Progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Progress tracking
    progress_percentage = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])
    last_accessed = models.DateTimeField(auto_now=True)
    current_lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Results
    final_score = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MaxValueValidator(100)])
    certificate_issued = models.BooleanField(default=False)

    class Meta:
        unique_together = ('learner', 'course')
        indexes = [
            models.Index(fields=['learner', 'status']),
            models.Index(fields=['course', 'status']),
            models.Index(fields=['organization', 'cohort_name']),
        ]

    def __str__(self):
        return f"{self.learner} - {self.course.title}"
    
    def update_progress(self):
        """Calculate and update progress percentage"""
        total_lessons = Lesson.objects.filter(module__course=self.course, is_published=True).count()
        if total_lessons == 0:
            return
        
        completed = LessonProgress.objects.filter(
            learner=self.learner,
            lesson__module__course=self.course,
            is_completed=True
        ).count()
        
        self.progress_percentage = int((completed / total_lessons) * 100)
        
        if self.progress_percentage >= 100:
            self.status = 'completed'
            self.completed_at = models.DateTimeField(auto_now=True)
        
        self.save(update_fields=['progress_percentage', 'status', 'completed_at'])


class LessonProgress(models.Model):
    learner = models.ForeignKey('Account.LearnerProfile', on_delete=models.CASCADE, related_name='lesson_progress_records')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    
    # Progress tracking
    is_completed = models.BooleanField(default=False, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # For video lessons
    last_watched_position = models.PositiveIntegerField(default=0, help_text="Last video position in seconds")
    
    # For code exercises
    code_submitted = models.TextField(blank=True)
    code_passed = models.BooleanField(default=False)
    
    # Time tracking
    time_spent_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('learner', 'lesson')
        indexes = [
            models.Index(fields=['learner', 'is_completed']),
            models.Index(fields=['lesson', 'is_completed']),
        ]

    def __str__(self):
        return f"{self.learner} - {self.lesson.title} - {'✓' if self.is_completed else '○'}"
    
    def complete(self):
        self.is_completed = True
        self.completed_at = models.DateTimeField(auto_now=True)
        self.save()
        # Update enrollment progress
        enrollment = Enrollment.objects.filter(
            learner=self.learner,
            course=self.lesson.module.course
        ).first()
        if enrollment:
            enrollment.update_progress()


class QuizAttempt(models.Model):
    """Track quiz attempts and answers"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    learner = models.ForeignKey('Account.LearnerProfile', on_delete=models.CASCADE, related_name='quiz_attempts')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='quiz_attempts', null=True)
    
    # Attempt info
    attempt_number = models.PositiveSmallIntegerField(default=1)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    score = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])
    passed = models.BooleanField(default=False)
    
    # Time tracking
    time_taken_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('quiz', 'learner', 'attempt_number')
        indexes = [
            models.Index(fields=['learner', 'quiz']),
            models.Index(fields=['enrollment']),
        ]

    def __str__(self):
        return f"{self.learner} - {self.quiz.title} (Attempt {self.attempt_number})"


class Review(models.Model):
    """Course reviews and ratings"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    learner = models.ForeignKey('Account.LearnerProfile', on_delete=models.CASCADE, related_name='reviews')
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='review')
    
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('course', 'learner')
        indexes = [
            models.Index(fields=['course', 'rating']),
        ]

    def __str__(self):
        return f"{self.learner} - {self.course.title} - {self.rating}★"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.course.update_stats()

class CourseExamAttempt(models.Model):
    """Final Marks and Attempts"""
    exam = models.ForeignKey(CourseExams,on_delete=models.CASCADE,related_name="attempts")
    learner = models.ForeignKey("Account.LearnerProfile", on_delete=models.CASCADE, related_name="exam_attempts")
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE,related_name="Exam_attempts")

    attempt_number = models.PositiveSmallIntegerField(default=1)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at =models.DateTimeField(null=True,blank=True)

    score = models.PositiveSmallIntegerField(default=0,validators=[MaxValueValidator(100)])
    passed = models.BooleanField(default=False)
    answers = models.JSONField(default= dict)

    #Time Trackinging

    class Meta:
        unique_together = ('exam', 'learner', 'attempt_number')
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.learner}- {self.exam.course.title} exam Attempt:{self.attempt_number}"
    
    def save(self, *args, **kwargs):
        super().save(*args,**kwargs)

        if self.passed:
            self.enrollment.passed =True
            self.enrollment.final_score = self.score
            self.enrollment.save()

        self.enrollment.total_attempt = CourseExamAttempt.objects.filter(enrollment = self.enrollment).count()
        self.enrollment.save()
        self.enrollment.update_progress()
                                             


class Certificate(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate')
    certificate_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    issue_date = models.DateField(auto_now_add=True)
    
    # PDF certificate (optional - can generate on demand)
    pdf_file = models.FileField(upload_to='certificates/', null=True, blank=True)
    
    # Verification
    verification_hash = models.CharField(max_length=64, unique=True, editable=False)
    
    def __str__(self):
        return f"Certificate - {self.enrollment.learner} - {self.enrollment.course.title}"
    
    def save(self, *args, **kwargs):
        if not self.verification_hash:
            import hashlib
            hash_input = f"{self.certificate_id}{self.enrollment.learner.id}{self.enrollment.course.id}"
            self.verification_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        super().save(*args, **kwargs)