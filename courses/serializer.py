from rest_framework import serializers
from courses.models import Course, Lesson, Module, Quizes, QuizQuestion, Enrollment, Certificate, CoursePrerequisite

class CoursePrerequisiteSerializer(serializers.ModelSerializer):
    prerequisite_course_title = serializers.CharField(source='prerequisite_course.title', read_only=True)
    class Meta:
        model = CoursePrerequisite
        fields = ['prerequisite_course', 'prerequisite_course_title', 'min_score']

class CourseSerializer(serializers.ModelSerializer):
    prerequisites_details = CoursePrerequisiteSerializer(source='prerequisite_requirements', many=True, read_only=True)
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    instructor_name = serializers.CharField(source='instructor.user.get_full_name', read_only=True)
    
    class Meta:
        model = Course
        fields = '__all__'

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'

class QuizesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quizes
        fields = '__all__'

class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = '__all__' 

class CertificateSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='enrollment.course.title', read_only=True)
    student_name = serializers.CharField(source='enrollment.learner.user.get_full_name', read_only=True)
    class Meta:
        model = Certificate
        fields = '__all__'

class EnrollmentSerializer(serializers.ModelSerializer):
    course_details = CourseSerializer(source='course', read_only=True)
    certificate = CertificateSerializer(read_only=True)
    class Meta:
        model = Enrollment
        fields = '__all__'