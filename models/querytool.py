import pyodbc
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Ambil konfigurasi SQL Server dari settings
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


def run_query(sql, params=None, skip=0, take=None, server_key="server1"):
    params = params or []
    result = {"message": "", "statuscode": 200, "totalcount": 0, "data": [], "skip": skip, "take": take, "kolom": []}

    if not _is_safe_query(sql):
        return {"message": "Query tidak diperbolehkan", "statuscode": 403}

    try:
        conn = get_connection(server_key)
        cursor = conn.cursor()
        cursor.execute(sql, params)
        columns = [desc[0] for desc in cursor.description]

        rows = cursor.fetchall()
        if take is not None:
            rows = rows[skip:skip + take]
        else:
            rows = rows[skip:]

        result.update({
            "data": [_trim_row(columns, row) for row in rows],
            "kolom": columns,
            "totalcount": len(rows),
            "message": "Query berhasil",
        })

    except pyodbc.Error as e:
        logger.error("Query gagal: %s | params: %s | error: %s", sql, params, e)
        return {"message": f"Database error: {str(e)}", "statuscode": 500}
    except Exception as e:
        logger.exception("Internal error saat query")
        return {"message": f"Internal error: {str(e)}", "statuscode": 500}
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

    return result


def insert_query(sql, params=None, server_key="server1"):
    params = params or []
    if not _is_safe_query(sql):
        return {"message": "Query tidak diperbolehkan", "statuscode": 403}

    try:
        conn = get_connection(server_key)
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return {"message": "Insert berhasil", "statuscode": 200}

    except pyodbc.Error as e:
        logger.error("Insert gagal: %s | params: %s | error: %s", sql, params, e)
        return {"message": f"Database error: {str(e)}", "statuscode": 500}
    except Exception as e:
        logger.exception("Internal error saat insert")
        return {"message": f"Internal error: {str(e)}", "statuscode": 500}
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


def update_query(sql, params=None, server_key="server1"):
    params = params or []
    if not _is_safe_query(sql):
        return {"message": "Query tidak diperbolehkan", "statuscode": 403}

    try:
        conn = get_connection(server_key)
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return {"message": "Update berhasil", "statuscode": 200}

    except pyodbc.Error as e:
        logger.error("Update gagal: %s | params: %s | error: %s", sql, params, e)
        return {"message": f"Database error: {str(e)}", "statuscode": 500}
    except Exception as e:
        logger.exception("Internal error saat update")
        return {"message": f"Internal error: {str(e)}", "statuscode": 500}
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


def delete_query(sql, params=None, server_key="server1"):
    params = params or []
    if not _is_safe_query(sql):
        return {"message": "Query tidak diperbolehkan", "statuscode": 403}

    try:
        conn = get_connection(server_key)
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return {"message": "Delete berhasil", "statuscode": 200}

    except pyodbc.Error as e:
        logger.error("Delete gagal: %s | params: %s | error: %s", sql, params, e)
        return {"message": f"Database error: {str(e)}", "statuscode": 500}
    except Exception as e:
        logger.exception("Internal error saat delete")
        return {"message": f"Internal error: {str(e)}", "statuscode": 500}
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass
