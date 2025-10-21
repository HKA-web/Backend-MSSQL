from rest_framework import routers
from django.urls import path
from mssql.views.querytool import QueryToolViewSet

router = routers.DefaultRouter()
router.register(r"querytool", QueryToolViewSet, basename="querytool")

urlpatterns = router.urls
