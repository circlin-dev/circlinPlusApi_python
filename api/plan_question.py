from global_things.functions import slack_error_notification, login_to_db, check_user
from . import api
from flask import request
import json
import pymysql

@api.route('/plan-question/add', methods=['POST'])
def add_plan_question():
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
  disease_detail = None

  # result = {
  #   'user_id': [user_id, str(type(user_id))],
  #   'purpose': [purpose, str(type(purpose))],
  #   'sports': [sports, str(type(sports))],
  #   'sex': [sex, str(type(sex))],
  #   'age_group': [age_group, str(type(age_group))],
  #   'experience_group': [experience_group, str(type(experience_group))],
  #   'schedule': [schedule, str(type(schedule))],
  #   'disease': [disease, str(type(disease))],
  #   'disease_detail': [disease_detail, str(type(disease_detail))],
  # }
  # return json.dumps(result, ensure_ascii=False), 200

  if type(disease[-1]) == str:
    disease_detail = disease[-1]
    del disease[-1]
  else:
    pass

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
  if is_valid_user['result'] == False:
    connection.close()
    result = {
      'result': False,
      'error': f"Cannot find user {user_id}: No such user."
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
    return json.dumps(result, ensure_ascii=False), 500
  elif is_valid_user['result'] == True:
    pass

  # query = 'INSERT INTO user_plan_questions (user_id, data) VALUES(%s, %s)'
  query_value = f"'purpose': {purpose}, 'sports': {sports}, 'sex': {sex}, 'age_group': {age_group}, 'experience_group': {experience_group}, 'schedule': {schedule}, 'disease', {disease}, 'disease_detail', {disease_detail}"
  query_value = "{" + query_value + "}"
  json_data = pymysql.escape_string(query_value)
  # "purpose", {str(purpose)}
  # "sports", {str(sports)}
  # "sex", {sex}
  # "age_group", {age_group}, "experience_group", {experience_group}, "schedule", {str(schedule)},
  # "disease", {str(disease)}, "disease_detail", {disease_detail}'
  # values = (user_id, json_data)

  query = f"INSERT INTO user_plan_questions (user_id, data) VALUES({user_id}, '" + json_data + "')"

  try:
    # cursor.execute(query, values)
    cursor.execute(query)
    connection.commit()
  except Exception as e:
    connection.close()
    error = str(e)
    result = {
      'result': False,
      'error': f'Server Error while executing INSERT query(user_plan_questions): {error}'
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
    return json.dumps(result, ensure_ascii=False), 500

  connection.close()
  result = {'result': True}
  return json.dumps(result, ensure_ascii=False), 201


@api.route('/plan-question/read/<user_id>', methods=['GET'])
def read_plan_question(user_id):
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
  if is_valid_user['result'] == False:
    connection.close()
    result = {
      'result': False,
      'error': f"Cannot find user {user_id}: No such user."
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
    return json.dumps(result, ensure_ascii=False), 500
  elif is_valid_user['result'] == True:
    pass

  # Get users latest bodylab data = User's data inserted just before.
  query = f'''
     SELECT 
           purpose, sports,
           sex, age_group,
           experience_group,
           schedule, disease,
           disease_detail
       FROM
           user_plan_questions
       WHERE
           user_id={user_id}
       ORDER BY id DESC LIMIT 1'''

  cursor.execute(query)
  latest_answers = cursor.fetchall()
  if len(latest_answers) == 0 or latest_answers == ():
    connection.close()
    result = {
      'result': False,
      'error': f'Cannot find requested answer data of user(id: {user_id})(users)'
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
    return json.dumps(result, ensure_ascii=False), 400
  else:
    connection.close()
    result = {
      'result': True,
      'purpose': latest_answers[0][0],
      'sports': latest_answers[0][1],
      'sex': latest_answers[0][2],
      'age_group': latest_answers[0][3],
      'experience_group': latest_answers[0][4],
      'schedule': latest_answers[0][5],
      'disease': latest_answers[0][6],
      'disease_detail': latest_answers[0][7],
    }
    return json.dumps(result, ensure_ascii=False), 201
