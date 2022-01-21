from global_things.constants import SLACK_NOTIFICATION_WEBHOOK
import json
import requests


# Slack notification: error
def slack_error_notification(user_ip: str = '', user_id: str = '', nickname: str = '', api: str = '',
                             error_log: str = '', query: str = ''):
  if user_ip == '' or user_id == '':
    user_ip = "Server error"
    user_id = "Server error"

  send_notification_request = requests.post(
    SLACK_NOTIFICATION_WEBHOOK,
    json.dumps({
      "channel": "#circlin-members-log",
      "username": "써클인 멤버스 - python",
      "text": f"*써클인 멤버스(python)에서 오류가 발생했습니다.* \n \
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
  query = f"""
    SELECT
          p.start_date,
          p.expire_date,
          sp.title AS plan_title,
          u.nickname,
          (SELECT nickname FROM users WHERE id={manager_id}) AS manager_name
    FROM
        purchases p,
        subscribe_plans sp,
        users u   
  WHERE
        p.id = {purchase_id} 
    AND sp.id = p.plan_id 
    AND u.id = p.user_id"""

  cursor.execute(query)
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
    }, ensure_ascii=False).encode('utf-8')
  )

  return send_notification_request
