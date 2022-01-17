from global_things.functions import slack_error_notification, login_to_db, check_user
from . import api
from flask import request
import json

@api.route('/plan-question/add', methods=['POST'])
def add_plan_question():
  ip = request.remote_addr
  endpoint = '/api/plan-question/add'

  user_id = request.form.get('user_id')
  purpose = request.form.get('purpose')  # array
  sports = request.form.get('sports')  # array
  sex = request.form.get('sex')  # string
  age_group = request.form.get('age_group')  # string
  experience_group = request.form.get('experience_group')  # string
  schedule = request.form.get('schedule')  # array with index(int)
  disease = request.form.get('disease')  # array with index(int) & short sentence for index 7(string)
  disease_detail = None

  if type(disease[-1]) == str:
    disease_detail = request.form.get('disease')
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

  if not disease_detail:
    query = f" \
      INSERT INTO \
                user_plan_question( \
                user_id, purpose, \
                sports, sex, \
                age_group, exprience_group, \
                schedule, disease) \
          VALUES(%s, %s, \
                %s, %s, \
                %s, %s, \
                %s, %s)"
    values = (user_id, purpose,
              sports, sex,
              age_group, experience_group,
              schedule, disease)
  else:
    query = f" \
      INSERT INTO \
                user_plan_question( \
                user_id, purpose, \
                sports, sex, \
                age_group, exprience_group, \
                schedule, disease, \
                disease_detail) \
          VALUES(%s, %s, \
                %s, %s, \
                %s, %s, \
                %s, %s, \
                %s)"
    values = (user_id, purpose,
              sports, sex,
              age_group, experience_group,
              schedule, disease,
              disease_detail)

  try:
    cursor.execute(query, values)
    connection.commit()
  except Exception as e:
    connection.close()
    error = str(e)
    result = {
      'result': False,
      'error': f'Server Error while executing INSERT query(user_plan_question): {error}'
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
           user_plan_question
       WHERE
           user_id={user_id}
       ORDER BY id DESC LIMIT 1'''

  cursor.execute(query)
  latest_answers = cursor.fetchall()
  if len(latest_answers) == 0 or latest_answers == ():
    connection.close()
    result = {
      'result': False,
      'error': f'Cannot find requested answer data of user(id: {user_id})(user_plan_question)'
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
