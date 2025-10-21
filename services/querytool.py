import pyodbc
from typing import List, Dict, Any
from django.conf import settings

def get_connection():
    conf = settings.CONFIG.get("databases", {}).get("sqlserver_default", {})
    conn_str = (
        f"DRIVER={conf['driver']};"
        f"Server={conf['pipe']};"
        f"Database={conf['database']};"
        f"UID={conf['uid']};"
        f"PWD={conf['pwd']};"
    )
    return pyodbc.connect(conn_str)

def run_query(sql: str, skip=0, take=50):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            data = [dict(zip(columns, row)) for row in rows]
            paginated = data[skip: skip + take]

            return {
                "message": "Success",
                "status_code": 200,
                "total_count": len(data),
                "data": paginated,
                "skip": skip,
                "take": take,
                "columns": columns
            }
    except Exception as e:
        return {"message": str(e), "status_code": 500, "data": None}

def insert_query(sql: str):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            return {
                "message": "Insert success",
                "status_code": 201,
                "data": sql,
            }
    except Exception as e:
        return {"message": str(e), "status_code": 500}

def update_query(sql: str):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            return {
                "message": "Update success",
                "status_code": 200,
                "data": sql,
            }
    except Exception as e:
        return {"message": str(e), "status_code": 500}

def delete_query(sql: str):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            return {
                "message": "Delete success",
                "status_code": 200,
                "data": sql,
            }
    except Exception as e:
        return {"message": str(e), "status_code": 500}
