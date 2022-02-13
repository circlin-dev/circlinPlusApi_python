from . import api
from global_things.constants import API_ROOT
from global_things.functions.slack import slack_error_notification
from global_things.functions.general import login_to_db, check_session, query_result_is_none
from flask import request, url_for
import json
from pypika import MySQLQuery as Query, Table, Order


@api.route('/trial', methods=['POST'])
def add_trial():
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    endpoint = API_ROOT + url_for('api.add_trial')
    # session_id = request.headers['Authorization']
    parameters = json.loads(request.get_data(), encoding='utf-8')
    user_id = parameters['user_id']
    """Define tables required to execute SQL."""
    user_questions = Table('user_questions')
    user_lectures = Table('user_lectures')
    user_lecture_clips = Table('user_lecture_clips')

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
        user_id == user_id
    ).orderby(
        user_questions.id, order=Order.desc
    ).limit(1)

    cursor.execute(sql.get_sql())
    data = cursor.fetchall()
    data = json.loads(data[0][0].replace("\\", "\\\\"), strict=False)  # To prevent decoding error.


    # data['sports']   # => 리스트 타입
    # data['gender']   # 문자열: M, W
    #
    # data['level']  # 문자열: 고, 중, 저

    """case: 1 ~ 19"""
    # case 9: 필라테스, 남자, 저강도를 기준으로 입력

    # dict = {
    #     'day': 1,
    #     'program_lecture_id':
    # }
    sql = Query.into(
        user_lectures
    ).columns(
        'user_id',
        'program_lecture_id',
        'scheduled_at'
    ).insert(
        user_id,

    )


sql = '''
        SELECT DISTINCT
                    (SELECT l.`type` FROM lectures l WHERE l.id = clip.lecture_id) AS `type`,
                    c.id AS clip_id, 
                    c.title,
                    CASE 
                        WHEN c.action_count = 0 THEN (c.intro_duration + 15)
                        WHEN c.action_count > 0 THEN c.intro_duration + (15 * 3) + 2
                    END AS duration,
                    c.intro_duration, 
                    c.action_count
            FROM
                clips c
            INNER JOIN(
                        SELECT 
                                lc.id, 
                                lc.lecture_id, 
                                lc.`order`, 
                                lc.clip_id, 
                                lc.duration, 
                                lc.intro_duration, 
                                lc.action_duration, 
                                lc.action_count 
                            FROM 
                                lecture_clips lc
                            INNER JOIN(
                                        SELECT 
                                                pl.id, 
                                                pl.program_id, 
                                                pl.lecture_id
                                            FROM 
                                                program_lectures pl
                                            INNER JOIN (SELECT
                                                            l.id, 
                                                            l.title, 
                                                            l.`type`, 
                                                            l.coach_id
                                                        FROM 
                                                            lectures l
                                                        JOIN coaches c
                                                            ON l.coach_id = c.id
                                                        WHERE c.name="{강사이름}}"
                                                            AND l.title="{lecture 제목}"
                                                             OR	l.title="{lecture 제목(실습)}") AS lecture
                                        ON pl.lecture_id = lecture.id) AS program_lecture
                            ON program_lecture.lecture_id = lc.lecture_id) AS clip
                                ON c.id = clip.clip_id OR c.id=297'''  # OR c.title="(임시)휴식클립"