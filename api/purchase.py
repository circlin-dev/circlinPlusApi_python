from global_things.constants import API_ROOT
from global_things.functions.slack import slack_error_notification, slack_purchase_notification
from global_things.functions.general import login_to_db, check_token, query_result_is_none
from global_things.functions.purchase import amount_to_be_paid, get_import_access_token
from global_things.constants import IMPORT_REST_API_KEY, IMPORT_REST_API_SECRET
from . import api
from flask import url_for, request
import json
import requests


@api.route('/purchase/read/<user_id>', methods=['GET'])
def read_purchase_record(user_id):
  """
  검증 조건 1: 존재하는 유저인지 확인
  검증 조건 2: 현재 구독기간이 끝나지 않은 플랜이 있는지 확인

  return: 현재 구독중인 플랜의 제목, 시작일, 마지막일
  """
  ip = request.headers["X-Forwarded-For"] # Both public & private.
  endpoint = API_ROOT + url_for('api.read_purchase_record', user_id=user_id)
  # token = request.headers['Authorization']

  try:
    connection = login_to_db()
  except Exception as e:
    error = str(e)
    result = {
      'result': False,
      'error': f'Server Error while connecting to DB: {error}'
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
    return json.dumps(result, ensure_ascii=False), 500

  cursor = connection.cursor()
  # 1. 유저 정보 확인
  # Verify user is valid or not.
  # is_valid_user = check_token(cursor, token)
  # if is_valid_user['result'] is False:
  #   connection.close()
  #   result = {
  #     'result': False,
  #     'error': f"Invalid request: Unauthorized token or no such user({user_id})"
  #   }
  #   slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
  #   return json.dumps(result, ensure_ascii=False), 401
  # elif is_valid_user['result'] is True:
  #   pass

  # 2. 해당 유저에게 구독중인(기간이 만료되지 않은) 플랜이 있는지 확인
  query = f"\
    SELECT DISTINCT \
          p.id, \
          sp.title, \
          sp.total_price, \
          p.start_date, \
          p.expire_date, \
          p.deleted_at, \
          p.buyer_email, \
          p.buyer_name, \
          p.buyer_tel, \
          p.status, \
          pd.post_code, \
          pd.address, \
          pd.comment \
      from \
          purchases p, \
          subscribe_plans sp, \
          purchase_delivery pd \
    WHERE \
          sp.id = p.user_id \
      AND p.id = pd.purchase_id \
      AND p.user_id = {user_id} \
    ORDER BY start_date"

  cursor.execute(query)
  purchase_records = cursor.fetchall()
  if query_result_is_none(purchase_records) is True:
    connection.close()
    result = {
      'result': True,
      'purchase_data': None
    }
    return json.dumps(result, ensure_ascii=False), 200
  else:
    result_list = []
    for data in purchase_records:
      if data[5] is not None:
        deleted_at = data[5].strftime("%Y-%m-%d %H:%M:%S")
      else:
        deleted_at = data[5]
      each_dict = {"index": data[0],
                   "payment_information": {
                     "plan_title": data[1],
                     "total_price": data[2],  # 정상가
                     "start_date": data[3].strftime("%Y-%m-%d %H:%M:%S"),
                     "expire_date": data[4].strftime("%Y-%m-%d %H:%M:%S"),
                     "deleted_at": deleted_at,
                     "buyer_email": data[6],  # 결제자 이메일
                     "buyer_name": data[7],  # 결제자 이름
                     "buyer_phone": data[8],  # 결제자 전화번호
                     "status": data[9],
                     "installment": "일시불",  # 이용권
                     "interest_free_installment": "해당없음",  # 무이자 할부 여부(일시불은 무조건 해당 없음
                     "option": "비렌탈"  # 선택옵션
                   },
                   "delivery_information": {
                     "recipient_postcode": data[10],  # 배송지 우편번호
                     "recipient_address": data[11],  # 배송지 주소
                     "recipient_comment": data[12],
                   }
                   }
      result_list.append(each_dict)
    result_dict = {
      "result": True,
      "purchase_data": result_list
    }
    return json.dumps(result_dict, ensure_ascii=False), 200


@api.route('/purchase/add', methods=['POST'])
def add_purchase():
  # ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
  ip = request.headers["X-Forwarded-For"]  # Both public & private.
  endpoint = API_ROOT + url_for('api.add_purchase')  # '/api/purchase/read/{user_id}'
  token = request.headers['Authorization']
  parameters = json.loads(request.get_data(), encoding='utf-8')

  user_id = parameters['user_id']
  period = int(parameters['subscription_period'])
  payment_info = parameters['payment_info']  # Value format: yyyy-Www(Week 01, 2017 ==> "2017-W01")
  delivery_info = parameters['delivery_info']  # int  # for plan_id 'purchases'
  # equipment_info = parameters('equipment_info')  # boolean  # for plan_id at table 'purchases'

  # 결제 정보 변수
  plan_title = payment_info['name']
  total_payment = payment_info['amount']
  imp_uid = payment_info['imp_uid']
  merchant_uid = payment_info['merchant_uid']

  # 배송 정보 변수
  recipient_name = delivery_info['recipient_name'].strip()  # 결제자 이름
  post_code = delivery_info['post_code'].strip()  # 스타터 키트 배송지 주소(우편번호)
  address = delivery_info['address'].strip()  # 스타터 키트 배송지 주소(주소)
  recipient_phone = delivery_info['recipient_phone'].strip()  # 결제자 휴대폰 번호

  comment = delivery_info['comment'].strip()  # 배송 요청사항

  # 기구 정보 변수

  # 구독 기간 정보 변수
  subscription_days = 0
  if period == 1:
    subscription_days = 30
  elif period == 3:
    subscription_days = 90
  elif period == 6:
    subscription_days = 180
  elif period == 12:
    subscription_days = 365

    if not(user_id and period and recipient_phone and imp_uid and merchant_uid):
      result = {
        'result': False,
        'error': f'Missing data in request.',
        'values': {
          'period': period,
          'user_id': user_id,
          'recipient_phone': recipient_phone,
          'imp_uid': imp_uid,
          'merchant_uid': merchant_uid,
        }
      }
      return json.dumps(result, ensure_ascii=False), 400

  # 1. 유저 정보 확인
  try:
    connection = login_to_db()
  except Exception as e:
    error = str(e)
    result = {
      'result': False,
      'error': f'Server Error while connecting to DB: {error}'
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
    return json.dumps(result, ensure_ascii=False), 500

  cursor = connection.cursor()

  # Verify user is valid or not.
  is_valid_user = check_token(cursor, user_id, token)
  if is_valid_user['result'] is False:
    connection.close()
    result = {
      'result': False,
      'error': f"Invalid request: Unauthorized token or no such user({user_id})"
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
    return json.dumps(result, ensure_ascii=False), 401
  elif is_valid_user['result'] is True:
    pass

  # 2. 결제 정보 조회(import)
  get_token = json.loads(get_import_access_token(IMPORT_REST_API_KEY, IMPORT_REST_API_SECRET))
  if get_token['result'] is False:
    result = {'result': False,
              'error': f'Failed to get import access token at server(message: {get_token["message"]})'}
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=get_token['message'])
    return json.dumps(result, ensure_ascii=False), 500
  else:
    access_token = get_token['access_token']

  payment_validation_import = requests.get(
    f"https://api.iamport.kr/payments/{payment_info['imp_uid']}",
    headers={"Authorization": access_token}
  ).json()
  payment_status = payment_validation_import['response']['status']
  user_paid_amount = int(payment_validation_import['response']['amount'])
  user_subscribed_plan = payment_validation_import['response']['name']
  buyer_email = payment_validation_import['response']['buyer_email']
  buyer_name = payment_validation_import['response']['buyer_name']
  buyer_tel = payment_validation_import['response']['buyer_tel']

  # 3. 결제 정보 검증(DB ~ import 결제액)
  """
  보완사항
  (1) 결제 검증 수단: payment_info의 name값으로만 비교 중.
    ==> 기구 렌탈 여부, 할인권 적용, 구독 기간 등의 정보 고려하여 올바르게 계산하도록 보완해야 함!
  (2) 결제 검증 수단: sales_price와 user_paid_amount의 비교는 테스트 결제액인 1004원으로 비교중.
    ==> 결제 가격 체계를 보완하여 1004원을 실제 판매가인 sales_price로 변경해야 함!
  (3) 기존 결제한 플랜의 기간이 만료되지 않은 상태에서의 결제 막기 
    ==> IMPORT 모듈을 이용하는 현재 구조상 클라이언트에서 처리해야 할듯
  """

  query = "SELECT sales_price FROM subscribe_plans WHERE title=%s"
  cursor.execute(query, user_subscribed_plan)
  sales_price = cursor.fetchall()

  if query_result_is_none(sales_price) is True:
    connection.close()
    result = {
      'result': False,
      'error': f': Error while validating payment information: Subscription plan "{user_subscribed_plan}" does not exist, but user purchased it. Check product list at IMPORT.'
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
    return json.dumps(result, ensure_ascii=False), 403
  else:
    pass

  total_amount = amount_to_be_paid()
  if total_amount != user_paid_amount:  # Test value: 1004
    connection.close()

    # Failed validation: Request import to cancel the payment.

    result = {
      'result': False,
      'error': f': Error while validating payment information: For plan "{user_subscribed_plan}", actual sales price is "{total_amount}", but user paid "{user_paid_amount}". Automatically cancel this payment(imp_uid: {imp_uid}, merchant_uid: {merchant_uid}).'
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
    return json.dumps(result, ensure_ascii=False), 403
  else:
    if payment_status == 'paid' or payment_status == 'failed':
      pass
    else:
      connection.close()
      result = {
        'result': False,
        'error': f': Error while validating payment information: Payment status is "{payment_status}". Payment process will continue only when the status value is "paid".'
      }
      slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
      return json.dumps(result, ensure_ascii=False), 403

  # 4. 결제 정보(-> purchases), 배송 정보(purchase_delivery) 저장
  """
  기구 신청을 했을 경우, 기구 신청 내역을 저장하는 쿼리를 만들어야 함!
  """
  query = f"INSERT INTO purchases( \
                                  user_id, plan_id, \
                                  start_date, expire_date, \
                                  total_payment, imp_uid, \
                                  merchant_uid, status, \
                                  buyer_email, buyer_name, buyer_tel) \
                          VALUES(%s, (SELECT id FROM subscribe_plans WHERE title=%s), \
                                (SELECT NOW()), (SELECT NOW() + INTERVAL {subscription_days} DAY), \
                                %s, %s, \
                                %s, %s, \
                                %s, %s, %s)"
  values = (int(user_id), plan_title,
            user_paid_amount, imp_uid,
            merchant_uid, payment_status,
            buyer_email, buyer_name, buyer_tel)
  # user_id, payment_info, delivery_info
  try:
    cursor.execute(query, values)
    purchase_id = cursor.lastrowid
  except Exception as e:
    connection.rollback()
    connection.close()
    error = str(e)
    result = {
      'result': False,
      'error': f'Server error while executing INSERT query(purchases): {error}'
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
    return json.dumps(result, ensure_ascii=False), 500

  query = f"""INSERT INTO purchase_delivery(
                                  purchase_id, post_code,
                                  address, recipient_name, 
                                  recipient_phone, comment)
                          VALUES(%s, %s,
                                %s, %s,
                                %s, %s)"""
  values = (purchase_id, post_code,
            address, recipient_name,
            recipient_phone, comment)
  try:
    cursor.execute(query, values)
  except Exception as e:
    connection.rollback()
    connection.close()
    error = str(e)
    result = {
      'result': False,
      'error': f'Server error while executing INSERT query(purchase_delivery): {error}'
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
    return json.dumps(result, ensure_ascii=False), 500

  # 5. 채팅방 생성 or 조회하여 채팅방 id 리턴
  """
  1. 매니저 할당(매니저 선정 로직: 초기에는 '성별'만 고려)
  2. chat_users에서 user와 manager의 chat_room_id의 교집합(= 이미 만들어진 채팅방)이 있는지 확인한다.
  3. 없으면 새 채팅룸을 생성하고, 있으면 기존 채팅룸 id를 조회한다.
  4. 채팅룸 id를 리턴한다.
  """

  query = f"""
    SELECT
          data
      FROM
          user_questions
    WHERE
          user_id={user_id}
    ORDER BY id DESC LIMIT 1"""
  cursor.execute(query)
  answer_data = cursor.fetchall()
  if query_result_is_none(answer_data) is True:
    connection.close()
    result = {
      'result': False,
      'error': f': No pre-survey data of user({user_id})'
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
    return json.dumps(result, ensure_ascii=False), 403

  user_sex = json.loads(answer_data[0].replace("\\", "\\\\"), strict=False)['sex']

  if user_sex == 'M':
    manager_id = 1  # 1 = 대표님, 2 = 희정님
  else:
    manager_id = 2

  query = f"""
    SELECT 
        manager.chat_room_id
    FROM
        chat_users customer, chat_users manager
    WHERE
        customer.chat_room_id = manager.chat_room_id 
        AND customer.user_id = {user_id}
        AND manager.user_id = {manager_id}"""

  cursor.execute(query)
  existing_chat_room = cursor.fetchall()

  if len(existing_chat_room) == 0 or existing_chat_room == ():
    query = "INSERT INTO chat_rooms(created_at, updated_at) VALUES((SELECT NOW()), (SELECT NOW()))"
    try:
      cursor.execute(query)
      chat_room_id = cursor.lastrowid
    except Exception as e:
      connection.rollback()
      connection.close()
      error = str(e)
      result = {
        'result': False,
        'error': f'Server Error while executing INSERT query(chat_rooms): {error}'
      }
      slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
      return json.dumps(result, ensure_ascii=False), 500

    query = f"INSERT INTO chat_users(created_at, updated_at, chat_room_id, user_id) \
                    VALUES(NOW(), NOW(), {chat_room_id}, {manager_id}), \
                          (NOW(), NOW(), {chat_room_id}, {user_id})"
    try:
      cursor.execute(query)
    except Exception as e:
      connection.rollback()
      connection.close()
      error = str(e)
      result = {
        'result': False,
        'error': f'Server Error while executing INSERT query(chat_users): {error}'
      }
      slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
      return json.dumps(result, ensure_ascii=False), 500
  else:
    chat_room_id = existing_chat_room[0][0]

  connection.commit()
  slack_purchase_notification(cursor, user_id, manager_id, purchase_id)
  connection.close()
  result = {
    'result': True,
    'chat_room_id': chat_room_id
  }

  return json.dumps(result, ensure_ascii=False), 201


@api.route('/purchase/update_notification', methods=['POST'])
def update_payment_status_by_webhook():
  """
  POST parameter
  * imp_uid
  * merchant_uid
  * status:
    - 결제가 승인되었을 때(모든 결제 수단): paid
    - 가상계좌가 발급되었을 때: ready
    - 가상계좌에 결제 금액이 입금되었을 때: paid
    - 예약결제가 시도되었을 때: paid / failed
    - 관리자 콘솔에서 환불되었을 때: cancelled
  :return:
  """
  # ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
  ip = request.headers["X-Forwarded-For"]  # Both public & private.
  endpoint = API_ROOT + url_for('api.update_payment_status_by_webhook')

  try:
    connection = login_to_db()
  except Exception as e:
    error = str(e)
    result = {
      'result': False,
      'error': f'Server Error while connecting to DB: {error}'
    }
    slack_error_notification(user_ip=ip, api=endpoint, error_log=result['error'])
    return json.dumps(result, ensure_ascii=False), 500
  cursor = connection.cursor()

  parameters = json.loads(request.get_data(), encoding='utf-8')

  imp_uid = parameters['imp_uid']
  merchant_uid = parameters['merchant_uid']
  updated_status = parameters['status']

  # 2. import에서 결제 정보 조회
  get_token = json.loads(get_import_access_token(IMPORT_REST_API_KEY, IMPORT_REST_API_SECRET))
  if get_token['result'] is False:
    result = {'result': False,
              'error': f'Failed to get import access token at server(message: {get_token["message"]})'}
    slack_error_notification(user_ip=ip, api=endpoint, error_log=get_token['message'])
    return json.dumps(result, ensure_ascii=False), 500
  else:
    access_token = get_token['access_token']

  payment_validation_import = requests.get(
    f"https://api.iamport.kr/payments/{imp_uid}",
    headers={"Authorization": access_token}
  ).json()
  payment_status = payment_validation_import['response']['status']
  import_paid_amount = int(payment_validation_import['response']['amount'])

  # 3. DB에서 결제 내역 조회
  query = "SELECT total_payment FROM purchases WHERE imp_uid=%s AND merchant_uid=%s"
  values = (imp_uid, merchant_uid)
  cursor.execute(query, values)
  db_paid_amount = cursor.fetchall()[0][0]

  if int(db_paid_amount) == int(import_paid_amount):
    if updated_status == 'cancelled':
      query = f"""
        UPDATE 
              purchases
          SET 
              status=%s, 
              deleted_at=(SELECT NOW())
        WHERE 
              imp_uid=%s 
          AND merchant_uid=%s"""
      values = (updated_status, imp_uid, merchant_uid)
      cursor.execute(query, values)
    else:
      pass
    connection.commit()
    connection.close()

    result = {'result': True}
    return json.dumps(result, ensure_ascii=False), 201
  else:
    connection.close()
    result = {
      'result': False,
      'error': f': Error while validating payment information: Paid amount that was sent from IMPORT is {import_paid_amount} WON(imp_uid: {imp_uid}), but purchase record from DB says {db_paid_amount} WON.'
    }
    slack_error_notification(user_ip=ip, api=endpoint, error_log=result['error'])
    return json.dumps(result, ensure_ascii=False), 403

