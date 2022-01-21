from config.database import DB_CONFIG
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
def check_user(cursor, user_id):
  query = f"SELECT * FROM users WHERE id={user_id}"
  cursor.execute(query)
  user_id_tuple = cursor.fetchall()
  if len(user_id_tuple) == 0 or user_id_tuple == ():
    result = {'result': False}
    return result
  else:
    result = {'result': True}
    return result


# Check how many rows are in the result of query execution
def query_result_is_none(execution: tuple):
  if len(execution) == 0 or execution == ():
    return True
  else:
    return False
