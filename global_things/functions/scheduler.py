from global_things.functions.general import login_to_db
from datetime import datetime
from pypika import MySQLQuery as Query, Table, Criterion, functions as fn, Order
import requests
import time


def common_code_for_lms() -> tuple:
    connection = login_to_db()
    cursor = connection.cursor()

    common_codes = Table('common_codes')
    sql = Query.from_(
        common_codes
    ).select(
        common_codes.id,
        common_codes.value
    ).where(
        Criterion.any([
            common_codes.code == "induce.after.1.logon",
            common_codes.code == "induce.after.7.order",
            common_codes.code == "induce.after.9.order",
            common_codes.code == "induce.after.12.order"
        ])
    ).get_sql()
    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()

    return result


def send_aligo_scheduled_lms(phone, message):
    send_aligo = requests.post(
        # "https://nodejs.circlinplus.co.kr:444/aligo/message",
        "https://api.circlinplus.co.kr/api/aligo/message",
        json={
            "phone": phone,
            "message": message
        }
    ).json()

    return send_aligo['result']


def cron_job_send_lms():
    connection = login_to_db()
    cursor = connection.cursor()
    # lms_reservations = Table('lms_reservations')
    # users = Table('users')
    # orders = Table('orders')
    # order_subscriptions = Table('order_subscriptions')
    # subscriptions = Table('subscriptions')
    # common_codes = Table('common_codes')
    # logs = Table('logs')

    sql = f"""
        SELECT
--            lr.id,
           lr.scheduled_at,
           cc.code,
           lr.message,
--            o.id,
--            o.total_price,
--            os.subscription_id,
--            s.title,
           u.nickname,
           u.phone,
           u.subscription_id,
           u.subscription_started_at,
           u.subscription_expired_at,
           (
               SELECT COUNT(*) FROM logs l WHERE l.user_id = u.id AND l.type = 'user.logon'
           ) AS num_logon
        FROM
            users u
        INNER JOIN
                lms_reservations lr ON u.id = lr.user_id
        INNER JOIN
                common_codes cc ON lr.common_code_id = cc.id
        WHERE
            u.phone IS NOT NULL
        AND lr.deleted_at IS NULL
        AND (lr.scheduled_at between NOW() - INTERVAL 30 SECOND AND NOW() + INTERVAL 30 SECOND)"""
    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()

    result_list = []
    for data in result:
        dict_data = {
            'scheduled_at': data[0],
            'code': data[1],
            'message': data[2],
            'nickname': data[3],
            'phone': data[4],
            'subscription_id': data[5],
            'subscription_started_at': data[6],
            'subscription_expired_at': data[7],
            'num_logon': data[8]
        }
        result_list.append(dict_data)

    for data in result_list:
        # 다음과 같은 경우에는 발송하지 않는다.
        if data['subscription_id'] == 1 and data['code'] == 'induce.after.1.logon' and data['num_logon'] > 0:
            continue
        else:
            send_aligo_scheduled_lms(data['phone'], data['message'])

