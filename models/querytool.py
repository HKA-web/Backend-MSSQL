import pyodbc
import logging
import re
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
    """Trim string di hasil SELECT"""
    return {col: val.strip() if isinstance(val, str) else val for col, val in zip(columns, row)}


def _is_safe_query(sql):
    forbidden = ["DROP", "ALTER", "TRUNCATE"]
    sql_upper = sql.strip().upper()
    return not any(sql_upper.startswith(f) for f in forbidden)


def _is_complex_query(sql: str) -> bool:
    """
    Deteksi apakah query tergolong 'berat' atau kompleks.
    Kalau ya → pakai query COUNT terpisah.
    """
    sql_upper = sql.upper()
    keywords = ["JOIN", "WHERE", "GROUP BY", "UNION", "HAVING", "DISTINCT"]
    return any(k in sql_upper for k in keywords)


def _extract_pk_from_where(sql: str):
    """
    Ekstrak nama kolom PK dari klausa WHERE, misal:
    UPDATE ... WHERE user_id = ?
    → return 'user_id'
    """
    match = re.search(r"WHERE\s+([a-zA-Z0-9_]+)\s*=", sql, re.IGNORECASE)
    return match.group(1) if match else None
    
    
def run_query(sql, params=None, skip=0, take=None, server_key="server1"):
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

        # Tentukan apakah perlu query COUNT terpisah
        use_count_query = _is_complex_query(sql)

        totalcount = 0
        if use_count_query:
            try:
                count_sql = f"SELECT COUNT(*) AS total FROM ({sql}) AS subquery"
                cursor.execute(count_sql, params)
                totalcount = cursor.fetchone()[0]
            except Exception as e:
                logger.warning(f"Gagal hitung totalcount cepat: {e}")
                totalcount = 0

        # Jalankan query utama
        cursor.execute(sql, params)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        # Kalau tidak pakai count query, totalcount dihitung dari hasil fetch
        if not use_count_query:
            totalcount = len(rows)

        # Pagination manual
        if take is not None:
            rows = rows[skip:skip + take]
        else:
            rows = rows[skip:]

        result.update({
            "data": [_trim_row(columns, row) for row in rows],
            "columns": columns,
            "totalcount": totalcount,
            "message": "Success",
        })

    except pyodbc.Error as e:
        logger.error("Query gagal: %s | params: %s | error: %s", sql, params, e)
        return {"message": f"Database error: {str(e)}", "statuscode": 500}
    except Exception as e:
        logger.exception("Internal error saat query")
        return {"message": f"Internal error: {str(e)}", "statuscode": 500}
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception:
            pass

    return result


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


