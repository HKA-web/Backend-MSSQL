from django.urls import re_path
from mssql.consumers import MssqlConsumer

websocket_urlpatterns = [
    re_path(r'ws/auth/(?P<user_id>\w+)/$', MssqlConsumer.as_asgi()),
]
