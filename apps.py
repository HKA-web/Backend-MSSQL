from django.apps import AppConfig

class MssqlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mssql'
    enabled = True
