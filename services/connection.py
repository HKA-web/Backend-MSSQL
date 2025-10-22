import pyodbc
from django.conf import settings

def get_connection(server_key="server1"):
    """
    Mengembalikan koneksi pyodbc ke SQL Server berdasarkan konfigurasi settings.SQLSERVER_CONF
    """
    cfg = settings.SQLSERVER_CONF.get(server_key)
    if not cfg:
        raise ValueError(f"SQL Server connection '{server_key}' tidak ditemukan")

    conn_str = (
        f"DRIVER={cfg['driver']};"
        f"SERVER=np:{cfg['pipe']};"
        f"DATABASE={cfg['database']};"
        f"UID={cfg['uid']};"
        f"PWD={cfg['pwd']};"
    )
    return pyodbc.connect(conn_str)
