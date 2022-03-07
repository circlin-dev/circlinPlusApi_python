from . import api
from global_things.constants import API_ROOT
from global_things.functions.slack import slack_error_notification
from global_things.functions.general import login_to_db, check_session, parse_for_mysql, query_result_is_none
from global_things.functions.user_question import sort_schedule_by_date, replace_number_to_experience
from flask import request, url_for
import json
from pypika import MySQLQuery as Query, Table, Order, Criterion


@api.route('/user-question', methods=['POST'])
def add_user_question():
    ip = request.headers["X-Forwarded-For"]
    endpoint = API_ROOT + url_for('api.add_user_question')
    # session_id = request.headers['Authorization']
    parameters = json.loads(request.get_data(), encoding='utf-8')
    """Define tables required to execute SQL."""
    user_questions = Table('user_questions')

    try:
        user_id = int(parameters['user_id'])
        purpose = parameters['purpose']  # Array
        sports = parameters['sports']  # Array
        gender = parameters['gender']  # string
        age_group = parameters['age_group']  # string
        experience_group = parameters['experience_group']  # string
        schedule = parameters['schedule']  # Array
        disease = parameters['disease']  # Array
        disease_detail = parameters['disease_detail']  # None or string
        level = parameters['level']  # string
    except:
        result = {
            'result': False,
            'error': f'Missing data in request.'
        }
        error_log = f"{result['error']}, parameters({json.dumps(parameters, ensure_ascii=False)}),"
        slack_error_notification(user_ip=ip, api=endpoint, error_message=error_log, method=request.method, status_code=400)
        return json.dumps(result, ensure_ascii=False), 400
    # Verify if mandatory information is not null.
    if request.method == 'POST':
        """
        <사전 질문 검증하기>
        (1) 배정받은 프로그램
        (2) 기간이 끝나지 않은 이용권 Or 프로그램(무료)
        있다면 더 이상 질문에 대한 응답을 받으면 안 된다.
        """
        if not(user_id and purpose and sports and gender and age_group and experience_group and level and schedule):
            result = {
                'result': False,
                'error': f'Missing data in request.'
            }
            error_log = f"{result['error']}, parameters({json.dumps(parameters, ensure_ascii=False)}),"
            slack_error_notification(user_ip=ip, api=endpoint, error_message=error_log, method=request.method, status_code=400)
            return json.dumps(result, ensure_ascii=False), 400
        # Check if disease_detail is None, or disease_detail is empty string("" or " " or "  " ...).
        if len(disease) == 0 and (disease_detail is not None or (type(disease_detail) == str and len(disease_detail.strip()) > 0)):
            result = {
                'result': False,
                'error': f'User answered that he/she has no disease, but disease_detail has value.',
                'disease': disease,
                'disease_detail': disease_detail
            }
            return json.dumps(result, ensure_ascii=False), 400
        if level not in ["매우 약하게", "약하게", "보통", "강하게", "매우 강하게"]:
            result = {
                'result': False,
                'error': f"Invalid request parameter: 'level' should be ['매우 약하게', '약하게', '보통', '강하게', '매우 강하게']."
            }
            return json.dumps(result, ensure_ascii=False), 400
        if len(schedule) == 0 or "" in schedule:
            result = {
                'result': False,
                'error': f'Invalid request parameter: Schedule data is empty or invalid.',
                'schedule': schedule
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
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], method=request.method, status_code=500)
        return json.dumps(result, ensure_ascii=False), 500

    cursor = connection.cursor()

    # Verify user is valid or not.
    # is_valid_user = check_session(cursor, session_id)
    # if is_valid_user['result'] is False:
    #   connection.close()
    #   result = {
    #     'result': False,
    #     'error': f"Cannot find user {user_id}: No such user."
    #   }
    #   slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], method=request.method, status_code=401)
    #   return json.dumps(result, ensure_ascii=False), 401
    # elif is_valid_user['result'] is True:
    #   pass

    # Formatting json to INSERT into mysql database.
    json_data = json.dumps({
        "purpose": purpose,
        "sports": sports,
        "gender": gender,
        "age_group": age_group,
        "experience_group": experience_group,
        "disease": disease,
        "disease_detail": parse_for_mysql(disease_detail),
        "schedule": sort_schedule_by_date(schedule),
        "level": level
    }, ensure_ascii=False)
    sql = Query.into(
        user_questions
    ).columns(
        'user_id', 'data'
    ).insert(
        user_id, json_data
    ).get_sql()

    try:
        cursor.execute(sql)
        connection.commit()
        user_question_id = int(cursor.lastrowid)  # 사전설문 데이터 저장 후 client에 반환, 무료 체험 프로그램 배정 시 다시 parameter로 전송받음.
        connection.close()
    except Exception as e:
        connection.rollback()
        connection.close()
        error = str(e)
        result = {
            'result': False,
            'error': f'Server Error while executing INSERT query(user_questions): {error}'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], query=sql, method=request.method, status_code=500)
        return json.dumps(result, ensure_ascii=False), 500

    result = {'result': True, 'user_question_id': user_question_id}
    return json.dumps(result, ensure_ascii=False), 201


@api.route('/user/<user_id>/user-schedule', methods=['GET'])
def read_user_question(user_id):
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.read_user_question', user_id=user_id)
    # token = request.headers['token']
    """Define tables required to execute SQL."""

    try:
        connection = login_to_db()
    except Exception as e:
        error = str(e)
        result = {
            'result': False,
            'error': f'Server Error while connecting to DB: {error}'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], method=request.method, status_code=500)
        return json.dumps(result, ensure_ascii=False), 500

    cursor = connection.cursor()

    # Verify user is valid or not.
    # is_valid_user = check_token(cursor, user_id, token)
    # if is_valid_user['result'] is False:
    #   connection.close()
    #   result = {
    #     'result': False,
    #     'error': f"Invalid request: Unauthorized token or no such user({user_id})"
    #   }
    #   slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], method=request.method)
    #   return json.dumps(result, ensure_ascii=False), 401
    # elif is_valid_user['result'] is True:
    #   pass

    sql = f"""
        SELECT 
            uq.id,
            uq.created_at, 
            IFNULL(uq.updated_data, uq.data) AS answer
        FROM
            user_questions uq
        WHERE uq.user_id = {user_id}
        ORDER BY uq.id DESC
        LIMIT 1"""
    cursor.execute(sql)
    data = cursor.fetchall()
    if query_result_is_none(data) is True:
        connection.close()
        result = {
            'result': False,
            'error': f'Cannot find requested answer data of user(id: {user_id})(users)'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], method=request.method, status_code=401)
        return json.dumps(result, ensure_ascii=False), 401
    else:
        connection.close()
        answer_id = data[0][0]
        created_at = data[0][1]
        answer = data[0][2]
        result_dict = json.loads(answer.replace("\\", "\\\\"), strict=False)  # To prevent decoding error.
        result_dict['result'] = True
        # result_dict['schedule'] = sort_schedule_by_date(result_dict['schedule'])
        # result_dict['experience_group'] = replace_number_to_experience(result_dict['experience_group'])
        result_dict['id'] = answer_id
        result_dict['created_at'] = created_at.strftime('%Y-%m-%d %H:%M:%S')

        return json.dumps(result_dict, ensure_ascii=False), 200


@api.route('/user/<user_id>/user-schedule/<question_id>', methods=['PATCH'])
def update_user_question(user_id, question_id):
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.update_user_question', user_id=user_id, question_id=question_id)
    # token = request.headers['token']
    parameters = json.loads(request.get_data(), encoding='utf-8')
    """Define tables required to execute SQL."""
    user_questions = Table('user_questions')


    try:
        purpose = parameters['purpose']  # array
        sports = parameters['sports']  # array
        gender = parameters['gender']  # string
        age_group = parameters['age_group']  # string
        experience_group = parameters['experience_group']  # string
        schedule = parameters['schedule']  # array with index(string)
        disease = parameters['disease']  # short sentence for index 7(string)
        disease_detail = parameters['disease_detail']
        level = parameters['level']
    except:
        result = {
            'result': False,
            'error': f'Missing data in request.'
        }
        error_log = f"{result['error']}, parameters({json.dumps(parameters, ensure_ascii=False)}),"
        slack_error_notification(user_ip=ip, api=endpoint, error_message=error_log, method=request.method, status_code=400)
        return json.dumps(result, ensure_ascii=False), 400

    try:
        connection = login_to_db()
    except Exception as e:
        error = str(e)
        result = {
            'result': False,
            'error': f'Server Error while connecting to DB: {error}'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], method=request.method, status_code=500)
        return json.dumps(result, ensure_ascii=False), 500

    cursor = connection.cursor()

    # Verify user is valid or not.
    # is_valid_user = check_token(cursor, user_id, token)
    # if is_valid_user['result'] is False:
    #   connection.close()
    #   result = {
    #     'result': False,
    #     'error': f"Invalid request: Unauthorized token or no such user({user_id})"
    #   }
    #   slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], method=request.method, status_code=401)
    #   return json.dumps(result, ensure_ascii=False), 401
    # elif is_valid_user['result'] is True:
    #   pass

    json_data = json.dumps({
        "purpose": purpose,
        "sports": sports,
        "gender": gender,
        "age_group": age_group,
        "experience_group": experience_group,
        "disease": disease,
        "disease_detail": parse_for_mysql(disease_detail),
        "schedule": schedule,
        "level": level
    }, ensure_ascii=False)
    sql = Query.update(
        user_questions
    ).set(
        user_questions.updated_data, json_data
    ).where(
        Criterion.all([
            user_questions.user_id == user_id,
            user_questions.id == question_id
        ])
    ).get_sql()

    try:
        cursor.execute(sql)
        connection.commit()
        connection.close()
    except Exception as e:
        connection.rollback()
        connection.close()
        error = str(e)
        result = {
            'result': False,
            'error': f'Server Error while executing INSERT query(user_questions): {error}'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], query=sql, method=request.method, status_code=500)
        return json.dumps(result, ensure_ascii=False), 500

    result = {'result': True}

    return json.dumps(result, ensure_ascii=False), 200
