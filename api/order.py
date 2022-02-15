from global_things.constants import API_ROOT, API_NODEJS_SERVER
from global_things.functions.slack import slack_error_notification, slack_purchase_notification
from global_things.functions.general import login_to_db, check_session, query_result_is_none
from global_things.functions.order import amount_to_be_paid, get_import_access_token, request_import_refund
from global_things.constants import IMPORT_REST_API_KEY, IMPORT_REST_API_SECRET
from . import api
from flask import url_for, request
import json
import requests
from pypika import MySQLQuery as Query, Criterion, Table, JoinType, Order, functions as fn


@api.route('/assign-manager', methods=['POST'])
def create_chat_with_manager():
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.create_chat_with_manager')
    # token = request.headers['Authorization']
    parameters = json.loads(request.get_data(), encoding='utf-8')
    """Define tables required to execute SQL."""
    user_questions = Table('user_questions')
    customers = Table('chat_users')
    managers = Table('chat_users')
    chat_rooms = Table('chat_rooms')
    chat_users = Table('chat_users')
    user_id = int(parameters['user_id'])
    order_id = parameters['order_id']  # null or int

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
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
        return json.dumps(result, ensure_ascii=False), 403

    gender = json.loads(answer_data[0][0].replace("\\", "\\\\"), strict=False)['gender']

    if gender == 'M':
        manager_id = 28  # 28 = 대표님, 18 = 희정님
    else:
        manager_id = 18

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
            error = str(e)
            result = {
                'result': False,
                'error': f'Server Error while executing INSERT query(chat_rooms): {error}'
            }
            slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=sql)
            return json.dumps(result, ensure_ascii=False), 500

        try:
            sql = Query.into(
                chat_users
            ).columns(
                chat_users.created_at,
                chat_users.updated_at,
                chat_users.chat_room_id,
                chat_users.user_id
            ).insert(
                (fn.Now(), fn.Now(), chat_room_id, manager_id),
                (fn.Now(), fn.Now(), chat_room_id, user_id)
            ).get_sql()
            cursor.execute(sql)
            connection.commit()
        except Exception as e:
            connection.rollback()
            connection.close()
            error = str(e)
            result = {
                'result': False,
                'error': f'Server Error while executing INSERT query(chat_users): {error}'
            }
            slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=sql)
            return json.dumps(result, ensure_ascii=False), 500
    else:
        connection.close()
        result = {
            'result': True,
            'manager_id': manager_id,  # 28 = 대표님, 18 = 희정님
            'message': 'Chatroom already exists.'
        }
        return json.dumps(result, ensure_ascii=False), 200

    if order_id is not None:
        slack_purchase_notification(cursor, user_id, manager_id, order_id)
    connection.close()
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
#         slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
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
#     #   slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
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
    # ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.update_payment_state_by_webhook')
    """Define tables required to execute SQL."""
    orders = Table("orders")

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
    updated_state = parameters['status']
    user_id = int(merchant_uid.split('_')[-1])

    # 2. import에서 결제 정보 조회
    get_token = json.loads(get_import_access_token(IMPORT_REST_API_KEY, IMPORT_REST_API_SECRET))
    if get_token['result'] is False:
        connection.close()
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
            error = str(e)
            result = {
                'result': False,
                'error': f'Server error while validating : {error}'
            }
            slack_error_notification(user_ip=ip, api=endpoint, error_log=result['error'], query=sql)
            return json.dumps(result, ensure_ascii=False), 500
    else:
        # 결제 취소 이벤트가 아임포트 어드민(https://admin.iamport.kr/)에서 "취소하기" 버튼을 클릭하여 발생한 경우에만 트리거됨.
        if int(db_paid_amount[0][0]) == int(import_paid_amount):
            """1. 결제 검증 실패에 의해 취소되는 경우: 어떤 조건들을 추가해 줄까???"""
            if updated_state == 'cancelled':
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
            slack_error_notification(user_ip=ip, api=endpoint, error_log=result['error'])
            return json.dumps(result, ensure_ascii=False), 403


@api.route('/purchase', methods=['POST'])
def add_subscription_order():
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.add_subscription_order')
    # token = request.headers['Authorization']
    """Define tables required to execute SQL."""
    orders = Table('orders')
    order_products = Table('order_products')
    order_product_deliveries = Table('order_product_delivery')
    order_subscriptions = Table('order_subscriptions')
    subscriptions = Table('subscriptions')
    discounts = Table('discounts')

    parameters = json.loads(request.get_data(), encoding='utf-8')
    user_id = parameters['user_id']
    subscription_code = parameters['subscription_code']
    discount_code = parameters['discount_code']
    period = int(parameters['subscription_period'])  # Month!!!!!
    payment_info = parameters['payment_info']  # Value format: yyyy-Www(Week 01, 2017 ==> "2017-W01")

    # 결제 정보 변수
    imp_uid = payment_info['imp_uid']
    merchant_uid = payment_info['merchant_uid']

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

    if not(user_id and period and imp_uid and merchant_uid):
        result = {
            'result': False,
            'error': f'Missing data in request: user_id: ({user_id}), subscription_period: ({period}), imp_uid:({imp_uid}, merchant_uid: {merchant_uid})'
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
    # is_valid_user = check_token(cursor, user_id, token)
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
                slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
                return json.dumps(result, ensure_ascii=False), 400
            else:
                result = {'result': False,
                          'error': f"결제 검증 실패(주문 플랜명 불일치), 다음 사유로 인해 환불처리 실패하여 아임포트 어드민에서 직접 취소 요망(imp_uid: {imp_uid}, merchant_uid: {merchant_uid}) : {refund_result['message']}"}
                slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
                return json.dumps(result, ensure_ascii=False), 400
        except Exception as e:
            connection.rollback()
            connection.close()
            error = str(e)
            result = {
                'result': False,
                'error': f'Server error while validating : {error}'
            }
            slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=sql)
            return json.dumps(result, ensure_ascii=False), 500
    else:
        pass

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

    to_be_paid, subscription_original_price, discount_id = amount_to_be_paid(subscription_information, discount_information)
    if to_be_paid != import_paid_amount:
        """
        1. '부분환불' 도입 시
            - DB에 canceled_amount 추가하기.
            - 환불 요청의 checksum, amount 파라미터의 값이 변경되어야 함.
        2. 케이스별 환불사유 준비하기
        """
        refund_reason = "[결제검증 실패]: 판매가와 결제금액이 불일치합니다."
        refund_result = request_import_refund(access_token, imp_uid, merchant_uid, import_paid_amount, user_subscription, refund_reason)
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
                error = str(e)
                result = {
                    'result': False,
                    'error': f'Server error while validating : {error}'
                }
                slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=sql)
                return json.dumps(result, ensure_ascii=False), 500
            connection.close()
            result = {'result': False,
                      'error': f"결제 검증 실패(결제 금액 불일치), 환불처리 성공(imp_uid: {imp_uid}, merchant_uid: {merchant_uid})."}
            slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
            return json.dumps(result, ensure_ascii=False), 400
        else:
            # IMPORT 서버의 오류로 인해 환불 요청이 실패할 경우 직접 환불한다.
            connection.close()
            result = {'result': False,
                      'error': f"결제 검증 실패(결제 금액 불일치), 다음 사유로 인해 환불처리 실패하였으니 아임포트 어드민에서 직접 취소 요망(imp_uid: {imp_uid}, merchant_uid: {merchant_uid}) : {refund_result['message']}"}
            slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
            return json.dumps(result, ensure_ascii=False), 400

    # 4. 결제 정보(-> purchases) 저장
    subscription_id = subscription_information[0][0]
    try:
        sql = f"""
            UPDATE
                orders o
            JOIN
                users u
            ON o.user_id = u.id
            SET
                o.user_id = {user_id},
                o.discount_id = {discount_id},
                u.subscription_expired_at = (SELECT(NOW() + INTERVAL {subscription_days} DAY)),
                u.subscription_id = {subscription_id}
            WHERE
                  o.user_id = {user_id}
            AND o.imp_uid = %s
            AND o.merchant_uid = %s"""
        values = (imp_uid, merchant_uid)
        cursor.execute(sql, values)
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
        order_id = int(cursor.fetchall()[0][0])

        sql = f"""
            INSERT INTO 
                    order_subscriptions(order_id, subscription_id, price, discount_price)
                VALUES({order_id}, {subscription_id}, {import_paid_amount}, {subscription_original_price - import_paid_amount})"""
        cursor.execute(sql)
        connection.commit()
        connection.close()
        result = {'result': True,
                  'message': 'Saved subscription payment data.',
                  'order_id': order_id}
        return json.dumps(result, ensure_ascii=False), 201
    except Exception as e:
        connection.close()
        error = str(e)
        result = {'result': False,
                  'error': error}
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=sql)
        return json.dumps(result, ensure_ascii=False), 400
