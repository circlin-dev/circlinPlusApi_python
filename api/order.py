from global_things.constants import API_ROOT
from global_things.error_handler import HandleException
from global_things.functions.slack import slack_error_notification, slack_purchase_notification
from global_things.functions.general import login_to_db, check_user_token, query_result_is_none
from global_things.functions.order import validation_subscription_order, validation_equipment_delivery, get_import_access_token, request_import_refund
from global_things.functions.trial import manager_by_gender
from global_things.constants import IMPORT_REST_API_KEY, IMPORT_REST_API_SECRET
from . import api
from flask import url_for, request
import json
import requests
from pypika import MySQLQuery as Query, Criterion, Table, Order, Interval, functions as fn


@api.route('/assign-manager', methods=['POST'])
def create_chat_with_manager():
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.create_chat_with_manager')
    # user_token = request.headers.get('Authorization')
    parameters = json.loads(request.get_data(), encoding='utf-8')
    user_id = int(parameters['user_id'])
    order_id = parameters['order_id']  # null or int
    """Define tables required to execute SQL."""
    user_questions = Table('user_questions')
    customers = Table('chat_users')
    managers = Table('chat_users')
    chat_rooms = Table('chat_rooms')
    chat_users = Table('chat_users')
    users = Table('users')

    connection = login_to_db()
    cursor = connection.cursor()
    # verify_user = check_user_token(cursor, user_token)
    # if verify_user['result'] is False:
    #     connection.close()
    #     message = 'No token at request header.' if user_token is None else 'Unauthorized user.'
    #     result = {
    #         'result': False,
    #         'message': message
    #     }
    # user_id = verify_user['user_id']
    # user_nickname = verify_user['user_nickname']

    sql = Query.from_(
        users
    ).select(
        users.nickname,
        users.phone
    ).where(
        Criterion.all([
            users.id == user_id
        ])
    ).get_sql()
    cursor.execute(sql)
    user_information = cursor.fetchall()
    user_nickname, user_phone = user_information[0]

    sql = Query.from_(
        user_questions
    ).select(
        user_questions.data
    ).where(
        user_questions.user_id == user_id
    ).orderby(
        user_questions.id, order=Order.desc
    ).limit(1).get_sql()

    cursor.execute(sql)
    answer_data = cursor.fetchall()
    if query_result_is_none(answer_data) is True:
        connection.close()
        result = {
            'result': False,
            'error': f': No pre-survey answer data of user({user_id})'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], method=request.method, status_code=403)
        return json.dumps(result, ensure_ascii=False), 403

    gender = json.loads(answer_data[0][0].replace("\\", "\\\\"), strict=False)['gender']

    manager_id = manager_by_gender(gender)

    sql = Query.from_(
        customers
    ).select(
        customers.chat_room_id
    ).join(
        managers
    ).on(
        customers.chat_room_id == managers.chat_room_id
    ).where(
        Criterion.all([
            customers.user_id == user_id,
            managers.user_id == manager_id
        ])
    ).get_sql()
    cursor.execute(sql)
    existing_chat_room = cursor.fetchall()

    if len(existing_chat_room) == 0 or existing_chat_room == ():
        sql = Query.into(
            chat_rooms
        ).columns(
            chat_rooms.created_at,
            chat_rooms.updated_at
        ).insert(
            fn.Now(),
            fn.Now()
        ).get_sql()
        try:
            cursor.execute(sql)
            connection.commit()
            chat_room_id = cursor.lastrowid
        except Exception as e:
            connection.rollback()
            connection.close()
            raise HandleException(user_ip=ip,
                                  nickname=user_nickname,
                                  user_id=user_id,
                                  api=endpoint,
                                  error_message=f'Server Error while making chat_rooms: {str(e)}',
                                  query=sql,
                                  method=request.method,
                                  status_code=500,
                                  payload=None,
                                  result=False)
        try:
            if order_id is None:
                sql = Query.into(
                    chat_users
                ).columns(
                    chat_users.created_at,
                    chat_users.updated_at,
                    chat_users.chat_room_id,
                    chat_users.user_id
                ).insert(
                    (fn.Now(), fn.Now(), chat_room_id, user_id),  # 무료체험: 채팅방 개설 시 유저만 입장시킴.
                    (fn.Now(), fn.Now(), chat_room_id, manager_id)
                ).get_sql()
            else:
                sql = Query.into(
                    chat_users
                ).columns(
                    chat_users.created_at,
                    chat_users.updated_at,
                    chat_users.chat_room_id,
                    chat_users.user_id
                ).insert(
                    (fn.Now(), fn.Now(), chat_room_id, manager_id),  # 유료 결제: 채팅방 개설 시 유저 & 매니저 함께 입장시킴.
                    (fn.Now(), fn.Now(), chat_room_id, user_id)
                ).get_sql()
            cursor.execute(sql)
            connection.commit()
            connection.close()
        except Exception as e:
            connection.rollback()
            connection.close()
            raise HandleException(user_ip=ip,
                                  nickname=user_nickname,
                                  user_id=user_id,
                                  api=endpoint,
                                  error_message=f'Server Error while making chat_rooms: {str(e)}',
                                  query=sql,
                                  method=request.method,
                                  status_code=500,
                                  payload=None,
                                  result=False)
    else:
        connection.close()
        result = {
            'result': True,
            'manager_id': manager_id,  # 28 = 대표님, 18 = 희정님
            'message': 'Chatroom already exists.'
        }
        return json.dumps(result, ensure_ascii=False), 200

    # if order_id is not None:
    #     slack_purchase_notification(cursor, user_id, user_nickname, user_phone, order_id)
    #     # slack_purchase_notification(cursor, user_id, user_nickname, user_phone, order_id)
    # else:
    #     pass
    result = {
        'result': True,
        'manager_id':  manager_id,  # 28 = 대표님, 18 = 희정님
        'message': 'Created a new chatroom.'
    }
    return json.dumps(result, ensure_ascii=False), 201


# @api.route('/purchase/<user_id>', methods=['GET'])
# def read_purchase_record(user_id):
#     """
#     검증 조건 1: 존재하는 유저인지 확인
#     검증 조건 2: 현재 구독기간이 끝나지 않은 플랜이 있는지 확인
#
#     return: 현재 구독중인 플랜의 제목, 시작일, 마지막일
#     """
#     ip = request.headers["X-Forwarded-For"] # Both public & private.
#     endpoint = API_ROOT + url_for('api.read_purchase_record', user_id=user_id)
#     # token = request.headers['Authorization']
#     """Define tables required to execute SQL."""
#     purchases = Table('purchases')
#     subscribe_plans = Table('subscriptions')
#
#     try:
#         connection = login_to_db()
#     except Exception as e:
#         error = str(e)
#         result = {
#             'result': False,
#             'error': f'Server Error while connecting to DB: {error}'
#         }
#         slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], method=request.method)
#         return json.dumps(result, ensure_ascii=False), 500
#
#     cursor = connection.cursor()
#     # 1. 유저 정보 확인
#     # Verify user is valid or not.
#     # is_valid_user = check_token(cursor, token)
#     # if is_valid_user['result'] is False:
#     #   connection.close()
#     #   result = {
#     #     'result': False,
#     #     'error': f"Invalid request: Unauthorized token or no such user({user_id})"
#     #   }
#     #   slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], method=request.method)
#     #   return json.dumps(result, ensure_ascii=False), 401
#     # elif is_valid_user['result'] is True:
#     #   pass
#
#     # 2. 해당 유저에게 구독중인(기간이 만료되지 않은) 플랜이 있는지 확인
#     sql = Query.from_(
#         purchases
#     ).select(
#         purchases.id.as_('purchase_id'),
#         subscribe_plans.title,
#         subscribe_plans.price,
#         purchases.total_payment,
#         purchases.user_id.as_('user_id'),
#         purchases.start_date,
#         purchases.expire_date,
#         purchases.deleted_at,
#         purchases.buyer_email,
#         purchases.buyer_name,
#         purchases.buyer_tel,
#         purchases.status
#     ).join(
#         subscribe_plans
#     ).on(
#         subscribe_plans.id == purchases.subscription_id
#     ).where(
#         purchases.user_id == user_id
#     ).orderby(purchases.start_date).get_sql()
#     cursor.execute(sql)
#     purchase_records = cursor.fetchall()
#     if query_result_is_none(purchase_records) is True:
#         connection.close()
#         result = {
#             'result': True,
#             'purchase_data': None
#         }
#         return json.dumps(result, ensure_ascii=False), 200
#     else:
#         result_list = []
#         for data in purchase_records:
#             if data[7] is not None:
#                 deleted_at = data[7].strftime("%Y-%m-%d %H:%M:%S")
#             else:
#                 deleted_at = data[7]
#             each_dict = {"index": data[0],
#                          "payment_information": {
#                              "plan_title": data[2],
#                              "total_price": data[3],  # 정상가
#                              "total_payment": data[4],
#                              "start_date": data[5].strftime("%Y-%m-%d %H:%M:%S"),
#                              "expire_date": data[6].strftime("%Y-%m-%d %H:%M:%S"),
#                              "deleted_at": deleted_at,
#                              "buyer_email": data[8],  # 결제자 이메일
#                              "buyer_name": data[9],  # 결제자 이름
#                              "buyer_phone": data[10],  # 결제자 전화번호
#                              "state": data[11]
#                          }}
#             result_list.append(each_dict)
#         result_dict = {
#             "result": True,
#             "purchase_data": result_list
#         }
#         return json.dumps(result_dict, ensure_ascii=False), 200


@api.route('/purchase/update_notification', methods=['POST'])
def update_payment_state_by_webhook():
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
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.update_payment_state_by_webhook')
    """Define tables required to execute SQL."""
    orders = Table("orders")
    users = Table("users")

    connection = login_to_db()
    cursor = connection.cursor()

    parameters = json.loads(request.get_data(), encoding='utf-8')

    imp_uid = parameters['imp_uid']
    merchant_uid = parameters['merchant_uid']
    updated_state = parameters['status']
    user_id = int(merchant_uid.split('_')[-1])
    # user_id = parameters['merchant_uid']

    # 2. import에서 결제 정보 조회
    get_token = json.loads(get_import_access_token(IMPORT_REST_API_KEY, IMPORT_REST_API_SECRET))
    if get_token['result'] is False:
        connection.close()
        raise HandleException(user_ip=ip,
                              user_id=user_id,
                              api=endpoint,
                              error_message=f'Failed to get import access token at server(message: {get_token["message"]})',
                              # query=sql,
                              method=request.method,
                              status_code=500,
                              payload=None,
                              result=False)
    else:
        access_token = get_token['access_token']

    payment_validation_import = requests.get(
        f"https://api.iamport.kr/payments/{imp_uid}",
        headers={"Authorization": access_token}
    ).json()
    import_paid_amount = int(payment_validation_import['response']['amount'])

    # 3. DB에서 결제 내역 조회
    # query = "SELECT total_payment FROM purchases WHERE imp_uid=%s AND merchant_uid=%s"
    sql = Query.from_(
        orders
    ).select(
        orders.total_price
    ).where(
        Criterion.all([
            orders.imp_uid == imp_uid,
            orders.merchant_uid == merchant_uid
        ])
    ).get_sql()
    cursor.execute(sql)
    db_paid_amount = cursor.fetchall()

    if query_result_is_none(db_paid_amount) is True:
        status = payment_validation_import['response']['status']
        method = payment_validation_import['response']['pg_provider']

        sql = Query.into(
            orders
        ).columns(
            orders.user_id,
            orders.total_price,
            orders.method,
            orders.imp_uid,
            orders.merchant_uid,
            orders.status
        ).insert(
            user_id,
            import_paid_amount,
            method,
            imp_uid,
            merchant_uid,
            status
        ).get_sql()

        try:
            cursor.execute(sql)
            connection.commit()
            connection.close()
            result = {'result': True}
            return json.dumps(result, ensure_ascii=False), 201
        except Exception as e:
            connection.rollback()
            connection.close()
            raise HandleException(user_ip=ip,
                                  user_id=user_id,
                                  api=endpoint,
                                  error_message=f'Failed to get import access token at server(message: {str(e)})',
                                  query=sql,
                                  method=request.method,
                                  status_code=500,
                                  payload=None,
                                  result=False)
    else:
        # 결제 취소 이벤트가 아임포트 어드민(https://admin.iamport.kr/)에서 "취소하기" 버튼을 클릭하여 발생한 경우에만 트리거됨.
        if int(db_paid_amount[0][0]) == int(import_paid_amount):
            if updated_state == 'cancelled':
                sql = Query.update(
                    users
                ).set(
                    orders.subscription_started_at, None
                ).set(
                    orders.subscription_expired_at, None
                ).set(
                    orders.subscription_id, None
                ).set(
                    orders.updated_at, fn.Now()
                ).get_sql()
                cursor.execute(sql)

                sql = Query.update(
                    orders
                ).set(
                    orders.status, updated_state
                ).set(
                    orders.deleted_at, fn.Now()
                ).set(
                    orders.updated_at, fn.Now()
                ).where(
                    Criterion.all([
                        orders.imp_uid == imp_uid,
                        orders.merchant_uid == merchant_uid
                    ])
                ).get_sql()
                cursor.execute(sql)
                connection.commit()
                connection.close()
                result = {'result': True}
                return json.dumps(result, ensure_ascii=False), 201
            """2. 결제 완료 후 사용자 요청에 의해 아임포트에 의해 취소되는 경우 => 어떤 조건들을 추가하고 어떤 데이터들을 변경할까???"""
        else:
            connection.close()
            result = {
                'result': False,
                'error': f': Error while validating payment information: Paid amount that was sent from IMPORT is {import_paid_amount} WON(imp_uid: {imp_uid}), but found {db_paid_amount} WON in orders table.'
            }
            slack_error_notification(user_ip=ip, api=endpoint, error_message=result['error'], method=request.method)
            return json.dumps(result, ensure_ascii=False), 400


@api.route('/purchase', methods=['POST'])
def add_subscription_order():
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.add_subscription_order')
    # user_token = request.headers.get('Authorization')
    """Define tables required to execute SQL."""
    orders = Table('orders')
    subscriptions = Table('subscriptions')
    discounts = Table('discounts')
    users = Table('users')
    order_subscriptions = Table('order_subscriptions')

    parameters = json.loads(request.get_data(), encoding='utf-8')
    try:
        subscription_code = parameters['subscription_code']
        discount_code = parameters['discount_code']
        period = int(parameters['subscription_period'])  # Month!!!!!
        payment_info = parameters['payment_info']  # Value format: yyyy-Www(Week 01, 2017 ==> "2017-W01")

        # 결제 정보 변수
        imp_uid = payment_info['imp_uid']
        merchant_uid = payment_info['merchant_uid']
        user_id = int(merchant_uid.split('_')[-1])
        # user_id = int(parameters['user_id'])
    except Exception as e:
        result = {
            'result': False,
            'message': f'Missing data: {str(e)}'
        }
        return json.dumps(result, ensure_ascii=False), 400

    if not(user_id and period and imp_uid and merchant_uid):
        result = {
            'result': False,
            'message': 'Null is not allowed.'
        }
        return json.dumps(result, ensure_ascii=False), 400

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

    # 1. 유저 정보 확인
    connection = login_to_db()
    cursor = connection.cursor()

    # Verify user is valid or not.
    # verify_user = check_user_token(cursor, user_token)
    # if verify_user['result'] is False:
    #     connection.close()
    #     result = {
    #         'result': False,
    #         'error': 'Unauthorized user.'
    #     }
    #     return json.dumps(result), 401
    # user_id = verify_user['user_id']
    # user_nickname = verify_user['user_nickname']

    # 2. 결제 정보 조회(import)
    get_token = json.loads(get_import_access_token(IMPORT_REST_API_KEY, IMPORT_REST_API_SECRET))
    if get_token['result'] is False:
        connection.close()
        raise HandleException(user_ip=ip,
                              # nickname=user_nickname,
                              user_id=user_id,
                              api=endpoint,
                              error_message=f'Failed to get import access token at server(message: {get_token["message"]})',
                              # query=sql,
                              method=request.method,
                              status_code=500,
                              payload=parameters,
                              result=False)
    else:
        access_token = get_token['access_token']

    payment_validation_import = requests.get(
        f"https://api.iamport.kr/payments/{payment_info['imp_uid']}",
        headers={"Authorization": access_token}
    ).json()
    payment_state = payment_validation_import['response']['status']
    import_paid_amount = int(payment_validation_import['response']['amount'])
    user_subscription = payment_validation_import['response']['name']

    # 3. 결제 정보 검증(DB ~ import 결제액)
    """
    보완사항
    (1) 결제 검증 수단 추가: subscription price, sales price, discount_id VS import 결제 정보
    (2) (1) 바탕으로 결제 검증 로직
    """
    sql = Query.from_(
        subscriptions
    ).select(
        subscriptions.id,
        subscriptions.title,
        subscriptions.original_price,
        subscriptions.price,
        subscriptions.period_days,
    ).where(
        subscriptions.code == subscription_code
    ).get_sql()
    cursor.execute(sql)

    subscription_information = cursor.fetchall()
    if query_result_is_none(subscription_information) is True:
        try:
            sql = Query.update(
                orders
            ).set(
                orders.user_id, user_id
            ).set(
                orders.status, "cancelled"
            ).set(
                orders.deleted_at, fn.Now()
            ).where(
                Criterion.all([
                    orders.imp_uid == imp_uid,
                    orders.merchant_uid == merchant_uid
                ])
            ).get_sql()
            cursor.execute(sql)
            connection.commit()
            connection.close()

            refund_reason = "[결제검증 실패]: 결제 요청된 플랜명과 일치하는 플랜명이 없습니다."
            refund_result = request_import_refund(access_token, imp_uid, merchant_uid, import_paid_amount, import_paid_amount, refund_reason)
            if refund_result['code'] == 0:
                result = {'result': False,
                          'error': f"결제 검증 실패(주문 플랜명 불일치), 환불처리 성공(imp_uid: {imp_uid}, merchant_uid: {merchant_uid})."}
                slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], method=request.method)
                return json.dumps(result, ensure_ascii=False), 400
            else:
                result = {'result': False,
                          'error': f"결제 검증 실패(주문 플랜명 불일치), 다음 사유로 인해 환불처리 실패하여 아임포트 어드민에서 직접 취소 요망(imp_uid: {imp_uid}, merchant_uid: {merchant_uid}) : {refund_result['message']}"}
                slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], method=request.method)
                return json.dumps(result, ensure_ascii=False), 400
        except Exception as e:
            raise HandleException(user_ip=ip,
                                  # nickname=user_nickname,
                                  user_id=user_id,
                                  api=endpoint,
                                  error_message=f'Server error while validating subscription purchase: {str(e)}',
                                  query=sql,
                                  method=request.method,
                                  status_code=500,
                                  payload=parameters,
                                  result=False)
    else:
        pass
    if discount_code is None:
        to_be_paid = subscription_information[0][3]
        subscription_original_price = subscription_information[0][2]
        discount_id = None
    else:
        sql = Query.from_(
            discounts
        ).select(
            discounts.id,
            discounts.type,
            discounts.method,
            discounts.value,
            discounts.code
        ).where(
            discounts.code == discount_code
        ).get_sql()
        cursor.execute(sql)
        discount_information = cursor.fetchall()
        to_be_paid, subscription_original_price, discount_id = validation_subscription_order(subscription_information, discount_information)

    if to_be_paid != import_paid_amount:
        """
        1. '부분환불' 도입 시
            - DB에 canceled_amount 추가하기.
            - 환불 요청의 checksum, amount 파라미터의 값이 변경되어야 함.
        2. 케이스별 환불사유 준비하기
        """
        refund_reason = f"[결제검증 실패]: 판매가와 결제금액이 불일치합니다(판매 금액: {to_be_paid} | 실제 결제 금액: {import_paid_amount})."
        refund_result = request_import_refund(access_token, imp_uid, merchant_uid, import_paid_amount, import_paid_amount, refund_reason)
        if refund_result['code'] == 0:
            try:
                sql = Query.update(
                    orders
                ).set(
                    orders.user_id, user_id
                ).set(
                    orders.status, "cancelled"
                ).set(
                    orders.deleted_at, fn.Now()
                ).where(
                    Criterion.all([
                        orders.imp_uid == imp_uid,
                        orders.merchant_uid == merchant_uid
                    ])
                ).get_sql()
                cursor.execute(sql)
                connection.commit()
            except Exception as e:
                connection.rollback()
                connection.close()
                raise HandleException(user_ip=ip,
                                      # nickname=user_nickname,
                                      user_id=user_id,
                                      api=endpoint,
                                      error_message=f'Server error while validating subscription purchase: {str(e)}',
                                      query=sql,
                                      method=request.method,
                                      status_code=500,
                                      payload=parameters,
                                      result=False)
            connection.close()
            result = {'result': False,
                      'error': f"결제 검증 실패(결제 금액 불일치), 환불처리 성공(imp_uid: {imp_uid}, merchant_uid: {merchant_uid})."}
            slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], method=request.method)
            return json.dumps(result, ensure_ascii=False), 400
        else:
            # IMPORT 서버의 오류로 인해 환불 요청이 실패할 경우 직접 환불한다.
            connection.close()
            result = {'result': False,
                      'error': f"결제 검증 실패(결제 금액 불일치), 다음 사유로 인해 환불처리 실패하였으니 아임포트 어드민에서 직접 취소 요망(imp_uid: {imp_uid}, merchant_uid: {merchant_uid}) : {refund_result['message']}"}
            slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], method=request.method)
            return json.dumps(result, ensure_ascii=False), 400

    # 4. 결제 정보(orders) 저장
    subscription_id = subscription_information[0][0]
    try:
        if discount_id is None:
            sql = Query.update(
                orders
            ).join(
                users
            ).on(
                orders.user_id == users.id
            ).set(
                orders.user_id, user_id
            ).set(
                users.subscription_expired_at, fn.Now() + Interval(days=subscription_days)
            ).set(
                users.subscription_id, subscription_id
            ).where(
                Criterion.all([
                    orders.user_id == user_id,
                    orders.imp_uid == imp_uid,
                    orders.merchant_uid == merchant_uid
                ])
            ).get_sql()
        else:
            sql = Query.update(
                orders
            ).join(
                users
            ).on(
                orders.user_id == users.id
            ).set(
                orders.user_id, user_id
            ).set(
                orders.discount_id, discount_id
            ).set(
                users.subscription_expired_at, fn.Now() + Interval(days=subscription_days)
            ).set(
                users.subscription_id, subscription_id
            ).where(
                Criterion.all([
                    orders.user_id == user_id,
                    orders.imp_uid == imp_uid,
                    orders.merchant_uid == merchant_uid
                ])
            ).get_sql()
        cursor.execute(sql)
        connection.commit()

        sql = Query.from_(
            orders
        ).select(
            orders.id
        ).where(
            Criterion.all([
                orders.imp_uid == imp_uid,
                orders.merchant_uid == merchant_uid
            ])
        ).get_sql()
        cursor.execute(sql)
        result = cursor.fetchall()
        if len(result) == 0:
            order_id = None
        else:
            order_id = result[0][0]

        sql = Query.into(
            order_subscriptions
        ).columns(
            order_subscriptions.order_id,
            order_subscriptions.subscription_id,
            order_subscriptions.price,
            order_subscriptions.discount_price
        ).insert(
            order_id,
            subscription_id,
            import_paid_amount,
            subscription_original_price - import_paid_amount
        ).get_sql()
        cursor.execute(sql)
        connection.commit()

        sql = Query.from_(
            users
        ).select(
            users.nickname,
            users.phone,
        ).where(
            users.id == user_id
        ).get_sql()
        cursor.execute(sql)
        user_information = cursor.fetchall()
        user_nickname, user_phone = user_information[0]

        slack_purchase_notification(cursor, user_id, user_nickname, user_phone, order_id)
        connection.close()
        result = {'result': True,
                  'message': 'Saved subscription payment data.',
                  'order_id': order_id}
        return json.dumps(result, ensure_ascii=False), 201
    except Exception as e:
        error = str(e)
        result = {'result': False,
                  'error': error}
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], query=sql, method=request.method)
        return json.dumps(result, ensure_ascii=False), 400
