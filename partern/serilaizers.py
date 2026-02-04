from rest_framework import serializers
from .models import TenantPartner, Campus, Schools, Department

class DepartmentSerializer(serializers.ModelSerializer):
    head_of_department_name = serializers.CharField(source='Head_of_department.get_full_name', read_only=True)
    class Meta:
        model = Department
        fields = '__all__'

class SchoolsSerializer(serializers.ModelSerializer):
    departments = DepartmentSerializer(many=True, read_only=True)
    dean_name = serializers.CharField(source='Dean.get_full_name', read_only=True)
    class Meta:
        model = Schools
        fields = '__all__'

class CampusSerializer(serializers.ModelSerializer):
    schools = SchoolsSerializer(many=True, read_only=True)
    head_of_campus_name = serializers.CharField(source='Head_of_campus.get_full_name', read_only=True)
    class Meta:
        model = Campus
        fields = '__all__'

class TenantPartnerSerializer(serializers.ModelSerializer):
    campuses = CampusSerializer(many=True, read_only=True)
    
    class Meta:
        model = TenantPartner
        fields = '__all__'

