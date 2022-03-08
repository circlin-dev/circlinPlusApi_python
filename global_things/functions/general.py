from config.database import DB_CONFIG
import hashlib
import pymysql
from pypika import MySQLQuery as Query, Criterion, Interval, Table, Field, Order, functions as fn
import re

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
def check_user_token(cursor, bearer_token):
    token = bearer_token.split(' ')[-1]
    hashed_bearer_token = hashlib.sha256(token.encode()).hexdigest()
    personal_access_tokens = Table('personal_access_tokens')

    sql = Query.from_(
        personal_access_tokens
    ).select(
        personal_access_tokens.tokenable_id
    ).where(
        personal_access_tokens.token == hashed_bearer_token
    ).get_sql()

    cursor.execute(sql)
    verified_user_id = cursor.fetchall()
    if len(verified_user_id) == 0 or verified_user_id == ():
        result = {'result': False, 'user_id': None}
        return result
    else:
        result = {'result': True, 'user_id': verified_user_id[0][0]}
        return result


# Check how many rows are in the result of query execution
def query_result_is_none(execution: tuple):
    if len(execution) == 0 or execution == ():
        return True
    else:
        return False


# Parsing strings...
def parse_for_mysql(strings: str):
    if strings is None:
        return strings
    else:
        parsed_strings = re.sub('\n', ' ', strings)
        parsed_strings = re.sub('\t', ' ', parsed_strings)
        parsed_strings = re.sub('\b', ' ', parsed_strings)
        parsed_strings = re.sub("‘", "\'", parsed_strings)
        parsed_strings = re.sub("’", "\'", parsed_strings)
        parsed_strings = re.sub('"', "\'", parsed_strings)
        parsed_strings = re.sub('“', "\'", parsed_strings)
        parsed_strings = re.sub('”', "\'", parsed_strings)
        parsed_strings = parsed_strings.lstrip()
        parsed_strings = parsed_strings.rstrip()

        return parsed_strings

