from global_things.constants import SLACK_NOTIFICATION_WEBHOOK
import json
from pypika import MySQLQuery as Query, Table
import requests


# Slack notification: error
def slack_error_notification(user_ip: str = '', user_id: int = 0, nickname: str = '', api: str = '',
                             error_log: str = '', query: str = ''):
  if user_ip == '' or user_id == '':
    user_ip = "Server error"
    user_id = "Server error"

  send_notification_request = requests.post(
    SLACK_NOTIFICATION_WEBHOOK,
    json.dumps({
      "channel": "#circlin-plus-log",
      "username": "써클인 플러스 - python",
      "text": f"*써클인 플러스(python)에서 오류가 발생했습니다.* \n \
사용자 IP: `{user_ip}` \n \
닉네임 (ID): `{nickname}({user_id})`\n \
API URL: `{api}` \n \
```{error_log} \n \
{query}```",
      "icon_url": "https://www.circlin.co.kr/new/assets/favicon/apple-icon-180x180.png"
    }, ensure_ascii=False).encode('utf-8')
  )

  return send_notification_request


# Slack notification: purchase
def slack_purchase_notification(cursor, user_id: int = 0, manager_id: int = 0, purchase_id: int = 0):
  purchases = Table('purchases')
  subscribe_plans = Table('subscribe_plans')
  users = Table('users')

  subquery_manager_name = Query.from_(
    users
  ).select(
    users.nickname
  ).where(
    users.id == manager_id
  )
  sql = Query.from_(
    purchases
  ).select(
    purchases.start_date,
    purchases.expire_date,
    subscribe_plans.title,
    users.nickname,
    subquery_manager_name
  ).join(
    subscribe_plans
  ).on(
    subscribe_plans.id == purchases.subscription_id
  ).join(
    users
  ).on(
    users.id == purchases.user_id
  ).where(
    purchases.id == purchase_id
  )

  cursor.execute(sql.get_sql())
  start_date, expire_date, plan_title, nickname, manager_name = cursor.fetchall()[0]

  send_notification_request = requests.post(
    SLACK_NOTIFICATION_WEBHOOK,
    json.dumps({
      "channel": "#circlin-plus-order-log",
      "username": f"결제 완료 알림: {nickname}({user_id})",
      "text": f":dollar::dollar: {nickname} 고객님께서 *{plan_title}* 플랜을 결제하셨습니다! :dollar::dollar: \n\n \
결제 id: `{purchase_id}` \n \
시작일: `{start_date.strftime('%Y-%m-%d %H:%M:%S')}` \n \
만료일: `{expire_date.strftime('%Y-%m-%d %H:%M:%S')}`\n \
담당 매니저: `{manager_name}({manager_id})`",
      "icon_url": "https://www.circlin.co.kr/new/assets/favicon/apple-icon-180x180.png"
    }, ensure_ascii=False).encode('utf-8'))

  return send_notification_request
