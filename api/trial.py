from . import api
from global_things.error_handler import HandleException
from global_things.constants import API_ROOT
from global_things.functions.slack import slack_error_notification
from global_things.functions.general import login_to_db, query_result_is_none
from global_things.functions.trial import send_aligo_free_trial
from global_things.functions.trial import TRIAL_DICTIONARY, replace_text_to_level
from datetime import datetime, timedelta
from flask import request, url_for
import json
from pypika import MySQLQuery as Query, Table, Criterion, functions as fn
import random
import requests


@api.route('/trial', methods=['POST'])  # 매니저 배정 리턴값을 받은 후!
def create_trial():
    ip = request.headers["X-Forwarded-For"]
    endpoint = API_ROOT + url_for('api.create_trial')
    # user_token = request.headers.get('Authorization')
    parameters = json.loads(request.get_data(), encoding='utf-8')
    user_id = parameters['user_id']
    user_question_id = parameters['user_question_id']

    """Define tables required to execute SQL."""
    users = Table('users')
    user_questions = Table('user_questions')
    user_lectures = Table('user_lectures')
    lectures = Table('lectures')

    connection = login_to_db()
    cursor = connection.cursor()

    # Verify user is valid or not.
    # verify_user = check_user_token(cursor, user_token)
    # if verify_user['result'] is False:
    #     connection.close()
    #     message = 'No token at request header.' if user_token is None else 'Unauthorized user.'
    #     result = {
    #         'result': False,
    #         'message': message
    #     }
    #     return json.dumps(result, ensure_ascii=False), 401
    # user_id = verify_user['user_id']
    # user_nickname = verify_user['user_nickname']

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
    # 복싱, 기타 종목은 잠정적으로 서킷 트레이닝의 강의를 배정해 주기로 한다.
    # 이를 위해, '기타'와 '복싱' 종목을 '서킷 트레이닝'으로 바꾼 다음, 중복을 없앤다.
    selected_sports = [title if title !='기타' and title != '복싱' else '서킷 트레이닝' for title in answer['sports']]
    sports_list = list(set(selected_sports))
    # if len(answer['sports']) == 1:
    #     selected_exercise = answer['sports'][:1]  # list with string
    # elif len(answer['schedule']) >= 2:
    #     selected_exercise = random.sample(answer['sports'], 2)
    if len(sports_list) == 1:
        selected_exercise = sports_list[:1]  # list with string
    elif len(answer['schedule']) >= 2:
        selected_exercise = random.sample(sports_list, 2)
    else:
        connection.close()
        result = {
            'result': False,
            'message': "Invalid data: User didn't selected 1 or more exercises."
        }
        return json.dumps(result, ensure_ascii=False), 400

    # 검증 2: 유저가 이미 무료 강의들을 배정받은 기록이 있는지 여부
    sql = Query.from_(
        user_lectures
    ).select(
        user_lectures.lecture_id,
        lectures.program_id
    ).join(
        lectures
    ).on(
        lectures.id == user_lectures.lecture_id
    ).where(
        Criterion.all([
            user_lectures.user_id == user_id,
            lectures.program_id.isnull(),
            user_lectures.deleted_at.isnull()
        ])
    ).get_sql()

    cursor.execute(sql)
    free_lecture_on_progress = cursor.fetchall()

    if query_result_is_none(free_lecture_on_progress) is False:
        connection.close()
        result = {
            'result': False,
            'message': 'Failed to create 1 week free trial(1 week free trial already exists).'
        }
        return json.dumps(result, ensure_ascii=False), 400

    sql = Query.from_(
        users
    ).select(
        users.phone,
        users.nickname
    ).where(
        users.id == user_id
    ).get_sql()
    cursor.execute(sql)
    user_phone, user_nickname = cursor.fetchall()[0]

    for sport in selected_exercise:
        # 여기서 종목 리스트만큼 순회하면서, 종목별 강의 배정을 한다.
        free_week_routines = TRIAL_DICTIONARY[sport][gender]  # list
        free_week_routines = sorted(free_week_routines, key=lambda x: x['day'])

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
                sql = Query.into(
                    user_lectures
                ).columns(
                    user_lectures.created_at,
                    user_lectures.updated_at,
                    user_lectures.user_id,
                    user_lectures.lecture_id,
                    user_lectures.level,
                    user_lectures.scheduled_at
                ).insert(
                    fn.Now(),
                    fn.Now(),
                    user_id,
                    routine['lecture_id'],
                    selected_level,
                    fn.Timestamp(scheduled_at)
                ).get_sql()
                try:
                    cursor.execute(sql)
                    connection.commit()
                except Exception as e:
                    connection.rollback()
                    connection.close()
                    raise HandleException(user_ip=ip,
                                          nickname=user_nickname,
                                          user_id=user_id,
                                          api=endpoint,
                                          error_message=f"Server Error while executing INSERT query(user_questions): {str(e)}",
                                          query=sql,
                                          method=request.method,
                                          status_code=500,
                                          payload=json.dumps(data, ensure_ascii=False),
                                          result=False)
            else:
                pass
    connection.close()
    send_aligo = send_aligo_free_trial(user_phone, user_nickname)
    if send_aligo is True:
        result = {'result': True, 'message': 'Created 7 days free trial routine.'}
        return json.dumps(result, ensure_ascii=False), 201
    else:
        raise HandleException(user_ip=ip,
                              nickname=user_nickname,
                              user_id=user_id,
                              api=endpoint,
                              error_message=f"Failed to send aligo message to free trial user.",
                              query=sql,
                              method=request.method,
                              status_code=500,
                              payload=json.dumps(data, ensure_ascii=False),
                              result=False)

