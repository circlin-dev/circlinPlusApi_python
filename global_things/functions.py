from global_things.constants import IMAGE_ANALYSYS_SERVER, SLACK_NOTIFICATION_WEBHOOK
from config.database import DB_CONFIG
import json
import requests
import pymysql

# region Connection to database.
def login_to_db():
  conn = pymysql.connect(
    user=DB_CONFIG['user'],
    passwd=DB_CONFIG['password'],
    host=DB_CONFIG['host'],
    db=DB_CONFIG['database'],
    charset=DB_CONFIG['charset'])

  return conn
# endregion

# region Slack error notification
def slack_error_notification(user_ip: str='', user_id: str='', nickname: str='', api: str='', error_log: str='', query: str=''):
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
    }
  ), ensure_ascii=False)

  return send_notification_request
# endregion

# region Bodylab functions
def standard_healthiness_score(type: str, age: int, sex: str, weight: float, height=0) -> float:
  if type == None or age == None or sex == None or weight == None:
    return 'Some parameter has None value.'

  if type == 'fat_mass':
    if sex == 'W':
      if age < 18: percent = 19.7
      elif age < 21: percent = (19.7 + 21.5) / 2
      elif age < 26: percent = 22.1
      elif age < 31: percent = 22.7
      elif age < 36: percent = (23.4 + 25.1) / 2
      elif age < 41: percent = (24.0 + 25.7) / 2
      elif age < 46: percent = (24.6 + 26.3) / 2
      elif age < 51: percent = 26.9
      elif age < 56: percent = 27.6
      else: percent = (28.2 + 29.8) / 2
    elif sex == 'M':
      if age < 18: percent = 9.4
      elif age < 21: percent = 10.5
      elif age < 26: percent = 11.6
      elif age < 31: percent = (12.7 + 14.6) / 2
      elif age < 36: percent = (13.7 + 15.7) / 2
      elif age < 41: percent = 16.8
      elif age < 46: percent = 17.8
      elif age < 51: percent = (18.9 + 20.7) / 2
      elif age < 56: percent = (20.0 + 21.8) / 2
      else: percent = 22.8
    else:
      return 'Out of category: sex'
    ideal_fat_mass = (weight * percent) / 100
    return ideal_fat_mass #float

  elif type == 'muscle_mass':
    if sex == 'W':
      ideal_muscle_mass = weight * 0.34
    elif sex == 'M':
      ideal_muscle_mass = weight * 0.4
    else:
      return 'Out of category: sex'
    return ideal_muscle_mass #float

  elif type == 'bmi_index':
    if height != 0 and type(height) == float:
      height_float = round(height / 100, 3) #Scale of height in BMI index is 'meter'.
      my_bmi = weight / (height_float ** 2)
    else:
      return 'Out of category: height'
    return my_bmi #float

  else:
    return 'Out of category: score type'
# endregion

def analyze_image(user_id: int, url: str):
  response = requests.post(
    f"http://{IMAGE_ANALYSYS_SERVER}/",
    json.dumps({
      "user_id": user_id,
      "url": url
    }, ensure_ascii=False)
  )

  if response.status_code == 200:
    return json.dumps({'response': json.loads(response), 'status_code':200}, ensure_ascii=False)
  elif response.status_code == 400:
    slack_error_notification(api='/api/bodylab/add', error_log=json.loads(response['message']))
    return json.dumps({'error': json.loads(response['message']), 'status_code': 400}, ensure_ascii=False)
  elif response.status_code == 500:
    slack_error_notification(api='/api/bodylab/add', error_log=json.loads(response['message']))
    return json.dumps({'error': json.loads(response['message']), 'status_code': 500}, ensure_ascii=False)


