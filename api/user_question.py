from . import api
from global_things.functions.slack import slack_error_notification
from global_things.functions.general import login_to_db, check_user, query_result_is_none
from global_things.functions.user_question import convert_index_to_sports
from flask import request
import json
from pymysql.converters import escape_string


@api.route('/user-question/add', methods=['POST'])
def add_user_question():
  ip = request.remote_addr
  endpoint = '/api/plan-question/add'
  parameters = json.loads(request.get_data(), encoding='utf-8')

  user_id = parameters['user_id']
  purpose = parameters['purpose']  # array
  sports = parameters['sports']  # array
  sex = parameters['sex']  # string
  age_group = parameters['age_group']  # string
  experience_group = parameters['experience_group']  # string
  schedule = parameters['schedule']  # array with index(int)
  disease = parameters['disease']  # array with index(int) & short sentence for index 7(string)
  disease_detail = parameters['disease_detail']

  # Verify if mandatory information is not null.
  if request.method == 'POST':
    if not(user_id and purpose and sports and sex and age_group and experience_group):
      result = {
        'result': False,
        'error': f'Missing data in request.',
        'values': {
          'user_id': user_id,
          'purpose': purpose,
          'sports': sports,
          'sex': sex,
          'age_group': age_group,
          'experience_group': experience_group
        }
      }
      return json.dumps(result, ensure_ascii=False), 400

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
  is_valid_user = check_user(cursor, user_id)
  if is_valid_user['result'] is False:
    connection.close()
    result = {
      'result': False,
      'error': f"Cannot find user {user_id}: No such user."
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
    return json.dumps(result, ensure_ascii=False), 401
  elif is_valid_user['result'] is True:
    pass

  # Formatting json to INSERT into mysql database.
  # query_value = f'"purpose": {purpose}, "sports": {sports}, "sex": "{sex}", "age_group": {age_group}, "experience_group": {experience_group}, "schedule": {schedule}, "disease": {disease}, "disease_detail": "{disease_detail}"'
  # query_value = "{" + query_value + "}"
  # json_data = escape_string(query_value)
  # query = f"INSERT INTO user_questions (user_id, data) VALUES({user_id}, '" + json_data + "')"

  json_data = json.dumps({
    "purpose": purpose,
    "sports": sports,
    "sex": sex,
    "age_group": age_group,
    "experience_group": experience_group,
    "schedule": schedule,
    "disease": disease,
    "disease_detail": disease_detail
  }, ensure_ascii=False)
  query = f"INSERT INTO user_questions (user_id, data) VALUES({user_id}, '{json_data}')"

  try:
    cursor.execute(query)
    connection.commit()
  except Exception as e:
    connection.close()
    error = str(e)
    result = {
      'result': False,
      'error': f'Server Error while executing INSERT query(user_questions): {error}'
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
    return json.dumps(result, ensure_ascii=False), 500

  connection.close()
  result = {'result': True}
  return json.dumps(result, ensure_ascii=False), 201


@api.route('/user-question/read/<user_id>', methods=['GET'])
def read_user_question(user_id):
  ip = request.remote_addr
  endpoint = '/plan-question/read/<user_id>'

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
  is_valid_user = check_user(cursor, user_id)
  if is_valid_user['result'] is False:
    connection.close()
    result = {
      'result': False,
      'error': f"Cannot find user {user_id}: No such user."
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
    return json.dumps(result, ensure_ascii=False), 401
  elif is_valid_user['result'] is True:
    pass

  # Get users latest bodylab data = User's data inserted just before.
  query = f'''
     SELECT 
           data
       FROM
           user_questions
       WHERE
           user_id={user_id}
       ORDER BY id DESC LIMIT 1'''

  cursor.execute(query)
  latest_answers = cursor.fetchall()
  if query_result_is_none(latest_answers) is True:
    connection.close()
    result = {
      'result': False,
      'error': f'Cannot find requested answer data of user(id: {user_id})(users)'
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
    return json.dumps(result, ensure_ascii=False), 401
  else:
    connection.close()
    latest_answers = json.loads(latest_answers[0][0].replace("\\", "\\\\"), strict=False)  # To prevent decoding error.
    # latest_answers["sports"] = convert_index_to_sports(latest_answers["sports"], "sports")  # list -> list
    # latest_answers["purpose"] = convert_index_to_sports(latest_answers["purpose"], "purpose")  # list -> list
    # latest_answers["disease"] = convert_index_to_sports(latest_answers["disease"], "disease")  # list -> list
    # latest_answers["age_group"] = convert_index_to_sports([int(x) for x in str(latest_answers["age_group"])],
    #                                                       "age_group")[0]  # list -> index
    # latest_answers["experience_group"] = convert_index_to_sports([int(x) for x in str(latest_answers["experience_group"])],
    #                                                              "experience_group")[0]  # list -> index
    latest_answers['result'] = True
    return json.dumps(latest_answers, ensure_ascii=False), 201
