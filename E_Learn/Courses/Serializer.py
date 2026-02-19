# serializers.py
from rest_framework import serializers
from .models import (
    Course, Module, Lesson, Quiz, QuizQuestion, 
    Enrollment, LessonProgress, QuizAttempt, Review,
    Certificate, CoursePrerequisite
)
from django.db import transaction
from django.utils import timezone

class CoursePrerequisiteSerializer(serializers.ModelSerializer):
    prerequisite_title = serializers.CharField(source='prerequisite.title', read_only=True)
    
    class Meta:
        model = CoursePrerequisite
        fields = ['id', 'prerequisite', 'prerequisite_title', 'min_score']

class CourseListSerializer(serializers.ModelSerializer):
    instructor_name = serializers.SerializerMethodField()
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    modules_count = serializers.IntegerField(source='modules.count', read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'short_description', 'thumbnail',
            'difficulty_level', 'is_free', 'price', 'instructor_name',
            'partner_name', 'total_enrollments', 'average_rating',
            'modules_count', 'created_at'
        ]
    
    def get_instructor_name(self, obj):
        if obj.instructor and hasattr(obj.instructor, 'user'):
            return obj.instructor.user.get_full_name() or obj.instructor.user.username
        return None

class CourseDetailSerializer(serializers.ModelSerializer):
    instructor = serializers.SerializerMethodField()
    partner = serializers.SerializerMethodField()
    prerequisites = CoursePrerequisiteSerializer(source='prerequisite_relations', many=True, read_only=True)
    modules = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'thumbnail', 'promo_video_url', 'difficulty_level',
            'is_free', 'price', 'instructor', 'partner',
            'prerequisites', 'modules', 'total_enrollments',
            'average_rating', 'total_reviews', 'total_duration_hours',
            'created_at', 'updated_at', 'is_published'
        ]
    
    def get_instructor(self, obj):
        if obj.instructor:
            return {
                'id': obj.instructor.id,
                'name': obj.instructor.user.get_full_name() or obj.instructor.user.username,
                'avatar': getattr(obj.instructor.user, 'picture_profile', None)
            }
        return None
    
    def get_partner(self, obj):
        if obj.partner:
            return {
                'id': obj.partner.id,
                'name': obj.partner.name,
                'logo': getattr(obj.partner, 'logo', None)
            }
        return None
    
    def get_modules(self, obj):
        modules = obj.modules.all().prefetch_related('lessons')
        return ModuleListSerializer(modules, many=True, context=self.context).data

class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    prerequisites = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Course.objects.all(), required=False, write_only=True
    )
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'short_description', 'thumbnail',
            'promo_video_url', 'difficulty_level', 'is_free', 'price',
            'is_published', 'prerequisites'
        ]
    
    def create(self, validated_data):
        prerequisites = validated_data.pop('prerequisites', [])
        with transaction.atomic():
            course = Course.objects.create(**validated_data)
            
            # Create prerequisite relations
            for prereq in prerequisites:
                CoursePrerequisite.objects.create(
                    course=course,
                    prerequisite=prereq,
                    min_score=70  # Default min score
                )
            
            return course
    
    def update(self, instance, validated_data):
        prerequisites = validated_data.pop('prerequisites', None)
        
        with transaction.atomic():
            # Update course fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            # Update prerequisites if provided
            if prerequisites is not None:
                # Remove existing prerequisites
                instance.prerequisite_relations.all().delete()
                # Add new prerequisites
                for prereq in prerequisites:
                    CoursePrerequisite.objects.create(
                        course=instance,
                        prerequisite=prereq,
                        min_score=70
                    )
            
            return instance

class ModuleListSerializer(serializers.ModelSerializer):
    lessons_count = serializers.IntegerField(source='lessons.count', read_only=True)
    
    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'lessons_count']

class ModuleDetailSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()
    quizzes = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'lessons', 'quizzes']
    
    def get_lessons(self, obj):
        lessons = obj.lessons.filter(is_published=True).order_by('order')
        return LessonListSerializer(lessons, many=True, context=self.context).data
    
    def get_quizzes(self, obj):
        quizzes = obj.quizzes.all().order_by('order')
        return QuizListSerializer(quizzes, many=True, context=self.context).data

class ModuleCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['course', 'title', 'description', 'order']
    
    def validate(self, data):
        # Ensure unique order within course
        course = data.get('course')
        order = data.get('order')
        instance = getattr(self, 'instance', None)
        
        if course and order:
            queryset = Module.objects.filter(course=course, order=order)
            if instance:
                queryset = queryset.exclude(pk=instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    f"Module with order {order} already exists in this course"
                )
        return data

class LessonListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'lesson_type', 'order', 
            'is_free', 'estimated_time_minutes', 'has_code_exercise'
        ]

class LessonDetailSerializer(serializers.ModelSerializer):
    module_title = serializers.CharField(source='module.title', read_only=True)
    course_id = serializers.IntegerField(source='module.course.id', read_only=True)
    quizzes = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'module', 'module_title', 'course_id', 'title',
            'lesson_type', 'content', 'video_url', 'video_duration_minutes',
            'code_initial', 'code_language', 'order', 'is_free',
            'estimated_time_minutes', 'has_code_exercise', 'quizzes',
            'created_at', 'updated_at'
        ]
    
    def get_quizzes(self, obj):
        quizzes = obj.quizzes.all().order_by('order')
        return QuizListSerializer(quizzes, many=True, context=self.context).data

class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'module', 'title', 'lesson_type', 'content', 'video_url',
            'video_duration_minutes', 'code_initial', 'code_solution',
            'code_test', 'code_language', 'order', 'is_free',
            'is_published', 'estimated_time_minutes'
        ]
    
    def validate(self, data):
        # Validate based on lesson type
        lesson_type = data.get('lesson_type')
        
        if lesson_type == 'video' and not data.get('video_url'):
            raise serializers.ValidationError(
                "Video URL is required for video lessons"
            )
        
        if lesson_type == 'code' and not data.get('code_initial'):
            raise serializers.ValidationError(
                "Initial code is required for code exercises"
            )
        
        # Ensure unique order within module
        module = data.get('module')
        order = data.get('order')
        instance = getattr(self, 'instance', None)
        
        if module and order:
            queryset = Lesson.objects.filter(module=module, order=order)
            if instance:
                queryset = queryset.exclude(pk=instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    f"Lesson with order {order} already exists in this module"
                )
        
        return data

class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = ['id', 'question_text', 'options', 'correct_option', 'explanation', 'points', 'order']

class QuizListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'quiz_type', 'time_limit_minutes', 'total_questions', 'order']

class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)
    parent_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'quiz_type', 'time_limit_minutes',
            'max_attempts', 'passing_score', 'shuffle_questions',
            'show_answers', 'order', 'total_questions', 'questions',
            'parent_info'
        ]
    
    def get_parent_info(self, obj):
        if obj.course:
            return {'type': 'course', 'id': obj.course.id, 'title': obj.course.title}
        elif obj.module:
            return {'type': 'module', 'id': obj.module.id, 'title': obj.module.title}
        elif obj.lesson:
            return {'type': 'lesson', 'id': obj.lesson.id, 'title': obj.lesson.title}
        return None

class QuizCreateUpdateSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, required=False)
    
    class Meta:
        model = Quiz
        fields = [
            'course', 'module', 'lesson', 'title', 'description',
            'quiz_type', 'time_limit_minutes', 'max_attempts',
            'passing_score', 'shuffle_questions', 'show_answers', 'order',
            'questions'
        ]
    
    def validate(self, data):
        # Ensure only one parent is provided
        parents = [data.get('course'), data.get('module'), data.get('lesson')]
        if sum(1 for p in parents if p) != 1:
            raise serializers.ValidationError(
                "Quiz must have exactly one parent (course, module, or lesson)"
            )
        return data
    
    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        
        with transaction.atomic():
            quiz = Quiz.objects.create(**validated_data)
            
            for order, question_data in enumerate(questions_data):
                QuizQuestion.objects.create(quiz=quiz, order=order, **question_data)
            
            quiz.update_stats()
            return quiz
    
    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)
        
        with transaction.atomic():
            # Update quiz fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            # Update questions if provided
            if questions_data is not None:
                instance.questions.all().delete()
                for order, question_data in enumerate(questions_data):
                    QuizQuestion.objects.create(quiz=instance, order=order, **question_data)
                
                instance.update_stats()
            
            return instance

class EnrollmentSerializer(serializers.ModelSerializer):
    learner_name = serializers.SerializerMethodField()
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_thumbnail = serializers.ImageField(source='course.thumbnail', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'learner', 'learner_name', 'course', 'course_title',
            'course_thumbnail', 'status', 'enrolled_at', 'completed_at',
            'progress_percentage', 'final_score', 'certificate_issued',
            'organization', 'cohort_name'
        ]
        read_only_fields = ['enrolled_at', 'progress_percentage']
    
    def get_learner_name(self, obj):
        if hasattr(obj.learner, 'user'):
            return obj.learner.user.get_full_name() or obj.learner.user.username
        return str(obj.learner)

class EnrollmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['course', 'organization', 'cohort_name']
    
    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # Check if already enrolled
            learner = request.user.learner_profile
            if Enrollment.objects.filter(learner=learner, course=data['course']).exists():
                raise serializers.ValidationError("Already enrolled in this course")
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['learner'] = request.user.learner_profile
        return super().create(validated_data)

class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'lesson', 'lesson_title', 'is_completed',
            'started_at', 'completed_at', 'last_watched_position',
            'code_submitted', 'code_passed', 'time_spent_seconds'
        ]
        read_only_fields = ['started_at', 'completed_at']

class LessonProgressUpdateSerializer(serializers.Serializer):
    is_completed = serializers.BooleanField(required=False)
    last_watched_position = serializers.IntegerField(required=False, min_value=0)
    code_submitted = serializers.CharField(required=False, allow_blank=True)
    time_spent_seconds = serializers.IntegerField(required=False, min_value=0)
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # If completed, set completed_at
        if validated_data.get('is_completed') and not instance.completed_at:
            instance.completed_at = timezone.now()
        
        instance.save()
        
        # Update enrollment progress if lesson completed
        if validated_data.get('is_completed'):
            enrollment = Enrollment.objects.filter(
                learner=instance.learner,
                course=instance.lesson.module.course
            ).first()
            if enrollment:
                enrollment.update_progress()
        
        return instance

class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    learner_name = serializers.SerializerMethodField()
    
    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'quiz', 'quiz_title', 'learner_name', 'attempt_number',
            'started_at', 'completed_at', 'score', 'passed',
            'time_taken_seconds'
        ]
        read_only_fields = ['started_at', 'attempt_number', 'score', 'passed']

class QuizAnswerSubmitSerializer(serializers.Serializer):
    answers = serializers.JSONField(help_text="Format: {question_id: selected_option_index}")
    time_taken_seconds = serializers.IntegerField(min_value=0)
    
    def validate_answers(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Answers must be a dictionary")
        return value
    
    def save(self, **kwargs):
        quiz_attempt = self.context['quiz_attempt']
        quiz = quiz_attempt.quiz
        
        # Calculate score
        total_points = 0
        earned_points = 0
        answers_dict = {}
        
        for question in quiz.questions.all():
            total_points += question.points
            selected = self.validated_data['answers'].get(str(question.id))
            
            if selected is not None and selected == question.correct_option:
                earned_points += question.points
            
            answers_dict[str(question.id)] = selected
        
        score_percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        
        # Update attempt
        quiz_attempt.answers = answers_dict
        quiz_attempt.score = score_percentage
        quiz_attempt.passed = score_percentage >= quiz.passing_score
        quiz_attempt.completed_at = timezone.now()
        quiz_attempt.time_taken_seconds = self.validated_data['time_taken_seconds']
        quiz_attempt.save()
        
        return quiz_attempt

class ReviewSerializer(serializers.ModelSerializer):
    learner_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = ['id', 'course', 'rating', 'comment', 'learner_name', 'created_at']
        read_only_fields = ['created_at']
    
    def get_learner_name(self, obj):
        if hasattr(obj.learner, 'user'):
            return obj.learner.user.get_full_name() or obj.learner.user.username
        return str(obj.learner)
    
    def validate(self, data):
        request = self.context.get('request')
        if request and request.method == 'POST':
            # Check if already reviewed
            if Review.objects.filter(
                course=data['course'],
                learner=request.user.learner_profile
            ).exists():
                raise serializers.ValidationError("You have already reviewed this course")
        return data

class CertificateSerializer(serializers.ModelSerializer):
    learner_name = serializers.CharField(source='enrollment.learner.user.get_full_name', read_only=True)
    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)
    verification_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'certificate_id', 'enrollment', 'learner_name',
            'course_title', 'issue_date', 'verification_hash',
            'verification_url'
        ]
    
    def get_verification_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f"/verify-certificate/{obj.verification_hash}/")
        return None