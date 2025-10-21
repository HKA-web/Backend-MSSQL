from rest_framework import routers
from django.urls import path
from mssql.views.company import CompanyViewSet
from mssql.views.querytool import QueryToolViewSet

router = routers.DefaultRouter()
router.register(r'company', CompanyViewSet, basename='company')
router.register(r"querytool", QueryToolViewSet, basename="querytool")

urlpatterns = router.urls
