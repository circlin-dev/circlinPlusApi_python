from . import api
from global_things.constants import API_ROOT
from global_things.functions.slack import slack_error_notification
from global_things.functions.general import login_to_db, check_session, query_result_is_none
from global_things.functions.trial import TRIAL_DICTIONARY, replace_text_to_level
from datetime import datetime, timedelta
from flask import request, url_for
import json
from pypika import MySQLQuery as Query, Table, Criterion
import random


@api.route('/trial', methods=['POST'])  # 매니저 배정 리턴값을 받은 후!
def create_trial():
    ip = request.headers["X-Forwarded-For"]
    endpoint = API_ROOT + url_for('api.create_trial')
    # session_id = request.headers['Authorization']
    parameters = json.loads(request.get_data(), encoding='utf-8')
    user_id = parameters['user_id']
    user_question_id = parameters['user_question_id']

    """Define tables required to execute SQL."""
    user_questions = Table('user_questions')

    try:
        connection = login_to_db()
    except Exception as e:
        error = str(e)
        result = {
            'result': False,
            'error': f'Server Error while connecting to DB: {error}'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], method=request.method)
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
    #   slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], method=request.method)
    #   return json.dumps(result, ensure_ascii=False), 401
    # elif is_valid_user['result'] is True:
    #   pass

    sql = Query.from_(
        user_questions
    ).select(
        user_questions.data
    ).where(
        Criterion.all([
            user_questions.user_id == user_id,
            user_questions.id == user_question_id
        ])
    ).get_sql()
    cursor.execute(sql)
    data = cursor.fetchall()
    # 검증 1: 사전설문 응답값 테이블에 전달받은 user id, id값에 해당하는 데이터가 있는지 여부
    if query_result_is_none(data) is True:
        connection.close()
        result = {
            'result': False,
            'message': 'Failed to create 1 week free trial(Cannot find user or user_question data).'
        }
        return json.dumps(result, ensure_ascii=False), 400

    answer = json.loads(data[0][0].replace("\\", "\\\\"), strict=False)  # To prevent decoding error.
    gender = answer['gender']  # M , W
    schedule_list = answer['schedule']
    '''
    # 운동 종목별로 각각의 무료 프로그램 준비가 완료되면, 
    # 선택한 N개의 운동 중 임의로 두 종목을 선택해 무료 프로그램을 부여하는 로직을 적용한다.
    '''
    if len(answer['sports']) == 1:
        selected_exercise = answer['sports'][:1]  # list with string
    elif len(answer['schedule']) >= 2:
        selected_exercise = random.sample(answer['sports'], 2)
    else:
        connection.close()
        result = {
            'result': False,
            'message': "Invalid data: User didn't selected 1 or more exercises."
        }
        return json.dumps(result, ensure_ascii=False), 400

    for sport in selected_exercise:
        # 여기서 종목 리스트만큼 순회하면서, 종목별 강의 배정을 한다.

    # selected_exercise = answer['sports'][0]  # list with string
        free_week_routines = TRIAL_DICTIONARY[sport][gender]  # list
        free_week_routines = sorted(free_week_routines, key=lambda x: x['day'])

        # 검증 2: 유저가 이미 무료 강의들을 배정받은 기록이 있는지 여부
        sql = f"""
            SELECT 
                ul.lecture_id,
                l.program_id 
            FROM 
                user_lectures ul
            INNER JOIN
                lectures l
                ON l.id = ul.lecture_id
            WHERE user_id={user_id}
            AND l.program_id IS NULL
            AND ul.deleted_at IS NULL
        """
        cursor.execute(sql)
        free_lecture_on_progress = cursor.fetchall()

        if query_result_is_none(free_lecture_on_progress) is False:
            connection.close()
            result = {
                'result': False,
                'message': 'Failed to create 1 week free trial(1 week free trial already exists).'
            }
            return json.dumps(result, ensure_ascii=False), 400

        for schedule in schedule_list:
            schedule_date_text, schedule_time_text = schedule.split(' ')
            if schedule_date_text == '월':
                schedule_date = 0
            elif schedule_date_text == '화':
                schedule_date = 1
            elif schedule_date_text == '수':
                schedule_date = 2
            elif schedule_date_text == '목':
                schedule_date = 3
            elif schedule_date_text == '금':
                schedule_date = 4
            elif schedule_date_text == '토':
                schedule_date = 5
            else:
                schedule_date = 6
            hour_schedule = int(schedule_time_text.split(':')[0])
            minute_schedule = int(schedule_time_text.split(':')[1])
            now = datetime.now()
            date_today = now.weekday()
            # hour_now = now.hour
            # minute_now = now.minute
            request_schedule = datetime(now.year, now.month, now.day, hour_schedule, minute_schedule) - timedelta(days=date_today) + timedelta(days=schedule_date)
            request_schedule_30m = datetime(now.year, now.month, now.day, hour_schedule, minute_schedule) - timedelta(days=date_today) + timedelta(days=schedule_date) + timedelta(minutes=30)
            request_schedule_7d = datetime(now.year, now.month, now.day, hour_schedule, minute_schedule) - timedelta(days=date_today) + timedelta(days=schedule_date) + timedelta(days=7)

            if schedule_date > date_today:
                scheduled_at = request_schedule.strftime('%Y-%m-%d %H:%M:00')  # request_schedule에 배정
                pass
            elif schedule_date < date_today:
                scheduled_at = request_schedule_7d.strftime('%Y-%m-%d %H:%M:00')  # request_schedule + 7days에 배정
                pass
            else:   # date_schedule == date_today
                if now < request_schedule_30m:
                    scheduled_at = request_schedule.strftime('%Y-%m-%d %H:%M:00')  # request_schedule 에 배정
                    pass
                else:   # now >= request_schedule_30m
                    scheduled_at = request_schedule_7d.strftime('%Y-%m-%d %H:%M:00')  # request_schedule + 7 days에 배정
                    pass

            to_be_scheduled = [x for x in free_week_routines if x['day'] == schedule_date]

            for routine in to_be_scheduled:

                if routine['type'] == 'guide':
                    selected_level = 0
                else:
                    selected_level = replace_text_to_level(answer['level'])
                sql = f"""
                    INSERT INTO
                        user_lectures(created_at, updated_at, user_id, lecture_id, level, scheduled_at)
                    VALUES
                        ((SELECT NOW()), (SELECT NOW()), {user_id}, {routine['lecture_id']}, {selected_level}, TIMESTAMP('{scheduled_at}'))"""
                try:
                    cursor.execute(sql)
                    connection.commit()
                except Exception as e:
                    connection.rollback()
                    connection.close()
                    error = str(e)
                    result = {
                        'result': False,
                        'error': f'Server Error while executing INSERT query(user_questions): {error}'
                    }
                    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], query=sql, method=request.method)
                    return json.dumps(result, ensure_ascii=False), 500
            else:
                pass

    connection.close()
    result = {'result': True, 'message': 'Created 7 days free trial routine.'}

    return json.dumps(result, ensure_ascii=False), 201
