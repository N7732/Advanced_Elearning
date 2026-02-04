from django.db import models


class Course(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)

    # Difficulty Level
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')

    # Instructor who created/owns this course
    instructor = models.ForeignKey(
        'accounts.Instructor',
        on_delete=models.CASCADE,
        related_name='courses',
        null=True,
        blank=True,
        help_text="Instructor who created this course"
    )
    
    # Partner organization this course belongs to
    partner = models.ForeignKey(
        'partern.TenantPartner',
        on_delete=models.CASCADE,
        related_name='courses',
        null=True,
        blank=True,
        help_text="Partner organization offering this course"
    )

    # For free courses/paid courses
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')

    # Prerequisites: Courses that must be completed before taking this one
    prerequisites = models.ManyToManyField(
        'self', 
        through='CoursePrerequisite', 
        symmetrical=False, 
        related_name='required_for', 
        blank=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return f"{self.title} ({self.get_difficulty_level_display()})"

class CoursePrerequisite(models.Model):
    """
    Through model for course prerequisites to allow specifying minimum marks
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='prerequisite_requirements')
    prerequisite_course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='dependent_courses')
    min_score = models.DecimalField(max_digits=5, decimal_places=2, default=50.00, help_text="Minimum marks required to satisfy this prerequisite")

    class Meta:
        unique_together = ('course', 'prerequisite_course')
        verbose_name = "Course Prerequisite"
        verbose_name_plural = "Course Prerequisites"

    def __str__(self):
        return f"{self.prerequisite_course.title} required for {self.course.title} (Min Score: {self.min_score})"

class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} (Course: {self.course.title})"
    
class Lesson(models.Model):
    Text ="text"
    Video ="video"
    Code ="code"
    LESSON_TYPE_CHOICES = [
        (Text, 'Text'),
        (Video, 'Video'),
        (Code, 'CodeExercises'),
    ]
    module = models.ForeignKey(Module, related_name='lessons', on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=100)
    lesson_type = models.CharField(max_length=10, choices=LESSON_TYPE_CHOICES, default=Text)
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True, null=True)
    code_template = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} (Module: {self.module.title if self.module else 'None'})"
    
class Quizes(models.Model):
    lesson = models.ForeignKey(Lesson, related_name='quizes', on_delete=models.CASCADE)
    question = models.TextField()
    max_attempts = models.PositiveIntegerField(default=1)
    time_limit = models.PositiveIntegerField(help_text="Time limit in seconds", default=60)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Quiz for Lesson: {self.lesson.title}"
    
class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quizes, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    
    #Answer options for multiple choice questions
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=[
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ])
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Question for Quiz: {self.quiz.id}"
    
class Enrollment(models.Model):
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ], default='active')

    learner = models.ForeignKey('accounts.Learner', related_name='enrollments', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='enrollments', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Final grade/score obtained")

    class Meta:
        unique_together = ('learner', 'course')
        ordering = ['-enrolled_at']
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"

    def __str__(self):
        return f"{self.learner.user.username} enrolled in {self.course.title}"

class Certificate(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate')
    issue_date = models.DateField(auto_now_add=True)
    certificate_code = models.CharField(max_length=100, unique=True)
    file = models.FileField(upload_to='certificates/', null=True, blank=True)

    def __str__(self):
        return f"Certificate for {self.enrollment.learner.user.username} - {self.enrollment.course.title}"
