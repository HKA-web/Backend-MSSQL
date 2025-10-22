from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from mssql.models.querytool import run_query, insert_query, update_query, delete_query
from django.conf import settings
from mssql.serializers.querytool import QueryToolSerializer

class QueryToolViewSet(viewsets.ViewSet):
    """API untuk menjalankan query SQL Server multi-connection."""

    @action(detail=False, url_path='read', url_name='query', methods=['post'])
    def query(self, request):
        serializer = QueryToolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = run_query(
            sql=data["sql"],
            params=data.get("params"),
            skip=data.get("skip", 0),
            take=data.get("take"),
            server_key=data.get("server")
        )
        return Response(result, status=result["statuscode"])

    @action(detail=False, url_path='create', url_name='insert_record', methods=['post'])
    def insert_record(self, request):
        serializer = QueryToolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = insert_query(
            sql=data["sql"],
            params=data.get("params"),
            server_key=data.get("server")
        )
        return Response(result, status=result["statuscode"])

    @action(detail=False, url_path='update', url_name='update_record', methods=['put'])
    def update_record(self, request):
        serializer = QueryToolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = update_query(
            sql=data["sql"],
            params=data.get("params"),
            server_key=data.get("server")
        )
        return Response(result, status=result["statuscode"])

    @action(detail=False, url_path='delete', url_name='delete_record', methods=['delete'])
    def delete_record(self, request):
        serializer = QueryToolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = delete_query(
            sql=data["sql"],
            params=data.get("params"),
            server_key=data.get("server")
        )
        return Response(result, status=result["statuscode"])

    # Menampilkan semua endpoint di /api/querytool/
    def list(self, request):
        base = request.build_absolute_uri()
        return Response({
            "create": f"{base}create/",
            "read": f"{base}read/",
            "update": f"{base}update/",
            "delete": f"{base}delete/"
        })
