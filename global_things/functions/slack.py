from global_things.constants import API_ROOT, SLACK_NOTIFICATION_WEBHOOK
import json
from pypika import MySQLQuery as Query, Table
import requests


# Slack notification: error
def slack_error_notification(user_ip: str = '', nickname: str = '', user_id: int = 0, api: str = '', method: str = '',
                             status_code: int = 0, query: str = '', error_message: str = ''):
  if user_ip == '' or user_id == '':
    user_ip = "Server error"
    user_id = 0

  send_notification_request = requests.post(
    SLACK_NOTIFICATION_WEBHOOK,
    json.dumps({
      "channel": "#circlin-plus-log",
      "username": "써클인 플러스 - python",
      "method": method,
      "text": f"*써클인 플러스(python)에서 오류가 발생했습니다.* \n \
사용자 IP: `{user_ip}` \n \
사용자 ID 번호: `{nickname}({user_id})`\n \
API URL: `{api}` \n \
HTTP method: `{method}` \n \
Status code: `{status_code}` \n \
```query: {query}``` \n \
```error: {error_message}```",
      "icon_url": "https://www.circlin.co.kr/new/assets/favicon/apple-icon-180x180.png"
    }, ensure_ascii=False).encode('utf-8')
  )

  return send_notification_request


# Slack notification: purchase
def slack_purchase_notification(cursor, user_id: int = 0, user_nickname: str = '', user_phone: str = '', order_id: int = 0):
  # manager_id: int = 0,
  subscriptions = Table('subscriptions')
  orders = Table('orders')
  order_subscriptions = Table('order_subscriptions')
  users = Table('users')

  # subquery_manager_name = Query.from_(
  #   users
  # ).select(
  #   users.nickname
  # ).where(
  #   users.id == manager_id
  # )
  # sql = Query.from_(
  #   orders
  # ).select(
  #   orders.created_at,
  #   users.subscription_expired_at,
  #   subscriptions.title,
  #   users.nickname,
  #   subquery_manager_name
  # ).join(
  #   users
  # ).on(
  #   orders.user_id == users.id
  # ).join(
  #   order_subscriptions
  # ).on(
  #   order_subscriptions.order_id == orders.id
  # ).join(
  #   subscriptions
  # ).on(
  #   order_subscriptions.subscription_id == subscriptions.id
  # ).where(
  #   orders.id == order_id
  # ).get_sql()
  sql = Query.from_(
    orders
  ).select(
    orders.created_at,
    users.subscription_expired_at,
    subscriptions.title
  ).join(
    users
  ).on(
    users.id == user_id
  ).join(
    order_subscriptions
  ).on(
    order_subscriptions.order_id == orders.id
  ).join(
    subscriptions
  ).on(
    order_subscriptions.subscription_id == subscriptions.id
  ).where(
    orders.id == order_id
  ).get_sql()

  cursor.execute(sql)
  start_date, expire_date, subscription_title = cursor.fetchall()[0]

  send_notification_request = requests.post(
    SLACK_NOTIFICATION_WEBHOOK,
    json.dumps({
      "channel": "#circlin-plus-order-log",
      "username": f"결제 완료 알림: {user_nickname}({user_id})",
      "text": f":dollar::dollar: {user_nickname} 고객님께서 *{subscription_title}* 플랜을 결제하셨습니다! :dollar::dollar: \n\n \
고객 연락처: `{user_phone}` \n \
결제 id: `{order_id}` \n \
시작일: `{start_date.strftime('%Y-%m-%d %H:%M:%S')}` \n \
만료일: `{expire_date.strftime('%Y-%m-%d %H:%M:%S')}`\n ",
      # 담당 매니저: `{manager_name}({manager_id})`
      "icon_url": "https://www.circlin.co.kr/new/assets/favicon/apple-icon-180x180.png"
    }, ensure_ascii=False).encode('utf-8'))

  return send_notification_request
