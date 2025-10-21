from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    
    class Meta:
        managed = False
        db_table = u'\"{}\".\"company\"'.format('mssql')
        app_label = 'mssql'