import pyodbc
import logging
import re
import textwrap
from django.conf import settings

logger = logging.getLogger(__name__)
SQLSERVER_CONF = getattr(settings, "SQLSERVER_DEFAULT", {})

def get_connection(server_key="server1"):
    cfg = SQLSERVER_CONF.get(server_key)
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


def _trim_row(columns, row):
    return {col: val.strip() if isinstance(val, str) else val for col, val in zip(columns, row)}


def _is_safe_query(sql):
    forbidden = ["DROP", "ALTER", "TRUNCATE"]
    sql_upper = sql.strip().upper()
    return not any(sql_upper.startswith(f) for f in forbidden)


def _fix_sql2000_compat(sql: str) -> str:
    """
    - Perbaiki NVARCHAR(MAX) -> NVARCHAR(4000)
    - Tambahkan SET NOCOUNT ON;
    - Bungkus DECLARE jadi EXEC jika perlu
    """
    sql = re.sub(r"\bNVARCHAR\s*\(\s*MAX\s*\)", "NVARCHAR(4000)", sql, flags=re.IGNORECASE)
    sql = textwrap.dedent(f"SET NOCOUNT ON;\n{sql.strip()}")
    return sql


def _split_sql_batch(sql: str):
    """
    Pisahkan query menjadi beberapa batch aman berdasarkan DECLARE, SELECT, SET, EXEC, dll.
    """
    sql = re.sub(r"\n+", "\n", sql.strip())
    parts = re.split(r";\s*(?=(DECLARE|SELECT|SET|EXEC|INSERT|UPDATE|DELETE)\b)", sql, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip()]

def _extract_pk_from_where(sql: str):
    """
    Ekstrak nama kolom PK dari klausa WHERE, misal:
    UPDATE ... WHERE user_id = ?
    → return 'user_id'
    """
    match = re.search(r"WHERE\s+([a-zA-Z0-9_]+)\s*=", sql, re.IGNORECASE)
    return match.group(1) if match else None
    
def run_query(sql, params=None, skip=0, take=None, server_key="server1"):
    import textwrap
    import re

    params = params or []
    result = {
        "message": "",
        "statuscode": 200,
        "totalcount": 0,
        "data": [],
        "skip": skip,
        "take": take,
        "columns": []
    }

    if not _is_safe_query(sql):
        return {"message": "Query tidak diperbolehkan", "statuscode": 403}

    conn = None
    cursor = None
    try:
        conn = get_connection(server_key)
        cursor = conn.cursor()
        sql = textwrap.dedent(f"SET NOCOUNT ON;\n{sql.strip()}")

        if re.match(r"^\s*DECLARE\s", sql, re.IGNORECASE):
            safe_sql = sql.replace("'", "''")
            sql = f"EXEC('{safe_sql}')"

        cursor.execute(sql, params)

        last_result = None
        while True:
            if cursor.description:
                last_result = {
                    "columns": [col[0] for col in cursor.description],
                    "rows": cursor.fetchall(),
                }
            if not cursor.nextset():
                break

        if last_result:
            columns = last_result["columns"]
            rows = last_result["rows"]
        else:
            columns, rows = [], []

        totalcount = len(rows)
        if take is not None and take != -1:
            rows = rows[skip:skip + take]
        elif take == -1:
            rows = rows[skip:]

        result.update({
            "data": [_trim_row(columns, row) for row in rows],
            "columns": columns,
            "totalcount": totalcount,
            "message": "Success",
        })
        return result

    except pyodbc.Error as e:
        logger.error("Query gagal: %s | error: %s", sql[:200], e)
        return {"message": f"Database error: {str(e)}", "statuscode": 500}

    except Exception as e:
        logger.exception("Internal error saat query")
        return {"message": f"Internal error: {str(e)}", "statuscode": 500}

    finally:
        try:
            if cursor: cursor.close()
            if conn: conn.close()
        except Exception:
            pass


def insert_query(sql, params=None, server_key="server1"):
    params = params or []
    if not _is_safe_query(sql):
        return {"message": "Query tidak diperbolehkan", "statuscode": 403}

    conn = None
    cursor = None
    try:
        conn = get_connection(server_key)
        cursor = conn.cursor()

        # Eksekusi INSERT
        cursor.execute(sql, params)
        conn.commit()

        # Ambil ID terakhir jika ada identity
        cursor.execute("SELECT SCOPE_IDENTITY()")
        last_id_row = cursor.fetchone()
        last_id = last_id_row[0] if last_id_row and last_id_row[0] is not None else None

        return {
            "message": f"Insert berhasil{f' dengan ID {last_id}' if last_id else ''}",
            "statuscode": 200,
            "last_id": last_id
        }

    except pyodbc.Error as e:
        logger.error("Insert gagal: %s | params: %s | error: %s", sql, params, e)
        return {"message": f"Database error: {str(e)}", "statuscode": 500}
    except Exception as e:
        logger.exception("Internal error saat insert")
        return {"message": f"Internal error: {str(e)}", "statuscode": 500}
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception:
            pass


def update_query(sql, params=None, server_key="server1"):
    """
    Jalankan query UPDATE, deteksi PK otomatis dari klausa WHERE.
    """
    params = params or []
    if not _is_safe_query(sql):
        return {"message": "Query tidak diperbolehkan", "statuscode": 403}

    conn = None
    cursor = None
    pk_value = None
    pk_field = _extract_pk_from_where(sql)

    # Ambil PK dari parameter terakhir (jika ada)
    if isinstance(params, (list, tuple)) and params:
        pk_value = params[-1]
    elif isinstance(params, dict) and pk_field and pk_field in params:
        pk_value = params[pk_field]

    try:
        conn = get_connection(server_key)
        cursor = conn.cursor()
        cursor.execute(sql, params)
        affected = cursor.rowcount
        conn.commit()
        return {
            "message": f"Update berhasil ({affected} baris)",
            "statuscode": 200,
            "affected": affected,
            "pk_field": pk_field,
            "pk": pk_value,
        }
    except pyodbc.Error as e:
        logger.error("Update gagal: %s | params: %s | error: %s", sql, params, e)
        return {"message": f"Database error: {str(e)}", "statuscode": 500}
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def delete_query(sql, params=None, server_key="server1"):
    """
    Jalankan query DELETE dan ambil PK otomatis dari klausa WHERE.
    """
    params = params or []
    if not _is_safe_query(sql):
        return {"message": "Query tidak diperbolehkan", "statuscode": 403}

    conn = None
    cursor = None
    pk_value = None
    pk_field = _extract_pk_from_where(sql)

    # Ambil PK dari parameter terakhir
    if isinstance(params, (list, tuple)) and params:
        pk_value = params[-1]
    elif isinstance(params, dict) and pk_field and pk_field in params:
        pk_value = params[pk_field]

    try:
        conn = get_connection(server_key)
        cursor = conn.cursor()
        cursor.execute(sql, params)
        affected = cursor.rowcount
        conn.commit()
        return {
            "message": f"Delete berhasil ({affected} baris)",
            "statuscode": 200,
            "affected": affected,
            "pk_field": pk_field,
            "pk": pk_value,
        }
    except pyodbc.Error as e:
        logger.error("Delete gagal: %s | params: %s | error: %s", sql, params, e)
        return {"message": f"Database error: {str(e)}", "statuscode": 500}
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


