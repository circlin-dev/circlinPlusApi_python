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
def check_token(cursor, token):
  hashed_token = hashlib.sha256(token.encode()).hexdigest()

  query = f"SELECT tokenable_id, token FROM personal_access_tokens WHERE token=%s"
  values = (hashed_token)
  cursor.execute(query, values)
  personal_token = cursor.fetchall()

  if len(personal_token) == 0 or personal_token == ():
    result = {'result': False}
    return result
  elif personal_token != hashed_token:
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
