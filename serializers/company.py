from rest_framework import serializers
from mssql.models.company import Company

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'
