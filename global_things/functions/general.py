from config.database import DB_CONFIG
import hashlib
import pymysql


# Connection to database.
def login_to_db():
    conn = pymysql.connect(
        user=DB_CONFIG['user'],
        passwd=DB_CONFIG['password'],
        host=DB_CONFIG['host'],
        db=DB_CONFIG['database'],
        charset=DB_CONFIG['charset'])

    return conn


# User verification by exploring user table.
def check_session(cursor, session_id):
    hashed_session_id = hashlib.sha256(session_id.encode()).hexdigest()

    query = f"SELECT id, user_id FROM sessions WHERE id=%s"
    values = (hashed_session_id)
    cursor.execute(query, values)
    user_session = cursor.fetchall()

    if len(user_session) == 0 or user_session == ():
        result = {'result': False, 'user_id': None}
        return result
    elif user_session[0][0] != hashed_session_id:
        result = {'result': False, 'user_id': None}
        return result
    else:
        result = {'result': True, 'user_id': user_session[0][1]}
        return result


# Check how many rows are in the result of query execution
def query_result_is_none(execution: tuple):
    if len(execution) == 0 or execution == ():
        return True
    else:
        return False
