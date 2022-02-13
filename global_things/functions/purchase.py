from global_things.functions.general import login_to_db
from global_things.functions.slack import slack_error_notification
import json
from pypika import MySQLQuery as Query, Table, Order
import requests

def get_import_access_token(api_key: str, api_secret: str):
    response = requests.post(
        "https://api.iamport.kr/users/getToken",
        json={
            "imp_key": api_key,
            "imp_secret": api_secret
        }).json()
    code = response['code']
    if code == 0:
        result = {'result': True,
                  'access_token': response['response']['access_token'],
                  'status_code': 200}
        return json.dumps(result, ensure_ascii=False)
    else:
        result = {'result': False,
                  'message': response['message'],
                  'status_code': 400}
        return json.dumps(result, ensure_ascii=False)


def amount_to_be_paid(subscription_information):
    """ user_paid_amount는 검증 로직 완료 시 반드시 빠져야 할 부분이다."""
    # 1원 단위에서 내림 계산

    # method == percent: price * (1 - (value * 0.01)) == sales_price (user_paid_amount) # 1의 자리에서 반올림
    # method == amount: price -
    # method == None: sales_price == user_paid_amount
    subscription_id, subscription_title, price, sales_price, period_days, discount_id, discount_title, method, value = subscription_information[0]

    if method == 'percent':
        to_be_paid = round(price * (1 - (value * 0.01)), -1)  # 1의 자리에서 '반올림'
        return to_be_paid, discount_id
    elif method == '':
        to_be_paid = price - value
        return to_be_paid, discount_id
    else:
        return sales_price, discount_id


def request_import_refund(access_token: str, imp_uid: str, merchant_uid: str, amount: int, checksum: int, reason: str):
    response = requests.post(
        "https://api.iamport.kr/payments/cancel",
        headers={"Content-Type": "application/json", "Authorization": access_token},
        json={
            "reason": reason,
            "imp_uid": imp_uid,
            "merchant_uid": merchant_uid,
            "amount": amount,  # 미입력 시 전액 환불됨
            # "checksum": checksum,  # 환불 가능금액: 부분환불이 도입될 경우 DB상의 '현재 환불 가능액'을 체크할 것.
        }).json()
    return response
