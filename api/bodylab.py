import datetime
from global_things.constants import API_ROOT, AMAZON_URL, BUCKET_NAME, BUCKET_BODY_IMAGE_INPUT_PATH, BODY_IMAGE_INPUT_PATH, BUCKET_ATFLEE_IMAGE_PATH, ATFLEE_IMAGE_INPUT_PATH
from global_things.functions.slack import slack_error_notification
from global_things.functions.general import login_to_db, check_session, query_result_is_none
from global_things.functions.bodylab import analyze_body_images, anaylze_atflee_images, upload_image_to_s3, standard_healthiness_score
from . import api
import cv2
from datetime import datetime
from flask import url_for, request
import json
import numpy as np
import os
from pypika import MySQLQuery as Query, Criterion, Table, Order
import shutil
from werkzeug.utils import secure_filename
"""2개의 이미지 전송
    -> 앳플리는 서버 저장 -> S3 저장 -> OCR
    -> 바디랩은 서버 저장 -> S3 저장 -> 바디랩 서버에 분석 -> 바디랩 서버에 키포인트 이미지 저장 -> S3 저장
    => OCR 데이터, 키포인트 수치 데이터 프론트에 반환 => 이상없는지 확인 후 수정된 내용을 DB 저장
    """


@api.route('/bodylab', methods=['POST'])
def weekly_bodylab():
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.weekly_bodylab')
    # token = request.headers['Authorization']
    data = request.form.to_dict()  # {'body': ~~~~~.png, 'atflee': ~~~~~.png}
    user_id = data['user_id']
    height = data['height']
    weight = data['weight']
    bmi = data['bmi']
    muscle_mass = data['muscle_mass']
    fat_mass = data['fat_mass']
    body_image = request.files.to_dict()['body_image']
    # atflee_image = request.files.to_dict()['atflee_image']

    if request.method == 'POST':
        """
        이미지 서버 임시 저장 & 업로드 코드 추가 필요
          - 눈바디 이미지, 앳플리 이미지 S3 업로드 후 URL 가져오는 코드 추가해야 함!
        """
        # period = request.form.get('period')  # Value format: yyyy-Www(Week 01, 2017 ==> "2017-W01")

        """Define tables required to execute SQL."""
        bodylabs = Table('bodylabs')
        bodylab_analyze_bodies = Table('bodylab_analyze_bodies')  # bodylab_body_images = Table('bodylab_body_images')
        # bodylab_analyze_atflees = Table('bodylab_analyze_atflees')
        user_questions = Table('user_questions')

        # Verify if mandatory information is not null.
        if not(user_id or height or weight or bmi or muscle_mass or fat_mass or body_image):
            result = {
                'result': False,
                'error': f'Missing data in request.',
                'values': {
                    'user_id': user_id,
                    'height': height,
                    'weight': weight,
                    'bmi': bmi,
                    'muscle_mass': muscle_mass,
                    'fat_mass': fat_mass,
                    'body_image': body_image
                }
            }
            return json.dumps(result, ensure_ascii=False), 400

        now = datetime.now().strftime('%Y%m%d%H%M%S')
        # year = period.split('-W')[0]
        # week_number_of_year = period.split('-W')[1]
        # firstdate_of_week, lastdate_of_week = get_date_range_from_week(year, week_number_of_year)
        if str(user_id) not in os.listdir(f"{BODY_IMAGE_INPUT_PATH}"):
            os.makedirs(f"{BODY_IMAGE_INPUT_PATH}/{user_id}")
        secure_file = secure_filename(body_image.filename)
        extension = secure_file.split('.')[-1]
        file_name = f'{user_id}_{now}.{extension}'

        local_image_path = f'{BODY_IMAGE_INPUT_PATH}/{user_id}/{file_name}'
        body_image.save(secure_file)
        if os.path.exists(secure_file):
            shutil.move(secure_file, f'{BODY_IMAGE_INPUT_PATH}/{user_id}')
            os.rename(f'{BODY_IMAGE_INPUT_PATH}/{user_id}/{secure_file}', local_image_path)

        object_name = f"{BUCKET_BODY_IMAGE_INPUT_PATH}/{user_id}/{file_name}"
        upload_result = upload_image_to_s3(local_image_path, BUCKET_NAME, object_name)
        if upload_result is True:
            pass
        else:
            result_dict = {
                'message': f'Failed to upload body image into S3({upload_result})',
                'result': False
            }
            return json.dumps(result_dict), 500
        s3_path_body_input = f"{AMAZON_URL}/{object_name}"
        if os.path.exists(local_image_path):
            os.remove(local_image_path)

        try:
            connection = login_to_db()
        except Exception as e:
            error = str(e)
            result = {
                'result': False,
                'error': f'Server Error while connecting to DB: {error}'
            }
            slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], method=request.method)
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
        #   slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], method=request.method)
        #   return json.dumps(result, ensure_ascii=False), 401
        # elif is_valid_user['result'] is True:
        #   pass


        """
        !!!데이터 추가 저장!!!
        - standard_healthiness_score()로 나에게의 권장되는 수치 및 차이 구해서 저장
        - 신체 수치는 1위와의 
        """
        sql = Query.from_(
            user_questions
        ).select(
            user_questions.data
        ).where(
            Criterion.all([
                user_questions.user_id == user_id
            ])
        ).orderby(
            user_questions.id, order=Order.desc
        ).limit(1).get_sql()
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
        answer = json.loads(data[0][0].replace("\\", "\\\\"), strict=False)
        gender = answer['gender']
        age_group = answer['age_group']

        ideal_fat_mass, ideal_muscle_mass, bmi_status = standard_healthiness_score(str(age_group), str(gender), float(weight), float(height), float(bmi))

        try:
            sql = Query.into(
                bodylabs
            ).columns(
                bodylabs.user_id,
                bodylabs.url_body_image,
                bodylabs.height,
                bodylabs.weight,
                bodylabs.bmi,
                bodylabs.bmi_status,
                bodylabs.muscle_mass,
                bodylabs.ideal_muscle_mass,
                bodylabs.fat_mass,
                bodylabs.ideal_fat_mass,
            ).insert(
                user_id,
                s3_path_body_input,
                height,
                weight,
                bmi,
                bmi_status,
                muscle_mass,
                ideal_muscle_mass,
                fat_mass,
                ideal_fat_mass
            ).get_sql()
            cursor.execute(sql)
            connection.commit()
        except Exception as e:
            connection.rollback()
            connection.close()
            error = str(e)
            result = {
                'result': False,
                'error': f'Server Error while executing INSERT query(bodylabs): {error}'
            }
            slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=sql, method=request.method)
            return json.dumps(result, ensure_ascii=False), 500

        # Get users latest bodylab data = User's data inserted just before.
        sql = Query.from_(
            bodylabs
        ).select(
            bodylabs.id
        ).where(
            bodylabs.user_id == user_id
        ).orderby(
            bodylabs.id, order=Order.desc
        ).limit(1).get_sql()
        cursor.execute(sql)
        latest_bodylab_id_tuple = cursor.fetchall()

        if query_result_is_none(latest_bodylab_id_tuple) is True:
            connection.rollback()
            connection.close()
            result = {
                'result': False,
                'error': f'Cannot find requested bodylab data of user(id: {user_id})(bodylab)'
            }
            slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=sql, method=request.method)
            return json.dumps(result, ensure_ascii=False), 400
        else:
            latest_bodylab_id = latest_bodylab_id_tuple[0][0]

        # Analyze user's image and store the result.
        body_analysis = json.loads(analyze_body_images(user_id, s3_path_body_input))
        result_code = body_analysis['status_code']
        if result_code == 200:
            analyze_result = body_analysis['result']
            sql = Query.into(
                bodylab_analyze_bodies
            ).columns(
                bodylab_analyze_bodies.bodylab_id,
                bodylab_analyze_bodies.url_output,
                bodylab_analyze_bodies.shoulder_ratio,
                bodylab_analyze_bodies.hip_ratio,
                bodylab_analyze_bodies.shoulder_width,
                bodylab_analyze_bodies.hip_width,
                bodylab_analyze_bodies.nose_to_shoulder_center,
                bodylab_analyze_bodies.shoulder_center_to_hip_center,
                bodylab_analyze_bodies.hip_center_to_ankle_center,
                bodylab_analyze_bodies.whole_body_length,
                bodylab_analyze_bodies.upperbody_lowerbody
            ).insert(
                latest_bodylab_id,
                analyze_result['output_url'],
                analyze_result['shoulder_ratio'],
                analyze_result['hip_ratio'],
                analyze_result['shoulder_width'],
                analyze_result['hip_width'],
                analyze_result['nose_to_shoulder_center'],
                analyze_result['shoulder_center_to_hip_center'],
                analyze_result['hip_center_to_ankle_center'],
                analyze_result['whole_body_length'],
                analyze_result['upper_body_lower_body']
            ).get_sql()
            try:
                cursor.execute(sql)
            except Exception as e:
                connection.rollback()
                connection.close()
                error = str(e)
                result = {
                    'result': False,
                    'error': f'Server error while executing INSERT query(bodylab_image): {error}'
                }
                slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=sql, method=request.method)
                return json.dumps(result, ensure_ascii=False), 400

            connection.commit()
            connection.close()
            result = {'result': True}
            return json.dumps(result, ensure_ascii=False), 201
        elif result_code == 400:
            connection.rollback()
            connection.close()
            result = {
                'result': False,
                'error': f"Failed to analysis requested image({user_id}, {s3_path_body_input}): {body_analysis['error']}"
            }
            slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], method=request.method)
            return json.dumps(result, ensure_ascii=False), 400
        elif result_code == 500:
            connection.rollback()
            connection.close()
            result = {
                'result': False,
                'error': f"Failed to analysis requested image({body_image}): {body_analysis['error']}"
            }
            slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], method=request.method)
            return json.dumps(result, ensure_ascii=False), 500
    else:
        result = {
            'result': False,
            'error': 'Method Not Allowed'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], method=request.method)
        return json.dumps(result, ensure_ascii=False), 403



@api.route('/user/<user_id>/bodylab', methods=['GET'])
def read_user_bodylab(user_id):
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.read_user_bodylab', user_id=user_id)
    # token = request.headers['Authorization']

    """Define tables required to execute SQL."""
    bodylabs = Table('bodylabs')
    bodylab_analyze_bodies = Table('bodylab_analyze_bodies')  # bodylab_body_images = Table('bodylab_body_images')
    # bodylab_analyze_atflees = Table('bodylab_analyze_atflees')

    try:
        connection = login_to_db()
    except Exception as e:
        error = str(e)
        result = {
            'result': False,
            'error': f'Server Error while connecting to DB: {error}'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], method=request.method)
        return json.dumps(result, ensure_ascii=False), 500
    cursor = connection.cursor()

    columns = ["bodylab_id",
               "created_at",
               "url_body_input",
               "height",
               "weight",
               "bmi",
               "bmi_status",
               "muscle_mass",
               "ideal_muscle_mass",
               "fat_mass",
               "ideal_fat_mass"
               "url_output",
               "shoulder_ratio",
               "hip_ratio",
               "shoulder_width",
               "hip_width",
               "nose_to_shoulder_center",
               "shoulder_center_to_hip_center",
               "hip_center_to_ankle_center",
               "whole_body_length",
               "upperbody_lowerbody"]
    sql = Query.from_(
        bodylabs
    ).select(
        bodylabs.id,
        bodylabs.created_at,
        bodylabs.url_body_image,
         # bodylabs.url_atflee_image,
        bodylabs.height,
        bodylabs.weight,
        bodylabs.bmi,
        bodylabs.bmi_status,
        bodylabs.muscle_mass,
        bodylabs.ideal_muscle_mass,
        bodylabs.fat_mass,
        bodylabs.ideal_fat_mass,
        bodylab_analyze_bodies.url_output,
        bodylab_analyze_bodies.shoulder_ratio,
        bodylab_analyze_bodies.hip_ratio,
        bodylab_analyze_bodies.shoulder_width,
        bodylab_analyze_bodies.hip_width,
        bodylab_analyze_bodies.nose_to_shoulder_center,
        bodylab_analyze_bodies.shoulder_center_to_hip_center,
        bodylab_analyze_bodies.hip_center_to_ankle_center,
        bodylab_analyze_bodies.whole_body_length,
        bodylab_analyze_bodies.upperbody_lowerbody
        #     bodylab_analyze_atflees.star
    ).join(
        bodylab_analyze_bodies
    ).on(
        bodylab_analyze_bodies.bodylab_id == bodylabs.id
        # ).join(
        #     bodylab_analyze_atflees
        # ).on(
        #     bodylab_analyze_atflees.bodylab_id == bodylabs.id
    ).where(
        Criterion.all([
            bodylabs.user_id == user_id
        ])
    ).get_sql()
    cursor.execute(sql)
    records = cursor.fetchall()

    if query_result_is_none(records) is True:
        connection.rollback()
        connection.close()
        result = {
            'result': False,
            'error': f'No bodylab data for user(id: {user_id})'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=sql,
                                 method=request.method)
        return json.dumps(result, ensure_ascii=False), 200

    result_list = []
    for data in records:
        each_dict = {}
        for index, value in enumerate(data):
            if type(value) == datetime:
                each_dict[columns[index]] = value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                each_dict[columns[index]] = value
        result_list.append(each_dict)

    result_dict = {
        'result': True,
        'bodylab_data': result_list
    }
    return json.dumps(result_dict, ensure_ascii=False), 200


@api.route('/user/<user_id>/bodylab/<bodylab_id>', methods=['GET'])
def read_user_bodylab_single(user_id, bodylab_id):
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.read_user_bodylab_single', user_id=user_id, bodylab_id=bodylab_id)
    # token = request.headers['Authorization']

    """Define tables required to execute SQL."""
    bodylabs = Table('bodylabs')
    bodylab_analyze_bodies = Table('bodylab_analyze_bodies')  # bodylb_body_images = Table('bodylab_body_images')
    # bodylab_analyze_atflees = Table('bodylab_analyze_atflees')

    try:
        connection = login_to_db()
    except Exception as e:
        error = str(e)
        result = {
            'result': False,
            'error': f'Server Error while connecting to DB: {error}'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], method=request.method)
        return json.dumps(result, ensure_ascii=False), 500
    cursor = connection.cursor()

    columns = ["bodylab_id",
               "created_at",
               "url_body_input",
               "height",
               "weight",
               "bmi",
               "bmi_status",
               "muscle_mass",
               "ideal_muscle_mass",
               "fat_mass",
               "ideal_fat_mass"
               "url_output",
               "shoulder_ratio",
               "hip_ratio",
               "shoulder_width",
               "hip_width",
               "nose_to_shoulder_center",
               "shoulder_center_to_hip_center",
               "hip_center_to_ankle_center",
               "whole_body_length",
               "upperbody_lowerbody"]

    sql = Query.from_(
        bodylabs
    ).select(
        bodylabs.id,
        bodylabs.created_at,
        bodylabs.url_body_image,
        bodylabs.height,
        bodylabs.weight,
        bodylabs.bmi,
        bodylabs.bmi_status,
        bodylabs.muscle_mass,
        bodylabs.ideal_muscle_mass,
        bodylabs.fat_mass,
        bodylabs.ideal_fat_mass,
        bodylab_analyze_bodies.url_output,
        bodylab_analyze_bodies.shoulder_ratio,
        bodylab_analyze_bodies.hip_ratio,
        bodylab_analyze_bodies.shoulder_width,
        bodylab_analyze_bodies.hip_width,
        bodylab_analyze_bodies.nose_to_shoulder_center,
        bodylab_analyze_bodies.shoulder_center_to_hip_center,
        bodylab_analyze_bodies.hip_center_to_ankle_center,
        bodylab_analyze_bodies.whole_body_length,
        bodylab_analyze_bodies.upperbody_lowerbody
    ).join(
        bodylab_analyze_bodies
    ).on(
        bodylab_analyze_bodies.bodylab_id == bodylabs.id
        # ).join(
        #     bodylab_analyze_atflees
        # ).on(
        #     bodylab_analyze_atflees.bodylab_id == bodylabs.id
    ).where(
        Criterion.all([
            bodylabs.user_id == user_id,
            bodylabs.id == bodylab_id
        ])
    ).get_sql()

    cursor.execute(sql)
    record = cursor.fetchall()

    if query_result_is_none(record) is True:
        connection.rollback()
        connection.close()
        result = {
            'result': False,
            'error': f'No data for bodylab_id({bodylab_id})'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=sql,
                                 method=request.method)
        return json.dumps(result, ensure_ascii=False), 200

    connection.close()
    result_dict = {'result': True}
    for index, value in enumerate(record[0]):
        if type(value) == datetime:
            result_dict[columns[index]] = value.strftime('%Y-%m-%d %H:%M:%S')
        else:
            result_dict[columns[index]] = value

    return json.dumps(result_dict, ensure_ascii=False), 200


    # region body lab score calculating
    '''
    * 바디랩: 총점, 순위 ==> 월요일 기준 갱신! 이지만 일요일에 운동하는 사람이 있을 수 있으니 월요일 정오 기준으로 계산한다.
      (1) 바디점수(바디랩 총점): 신체점수 & 매력점수 평균(정수), (전체 동성 유저의 신체 + 매력 점수 합산 결과에 대한)순위
      (2) 신체점수: 총점, (전체 동성 유저 중)순위
          - BMI, 체지방, 근육량 가중평균
      (3) 매력점수: 총점, (전체 동성 유저 중)순위
          - BMI, 체지방, 근육량, 사진분석값 가중평균  ==> 사진분석값을 활용한 눈바디 점수 계산식 확인 요망
      (4) BMI:
          - 수치에 따른 상단 한줄 코멘트
          - 나의 수치 & 권장수치/이성 선호/동성 선호 각각과의 차이(절대량)
          - 권장수치
          - 신체점수
          - 이성 선호(이성이 좋아하는 나와의 동성 1등의 금주 BMI), 동성 선호(동성이 좋아하는 나와의 동성 1등의 금주 BMI),
          - 매력점수
          - 최근 1주일의 날짜 & 일자별 내 점수
      (5) 체지방
          - 수치에 따른 상단 한줄 코멘트
          - 나의 수치 & 권장수치/이성 선호/동성 선호 각각과의 차이(절대량)
          - 권장수치
          - 신체점수
          - 이성 선호(이성이 좋아하는 나와의 동성 1등의 금주 체지방), 동성 선호(동성이 좋아하는 나와의 동성 1등의 금주 체지방)
          - 매력점수
          - 최근 1주일의 날짜 & 일자별 내 점수
      (6) 근육량:
          - 수치에 따른 상단 한줄 코멘트
          - 나의 수치 & 권장수치/이성 선호/동성 선호 각각과의 차이(절대량)
          - 권장수치
          - 신체점수
          - 이성 선호(이성이 좋아하는 나와의 동성 1등의 금주 근육량), 동성 선호(동성이 좋아하는 나와의 동성 1등의 금주 근육량)
          - 매력점수
          - 최근 1주일의 날짜 & 일자별 내 점수
      (7) 사진분석값: 우선은 점수만 그대로 보내주는 것으로.
      ##########################################################
      - 입력값: period(default: 금주), 유저 id
      - 반환값 예시
      {
        'WEEKLY_RECORD': {
          'total_body_score': '',
          'total_attractiveness_score': '',
          'total_bodylab_score': '',
          'weekly_body_rank': '',
          'weekly_attractiveness_rank': '',
          'weekly_bodylab_rank': ''
        }
        'BMI': {
          'comment': '',
          'amount_recommended': '',
          'amount_mine': '',
          'gap_with_recommended_amount': '',
          'body_score': '',
          'amount_of_person_most_preferred_by_same_sex': '',
          'amount_of_person_most_preferred_by_other_sex': '',
          'gap_with_person_most_preferred_by_same_sex': '',
          'gap_with_person_most_preferred_by_other_sex': '',
          'attractiveness_score': '',
          'history_4weeks': {'2022-01-01': '', '2022-01-02': '', ...}     #입력받은 period 포함한 최근 4주치의 my_amount
        },
        'MUSCLE': {},
        'FAT': {},
        'picture_analysis': {}
      }
      ##########################################################
    '''

# @api.route('/bodylab/<user_id>/<week>', methods=['GET'])    #check_token 추가하기!!!!!
# def read_weekly_score(user_id, period):
#   endpoint = API_ROOT + url_for('api.read_weekly_score', user_id=user_id, period=period)
#   ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
#   ip = request.headers["X-Forwarded-For"]  # Both public & private.
#   token = request.headers['Authorization']
#   user_id = request.args.get(user_id)
#   period = request.args.get(period)
#
#   try:
#     connection = login_to_db()
#   except Exception as e:
#     error = str(e)
#     result = {
#       'result': False,
#       'error': f'Server Error while connecting to DB:{error}'
#     }
#     slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], method=request.method)
#     return json.dumps(result, ensure_ascii=False), 500
#
#   cursor = connection.cursor()
#
# # Verify user is valid or not.
# is_valid_user = check_token(cursor, user_id, token)
# if is_valid_user['result'] is False:
#   connection.close()
#   result = {
#     'result': False,
#     'error': f"Invalid request: Unauthorized token or no such user({user_id})"
#   }
#   slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], method=request.method)
#   return json.dumps(result, ensure_ascii=False), 401
# elif is_valid_user['result'] is True:
#   pass

#   query = f'''
#     SELECT * FROM bodylab
#             (user_id,
#             height,
#             weight,
#             bmi,
#             muscle_mass,
#             fat_mass)
#       WHERE
#             user_id = {user_id}
#         AND
#             created_at = {period}'''
#   try:
#     cursor.execute(query)
#   except Exception as e:
#     connection.close()
#     error = str(e)
#     result = {
#       'result': False,
#       'error': f'Server Error while executing SELECT query: {error}'
#     }
#     slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query, , method=request.method)
#     return json.dumps(result), 500
#
#   return ''
#
# def calculate_body_score(score_type: str, my_bmi: float, my_fat: float, my_muscle: float):
#   # 신체 점수
#   """
#   반환값 정의
#   :
#   :param score_type:
#   :param my_bmi:
#   :param my_fat:
#   :param my_muscle:
#   :return:
#   """
#
#   if score_type == 'bmi':
#     pass
#   elif score_type == 'fat':
#     pass
#   elif score_type == 'muscle':
#     pass
#
# def get_comment():
#   # 수치에 따른 상단 한줄 코멘트
#   return ''
#
# def get_my_amount():
#   # 나의 BMI, 체지방, 근육량 DB에서 조회하기
#   return ''
#
# def get_preferred_amount():
#   return ''
#
# def calculate_gap():
#   # 권장 수치와 내 수치의 차이
#
#   # 이성 선호, 동성 선호와 내 수치의 차이
#   return ''
#
# def get_recommended_amount(target: str = '', height: float = 0.0, age: int = 0, weight: float = 0.0, sex: str = ''):
#   # 권장 수치
#   if target == 'bmi':
#     recommended_bmi = '18.5 ~ 22.9'
#   elif target == 'fat':
#     if sex == 'male':
#       if age < 18:
#         percent = 9.4
#       elif age < 21:
#         percent = 10.5
#       elif age < 26:
#         percent = 11.6
#       elif age < 31:
#         percent = (12.7 + 14.6) / 2
#       elif age < 36:
#         percent = (13.7 + 15.7) / 2
#       elif age < 41:
#         percent = 16.8
#       elif age < 46:
#         percent = 17.8
#       elif age < 51:
#         percent = (18.9 + 20.7) / 2
#       elif age < 56:
#         percent = (20.0 + 21.8) / 2
#       else:
#         percent = 22.8
#     else:
#       if age < 18:
#         percent = 19.7
#       elif age < 21:
#         percent = (19.7 + 21.5) / 2
#       elif age < 26:
#         percent = 22.1
#       elif age < 31:
#         percent = 22.7
#       elif age < 36:
#         percent = (23.4 + 25.1) / 2
#       elif age < 41:
#         percent = (24.0 + 25.7) / 2
#       elif age < 46:
#         percent = (24.6 + 26.3) / 2
#       elif age < 51:
#         percent = 26.9
#       elif age < 56:
#         percent = 27.6
#       else:
#         percent = (28.2 + 29.8) / 2
#     recommended_fat_mass = (weight * percent) / 100
#   elif target == 'muscle':
#     if sex == 'male':
#       recommended_muscle_mass = weight * 0.4
#     else:
#       recommended_muscle_mass = weight * 0.34
#
#   return recommended_bmi, recommended_fat_mass, recommended_muscle_mass
#
# def calculate_attractiveness_score(score_type: str):
#   if score_type == 'bmi':
#     pass
#   elif score_type == 'fat':
#     pass
#   elif score_type == 'muscle':
#     pass
#
# def history_data():
#   # 최근 1주일의 날짜 & 일자별 내 점수
#   return ''
#
# def get_image_analysis(user_id: int):
#   # (7) 사진 분석값
#   return ''
#
# def calculate_total_attractiveness_score():
#   # (3) 매력 점수: 총점, (전체 동성 유저 중)순위
#   # total_score
#   # ranking
#   return ''
#
# def calculate_total_body_score():
#   # (2) 신체 점수: 총점, (전체 동성 유저 중)순위
#   return ''
# endregion