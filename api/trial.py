from . import api
from global_things.constants import API_ROOT
from global_things.functions.slack import slack_error_notification
from global_things.functions.general import login_to_db, check_session, query_result_is_none
from global_things.functions.trial import TRIAL_DICTIONARY
from flask import request, url_for
import json
from pypika import MySQLQuery as Query, Table, Criterion


@api.route('/trial', methods=['POST'])  # 매니저 배정 리턴값을 받은 후!
def create_trial():
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    endpoint = API_ROOT + url_for('api.create_trial')
    # session_id = request.headers['Authorization']
    parameters = json.loads(request.get_data(), encoding='utf-8')
    user_id = parameters['user_id']
    user_question_id = parameters['user_question_id']

    """Define tables required to execute SQL."""
    user_questions = Table('user_questions')
    user_lectures = Table('user_lectures')

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
    # is_valid_user = check_session(cursor, session_id)
    # if is_valid_user['result'] is False:
    #   connection.close()
    #   result = {
    #     'result': False,
    #     'error': f"Cannot find user {user_id}: No such user."
    #   }
    #   slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
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
            'message': 'Failed to create 1 week free trial(Cannot fine user or user_question data).'
        }
        return json.dumps(result, ensure_ascii=False), 400

    answer = json.loads(data[0][0].replace("\\", "\\\\"), strict=False)  # To prevent decoding error.
    gender = answer['gender']  # M , W
    selected_exercise = answer['sports'][0]  # list with string
    selected_level = 0
    if answer['level'] == '저':
        pass
    elif answer['level'] == '중':
        selected_level = 1
    else:
        selected_level = 2

    # case 4(피트니스, 여자, 고강도), 5(피트니스, 여자, 중강도), 6(피트니스, 여자, 저강도) => 7일치 모두 완료
    # case 9: 필라테스, 남자, 저강도를 기준으로 입력
    # 'guide'는 원래 있던 것, 'drill'은 새로 만든(무료)로! => user_lecture 만드는 로직 여쭤보기
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
    # 검증 2: 유저가 이미 무료 강의들을 배정받은 기록이 있는지 여부
    if query_result_is_none(free_lecture_on_progress) is False:
        connection.close()
        result = {
            'result': False,
            'message': 'Failed to create 1 week free trial(1 week free trial already exists).'
        }
        return json.dumps(result, ensure_ascii=False), 400

    week_routines = TRIAL_DICTIONARY[selected_exercise][gender]  # list
    week_routines = sorted(week_routines, key=lambda x: x['day'])
    sql = f"""
        INSERT INTO
            user_lectures(created_at, updated_at, user_id, lecture_id, level, scheduled_at)
        VALUES
            ((SELECT NOW()), (SELECT NOW()), {user_id}, {week_routines[0]['lecture_id']}, {selected_level}, (SELECT NOW() + INTERVAL {week_routines[0]['day']} DAY)),
            ((SELECT NOW()), (SELECT NOW()), {user_id}, {week_routines[1]['lecture_id']}, {selected_level}, (SELECT NOW() + INTERVAL {week_routines[1]['day']} DAY)),
            ((SELECT NOW()), (SELECT NOW()), {user_id}, {week_routines[2]['lecture_id']}, {selected_level}, (SELECT NOW() + INTERVAL {week_routines[2]['day']} DAY)),
            ((SELECT NOW()), (SELECT NOW()), {user_id}, {week_routines[3]['lecture_id']}, {selected_level}, (SELECT NOW() + INTERVAL {week_routines[3]['day']} DAY)),
            ((SELECT NOW()), (SELECT NOW()), {user_id}, {week_routines[4]['lecture_id']}, {selected_level}, (SELECT NOW() + INTERVAL {week_routines[4]['day']} DAY)),
            ((SELECT NOW()), (SELECT NOW()), {user_id}, {week_routines[5]['lecture_id']}, {selected_level}, (SELECT NOW() + INTERVAL {week_routines[5]['day']} DAY)),
            ((SELECT NOW()), (SELECT NOW()), {user_id}, {week_routines[6]['lecture_id']}, {selected_level}, (SELECT NOW() + INTERVAL {week_routines[6]['day']} DAY))"""
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
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=sql)
        return json.dumps(result, ensure_ascii=False), 500

    connection.close()
    result = {'result': True, 'message': 'Created 7 days free trial routine.'}

    return json.dumps(result, ensure_ascii=False), 201










# sql = '''
#         SELECT DISTINCT
#                     (SELECT l.`type` FROM lectures l WHERE l.id = clip.lecture_id) AS `type`,
#                     c.id AS clip_id,
#                     c.title,
#                     CASE
#                         WHEN c.action_count = 0 THEN (c.intro_duration + 15)
#                         WHEN c.action_count > 0 THEN c.intro_duration + (15 * 3) + 2
#                     END AS duration,
#                     c.intro_duration,
#                     c.action_count
#             FROM
#                 clips c
#             INNER JOIN(
#                         SELECT
#                                 lc.id,
#                                 lc.lecture_id,
#                                 lc.`order`,
#                                 lc.clip_id,
#                                 lc.duration,
#                                 lc.intro_duration,
#                                 lc.action_duration,
#                                 lc.action_count
#                             FROM
#                                 lecture_clips lc
#                             INNER JOIN(
#                                         SELECT
#                                                 pl.id,
#                                                 pl.program_id,
#                                                 pl.lecture_id
#                                             FROM
#                                                 program_lectures pl
#                                             INNER JOIN (SELECT
#                                                             l.id,
#                                                             l.title,
#                                                             l.`type`,
#                                                             l.coach_id
#                                                         FROM
#                                                             lectures l
#                                                         JOIN coaches c
#                                                             ON l.coach_id = c.id
#                                                         WHERE c.name="{강사이름}}"
#                                                             AND l.title="{lecture 제목}"
#                                                              OR	l.title="{lecture 제목(실습)}") AS lecture
#                                         ON pl.lecture_id = lecture.id) AS program_lecture
#                             ON program_lecture.lecture_id = lc.lecture_id) AS clip
#                                 ON c.id = clip.clip_id OR c.id=297'''  # OR c.title="(임시)휴식클립"