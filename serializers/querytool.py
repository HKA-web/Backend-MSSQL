from rest_framework import serializers
from django.conf import settings


class QueryToolSerializer(serializers.Serializer):
    sql = serializers.CharField()
    params = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    server = serializers.ChoiceField(
        choices=list(settings.SQLSERVER_DEFAULT.keys()),
        required=False,
        default=list(settings.SQLSERVER_DEFAULT.keys())[0] if settings.SQLSERVER_DEFAULT else "server1"
    )
    skip = serializers.IntegerField(required=False, default=0)
    take = serializers.IntegerField(required=False, allow_null=True)