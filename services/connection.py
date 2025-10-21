import pyodbc
from django.conf import settings

# Konfigurasi multi-SQLServer
SQLSERVER_CONF = getattr(settings, "SQLSERVER_CONF", {
    "server1": {
        "driver": "{SQL Server}",
        "pipe": r"\\192.168.6.28\pipe\sql\query",
        "database": "master",
        "uid": "sa",
        "pwd": "PASSWORDSETUPSRVNUSANTARAMUJUR",
    },
    # Tambahkan server lain jika perlu
    "server2": {
        "driver": "{SQL Server}",
        "pipe": r"\\192.168.6.29\pipe\sql\query",
        "database": "master",
        "uid": "sa",
        "pwd": "PASSWORDSETUPSRVNUSANTARAMUJUR",
    },
})

def get_connection(server_key="server1"):
    """
    Mengembalikan koneksi pyodbc ke SQL Server.
    """
    cfg = SQLSERVER_CONF.get(server_key)
    if not cfg:
        raise ValueError(f"SQL Server connection '{server_key}' tidak ditemukan")

    conn_str = (
        f"DRIVER={cfg['driver']};"
        f"SERVER=np:{cfg['pipe']};"  # "np:" untuk named pipe SQL Server 2000
        f"DATABASE={cfg['database']};"
        f"UID={cfg['uid']};"
        f"PWD={cfg['pwd']};"
    )
    return pyodbc.connect(conn_str)
