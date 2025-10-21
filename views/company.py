from rest_framework import viewsets
from mssql.models.company import Company
from mssql.serializers.company import CompanySerializer

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer