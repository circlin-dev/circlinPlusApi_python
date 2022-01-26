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


def amount_to_be_paid():
  """
  Must add purchase options as parameter!
  :return: Total amount to be paid(int).
  """
  return 1004  # Calculate sales price by purchase options.


def data_to_assign_manager(connection, user_id: int):
  cursor = connection.cursor()
  query = f"""SELECT
                    data
                FROM
                    user_questions
              WHERE
                    user_id={user_id}
              ORDER BY id DESC LIMIT 1"""
  cursor.execute(query)
  latest_answers = json.loads(cursor.fetchall()[0][0].replace("\\", "\\\\"), strict=False)
  user_sex = latest_answers['sex']
  return user_sex
