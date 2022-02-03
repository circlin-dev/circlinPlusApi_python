import json
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


def amount_to_be_paid(plan_name: str):
    """
    Must add purchase options as parameter!

    :return: Total amount to be paid(int).
    Calculate sales price by purchase options.
    """
    if plan_name == "써클인플러스 1개월 회원권":
        return 60000  # 60000/month
    elif plan_name == "써클인플러스 3개월 회원권":
        return 89700  # 29900/month
    elif plan_name == "써클인플러스 6개월 회원권":
        return 149400  # 24900/month
    elif plan_name == "써클인플러스 12개월 회원권":
        return 238800  # 19900/month
    else:
        return None


def request_import_refund(access_token: str, imp_uid: str, merchant_uid: str, amount: int, checksum: int, reason: str):
    response = requests.post(
        "https://api.iamport.kr/payments/cancel",
        headers={"Content-Type": "application/json", "Authorization": access_token},
        json={
            "reason": reason,
            "imp_uid": imp_uid,
            "merchant_uid": merchant_uid,
            "amount": amount,  # 미입력 시 전액 환불됨
            "checksum": checksum,  # 환불 가능금액: 부분환불이 도입될 경우 DB상의 '현재 환불 가능액'을 체크할 것.
        }).json()
    code = response['code']
    return code
