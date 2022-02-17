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


def validation_subscription_order(purchase_information: tuple, discount_information: tuple):
    """ user_paid_amount는 검증 로직 완료 시 반드시 빠져야 할 부분이다."""
    # 1원 단위에서 내림 계산

    # method == percent: price * (1 - (value * 0.01)) == sales_price (user_paid_amount) # 1의 자리에서 반올림
    # method == amount: price -
    # method == None: sales_price == user_paid_amount

    subscription_id = purchase_information[0][0]
    subscription_type = purchase_information[0][1]
    subscription_original_price = purchase_information[0][2]
    subscription_price = purchase_information[0][3]
    subscription_period_days = purchase_information[0][4]

    discount_id = discount_information[0][0]
    discount_type = discount_information[0][1]
    method = discount_information[0][2]
    value = discount_information[0][3]
    discount_code = discount_information[0][4]

    # 개발자 할인코드 테스트용
    if discount_code == "ASDASDFWJNSF456":
        to_be_paid = 1004
        return to_be_paid, subscription_original_price, discount_id

    if method == 'percent':
        to_be_paid = round(subscription_original_price * (1 - (value * 0.01)), -1)  # 1의 자리에서 '반올림'
        return to_be_paid, subscription_original_price, discount_id
    elif method == 'amount':
        to_be_paid = subscription_original_price - value
        return to_be_paid, subscription_original_price, discount_id
    else:
        return subscription_original_price, subscription_original_price, discount_id


def validation_equipment_delivery(equipment_information: dict, discount_information: dict):
    first_delivery_discount = discount_information['first_delivery_discount']
    is_first_delivery = first_delivery_discount['is_first']
    first_delivery_discount_method = first_delivery_discount['method']
    first_delivery_discount_value = first_delivery_discount['value']

    area_discount = discount_information['area_discount']
    area_discount_id = area_discount['id']
    area_discount_method = area_discount['method']
    area_discount_value = area_discount['value']
    equipment_delivery_fee = equipment_information['delivery_fee']

    if is_first_delivery is True:
        if area_discount_method == 'amount' and first_delivery_discount_method['method'] == 'percent':
            total_fee = equipment_delivery_fee - first_delivery_discount_value
            to_be_paid = round(total_fee * (1 - (first_delivery_discount_value * 0.01)), -1)
            return to_be_paid, total_fee, area_discount_id, first_delivery_discount_value
    else:
        total_fee = equipment_delivery_fee - area_discount_value
        return total_fee, total_fee, area_discount_id, first_delivery_discount_value

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
