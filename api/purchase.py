from global_things.functions import slack_error_notification, login_to_db
from global_things.constants import ATTRACTIVENESS_SCORE_CRITERIA
from . import api
from flask import request
import json

@api.route('/purchase/record', methods=['POST'])
def read_purchase_record():
  ip = request.remote_addr
  endpoint = '/api/purchase/record'
  user_id = request.form.get('user_id')

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
  query = f"\
    SELECT \
          id, success \
      from \
          purchases \
      WHERE \
          user_id={user_id} \
      ORDER BY id"

  cursor.execute(query)
  purchase_record = cursor.fetchall()
  if len(purchase_record) == 0 or purchase_record == ():
    result = {
      'result': True,
      'num_purchase_record': 0
    }
    return json.dumps(result, ensure_ascii=False), 201
  elif len(purchase_record) > 0 and purchase_record[0][1] != 'success':
    result = {
      'result': True,
      'num_purchase_record': 0
    }
    return json.dumps(result, ensure_ascii=False), 201



# @api.route('/purchase/add', methods=['POST'])
# def add_purchase():
#   ip = request.remote_addr
#   endpoint = '/api/purchase/add'
#
#   period = request.form.get('period')  # Value format: yyyy-Www(Week 01, 2017 ==> "2017-W01")
#   user_id = request.form.get('user_id')
#   subscribe_period = request.form.get('subscribe_period') # int  # for plan_id 'purchases'
#   rent_equipment = request.form.get('rent_equipment') # boolean  # for plan_id at table 'purchases'
#
#   try:
#     connection = login_to_db()
#   except Exception as e:
#     error = str(e)
#     result = {
#       'result': False,
#       'error': f'Server Error while connecting to DB: {error}'
#     }
#     slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
#     return json.dumps(result, ensure_ascii=False), 500
#
#   cursor = connection.cursor()
#
#   if subscribe_period == 1:
#     if rent_equipment is True: plan_id = 0
#       # start_date
#       # expire_date
#       # discount_id
#
#   # 결제 정보
#   apply_num = request.form.get('apply_num')
#   bank_name = request.form.get('bank_name')
#   buyer_addr = request.form.get('buyer_addr')
#   buyer_email = request.form.get('buyer_email')
#   buyer_name = request.form.get('buyer_name')
#   buyer_postcode = request.form.get('buyer_postcode')
#   buyer_tel = request.form.get('buyer_tel')
#   card_name = request.form.get('card_name')
#   card_number = request.form.get('card_number')
#   card_quota = request.form.get('card_quota')
#   currency = request.form.get('currency')
#   custom_data = request.form.get('custom_data')
#   imp_uid = request.form.get('imp_uid')
#   merchant_id = request.form.get('merchant_id')
#   name = request.form.get('name')
#   paid_amount = request.form.get('paid_amount')
#   paid_at = request.form.get('paid_at')
#   pay_method = request.form.get('pay_method')
#   pg_provider = request.form.get('pg_provider')
#   pg_tid = request.form.get('pg_tid')
#   pg_type = request.form.get('pg_tid')
#   receipt_url = request.form.get('receipt_url')
#   status = request.form.get('status')
#   success = request.form.get('success')
#
#   # 배송정보
#   recipient_name = request.form.get('recipient_name')  # 결제자 이름
#   post_code  = request.form.get('post_code') # 스타터키트 배송지 주소(우편번호)
#   address = request.form.get('address') # 스타터키트 배송지 주소(주소)
#   aaddress_detail = request.form.get('aaddress_detail') # 스타터키트 배송지 주소(상세주소)
#   phone = request.form.get('phone') # 결제자 휴대폰 번호
#
#
#   if request.method == 'POST':
#     if not(user_id, )