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