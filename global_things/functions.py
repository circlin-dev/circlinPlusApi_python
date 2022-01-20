from global_things.constants import IMAGE_ANALYSYS_SERVER, SLACK_NOTIFICATION_WEBHOOK
from config.database import DB_CONFIG
import datetime
import json
import requests
import pymysql


# region General
# Connection to database.
def login_to_db():
  conn = pymysql.connect(
    user=DB_CONFIG['user'],
    passwd=DB_CONFIG['password'],
    host=DB_CONFIG['host'],
    db=DB_CONFIG['database'],
    charset=DB_CONFIG['charset'])

  return conn


# User verification by exploring user table.
def check_user(cursor, user_id):
  query = f"SELECT * FROM users WHERE id={user_id}"
  cursor.execute(query)
  user_id_tuple = cursor.fetchall()
  if len(user_id_tuple) == 0 or user_id_tuple == ():
    result = {'result': False}
    return result
  else:
    result = {'result': True}
    return result


# Check how many rows are in the result of query execution
def query_result_is_none(execution: tuple):
  if len(execution) == 0 or execution == ():
    return True
  else:
    return False


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
# endregion


# region bodylab.py
def standard_healthiness_score(score_type: str, age: int, sex: str, weight: float, height=0):
  if score_type is None or age is None or sex is None or weight is None:
    return 'Some parameter has None value.'

  if score_type == 'fat_mass':
    if sex == 'W':
      if age < 18:
        percent = 19.7
      elif age < 21:
        percent = (19.7 + 21.5) / 2
      elif age < 26:
        percent = 22.1
      elif age < 31:
        percent = 22.7
      elif age < 36:
        percent = (23.4 + 25.1) / 2
      elif age < 41:
        percent = (24.0 + 25.7) / 2
      elif age < 46:
        percent = (24.6 + 26.3) / 2
      elif age < 51:
        percent = 26.9
      elif age < 56:
        percent = 27.6
      else:
        percent = (28.2 + 29.8) / 2
    elif sex == 'M':
      if age < 18:
        percent = 9.4
      elif age < 21:
        percent = 10.5
      elif age < 26:
        percent = 11.6
      elif age < 31:
        percent = (12.7 + 14.6) / 2
      elif age < 36:
        percent = (13.7 + 15.7) / 2
      elif age < 41:
        percent = 16.8
      elif age < 46:
        percent = 17.8
      elif age < 51:
        percent = (18.9 + 20.7) / 2
      elif age < 56:
        percent = (20.0 + 21.8) / 2
      else:
        percent = 22.8
    else:
      return 'Out of category: sex'
    ideal_fat_mass = (weight * percent) / 100
    return ideal_fat_mass  # float

  elif score_type == 'muscle_mass':
    if sex == 'W':
      ideal_muscle_mass = weight * 0.34
    elif sex == 'M':
      ideal_muscle_mass = weight * 0.4
    else:
      return 'Out of category: sex'
    return ideal_muscle_mass  # float

  elif score_type == 'bmi_index':
    if height != 0 and type(height) == float:
      height_float = round(height / 100, 3)  # Scale of height in BMI index is 'meter'.
      my_bmi = weight / (height_float ** 2)
    else:
      return 'Out of category: height'
    return my_bmi  # float

  else:
    return 'Out of category: score type'


def analyze_image(user_id, url):
  response = requests.post(
    f"http://{IMAGE_ANALYSYS_SERVER}/analysis",
    json={
      "user_id": user_id,
      "url": url
    })

  if response.status_code == 200:
    return json.dumps({'result': response.json(), 'status_code': 200}, ensure_ascii=False)
  elif response.status_code == 400:
    slack_error_notification(api='/api/bodylab/add', error_log=response.json()['message'])
    return json.dumps({'error': response.json()['message'], 'status_code': 400}, ensure_ascii=False)
  elif response.status_code == 500:
    slack_error_notification(api='/api/bodylab/add', error_log=response.json()['message'])
    return json.dumps({'error': response.json()['message'], 'status_code': 500}, ensure_ascii=False)


def get_date_range_from_week(year: str, week_number: str):
  """
  Reference: http://mvsourcecode.com/python-how-to-get-date-range-from-week-number-mvsourcecode/

  getDateRangeFromWeek(2022, 2) ==> input<'week'> 기준 (2022, 1) (1.3 ~ 1.9)
  getDateRangeFromWeek(2022, 53) ==> input<'week'> 기준 (2022, 52) (12.26 ~ 1.1)

  getDateRangeFromWeek(2023, 2) ==> input<'week'> 기준 (2023, 1) (1.2 ~ 1.8)
  getDateRangeFromWeek(2023, 53) ==> input<'week'> 기준 (2023, 52) (12.25 ~ 12.31)

  getDateRangeFromWeek(2024, 2) ==> input<'week'> 기준 (2024, 1) (1.1 ~ 1.7)       *** getDateRangeFromWeek(2024, 1) == getDateRangeFromWeek(2024, 2)
  getDateRangeFromWeek(2024, 53) ==> input<'week'> 기준 (2024, 52) (12.23 ~ 12.29)
  ################################################################################### 이상 input_week + 1 == selected week
  getDateRangeFromWeek(2025, 1) ==> input<'week'> 기준 (2025, 1) (12.30 ~ 1.5)
  getDateRangeFromWeek(2025, 52) ==> input<'week'> 기준 (2025, 52) (12.22 ~ 12.28)

  getDateRangeFromWeek(2026, 1) ==> input<'week'> 기준 (2026, 1) (12.29 ~ 1.4)
  getDateRangeFromWeek(2026, 53) ==> input<'week'> 기준 (2026, 53) (12.28 ~ 1.3)
  ################################################################################### 이상 input_week == selected week
  getDateRangeFromWeek(2027, 2) ==> input<'week'> 기준 (2027, 1) (1.4 ~ 1.10)
  getDateRangeFromWeek(2027, 53) ==> input<'week'> 기준 (2027, 52) (12.27 ~ 1.2)

  getDateRangeFromWeek(2028, 2) ==> input<'week'> 기준 (2028, 1) (1.3 ~ 1.9)
  getDateRangeFromWeek(2028, 53) ==> input<'week'> 기준 (2028, 52) (12.25 ~ 12.31)

  getDateRangeFromWeek(2029, 2) ==> input<'week'> 기준 (2029, 1) (1.1 ~ 1.7)       *** getDateRangeFromWeek(2029, 1) == getDateRangeFromWeek(2029, 2)
  getDateRangeFromWeek(2029, 53) ==> input<'week'> 기준 (2029, 52) (12.24 ~ 12.30)
  ################################################################################### input_week + 1 == selected week
  getDateRangeFromWeek(2030, 1) ==> input<'week'> 기준 (2030, 1) (12.31 ~ 1.6)
  getDateRangeFromWeek(2030, 52) ==> input<'week'> 기준 (2030, 52) (12.23 ~ 12.29)

  getDateRangeFromWeek(2031, 1) ==> input<'week'> 기준 (2031, 1) (12.30 ~ 1.5)
  getDateRangeFromWeek(2031, 52) ==> input<'week'> 기준 (2031, 52) (12.22 ~ 12.28)

  getDateRangeFromWeek(2032, 1) ==> input<'week'> 기준 (2032, 1) (12.29 ~ 1.4)
  getDateRangeFromWeek(2032, 53) ==> input<'week'> 기준 (2032, 53) (12.27 ~ 1.2)
  ################################################################################### 이상 input_week == selected week
  getDateRangeFromWeek(2033, 2) ==> input<'week'> 기준 (2033, 1) (1.3 ~ 1.9)
  getDateRangeFromWeek(2033, 53) ==> input<'week'> 기준 (2033, 52) (12.26 ~ 1.1)

  getDateRangeFromWeek(2034, 2) ==> input<'week'> 기준 (2034, 1) (1.2 ~ 1.8)
  getDateRangeFromWeek(2034, 53) ==> input<'week'> 기준 (2034, 52) (12.25 ~ 12.31)

  getDateRangeFromWeek(2035, 2) ==> input<'week'> 기준 (2035, 1) (1.1 ~ 1.7)      *** getDateRangeFromWeek(2035, 1) == getDateRangeFromWeek(2035, 2)
  getDateRangeFromWeek(2035, 53) ==> input<'week'> 기준 (2035, 52) (12.24 ~ 12.30)
  ################################################################################### input_week + 1 == selected week
  getDateRangeFromWeek(2036, 1) ==> input<'week'> 기준 (2036, 1) (12.31 ~ 1.6)
  getDateRangeFromWeek(2036, 52) ==> input<'week'> 기준 (2036, 52) (12.22 ~ 12.28)

  :param year: year(YYYY)
  :param week_number: month(mm)
  # Either (String, String) or (int, int) is OK.
  # But month format is 'ww', so if value 01~09 and
  # you want to set parameter type as int, you must convert string 'ww' to int 'w'.
  :return:
  """
  if year in ['2022', '2023', '2024', '2027', '2028', '2029', '2033', '2034', '2035']:
    corrected_week_number = int(week_number) + 1  # int("01" ~ "09) => 1 ~ 9

    firstdate_of_week = datetime.datetime.strptime(f'{year}-W{int(corrected_week_number)-1}-1', "%Y-W%W-%w").date()
    lastdate_of_week = firstdate_of_week + datetime.timedelta(days=6.9)
    return str(firstdate_of_week), str(lastdate_of_week)
  elif year in ['2025', '2026', '2030', '2031', '2032', '2036']:
    firstdate_of_week = datetime.datetime.strptime(f'{year}-W{int(week_number)-1}-1', "%Y-W%W-%w").date()
    lastdate_of_week = firstdate_of_week + datetime.timedelta(days=6.9)
    return str(firstdate_of_week), str(lastdate_of_week)
# endregion


# region user_question.py
def convert_index_to_sports(answer_array: list, list_type: str):
  # list_type == 'purpose', 'sports', 'equipment'는 응답값 index가 1부터 시작되므로 유의한다(DB에서 각 항목을 1번부터 관리하기 때문).
  if list_type == 'purpose' and len(answer_array) > 0:
    new_list = []
    for answer in answer_array:
      if answer == 1: new_list.append("체력강화/건강유지")
      elif answer == 2: new_list.append("다이어트")
      elif answer == 3: new_list.append("바른체형/신체정렬")
      elif answer == 4: new_list.append("근력향상")
      elif answer == 5: new_list.append("산전/산후관리")
      elif answer == 6: new_list.append("중증 통증관리")
    return new_list
  elif list_type == 'sports' and len(answer_array) > 0:
    new_list = []
    for answer in answer_array:
      if answer == 1: new_list.append("무관")
      elif answer == 2: new_list.append("요가")
      elif answer == 3: new_list.append("필라테스")
      elif answer == 4: new_list.append("웨이트")
      elif answer == 5: new_list.append("유산소")
      elif answer == 6: new_list.append("무산소")
    return new_list
  elif list_type == 'disease' and len(answer_array) > 0:
    new_list = []
    for answer in answer_array:
      if answer == 0: new_list.append("허리디스크")
      elif answer == 1: new_list.append("목디스크")
      elif answer == 2: new_list.append("고혈압")
      elif answer == 3: new_list.append("저혈압")
      elif answer == 4: new_list.append("천식")
      elif answer == 5: new_list.append("당뇨")
      elif answer == 6: new_list.append("기타(수술이력, 사고이력)")
    return new_list
  elif list_type == 'age_group' and len(answer_array) > 0:
    new_list = []
    for answer in answer_array:
      if answer == 0: new_list.append("10대")
      elif answer == 1: new_list.append("20대")
      elif answer == 2: new_list.append("30대")
      elif answer == 3: new_list.append("40대")
      elif answer == 4: new_list.append("50대")
      elif answer == 5: new_list.append("60대")
      elif answer == 6: new_list.append("70대+")
    return new_list
  elif list_type == 'experience_group' and len(answer_array) > 0:
    new_list = []
    for answer in answer_array:
      if answer == 0: new_list.append("처음")
      elif answer == 1: new_list.append("~1개월 이내")
      elif answer == 2: new_list.append("~3개월 이내")
      elif answer == 3: new_list.append("~6개월 이내")
      elif answer == 4: new_list.append("~1년 이내")
      elif answer == 5: new_list.append("~3년 이내")
      elif answer == 6: new_list.append("~5년 이내")
      elif answer == 7: new_list.append("5년 이상")
    return new_list
# endregion


# region purchase.py
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


# endregion
