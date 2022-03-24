import datetime
from global_things.constants import API_ROOT, AMAZON_URL, ATTRACTIVENESS_SCORE_CRITERIA, BODY_IMAGE_ANALYSIS_CRITERIA, \
    LOCAL_SAVE_PATH_ATFLEE_INPUT, BUCKET_IMAGE_PATH_ATFLEE_INPUT, BUCKET_NAME
from global_things.functions.slack import slack_error_notification
from global_things.functions.general import login_to_db, check_user_token, query_result_is_none
from global_things.error_handler import HandleException
from global_things.functions.bodylab import analyze_body_images, generate_resized_image, get_image_information, validate_and_save_to_s3, upload_image_to_s3, standard_healthiness_value, healthiness_score, attractiveness_score, return_dict_when_nothing_to_return, ocr_atflee_images
from . import api
import cv2
from datetime import datetime
from flask import url_for, request
import json
import os
from pypika import MySQLQuery as Query, Criterion, Table, Order, functions as fn
import shutil
from werkzeug.utils import secure_filename
"""2개의 이미지 전송
    -> 앳플리는 서버 저장 -> S3 저장 -> OCR
    -> 바디랩은 서버 저장 -> S3 저장 -> 바디랩 서버에 분석 -> 바디랩 서버에 키포인트 이미지 저장 -> S3 저장
    => OCR 데이터, 키포인트 수치 데이터 프론트에 반환 => 이상없는지 확인 후 수정된 내용을 DB 저장
    """


@api.route('/bodylab', methods=['POST'])
def post_bodylab():
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.post_bodylab')
    user_token = request.headers.get('Authorization')

    data = request.form.to_dict()  # {'body': ~~~~~.png, 'atflee': ~~~~~.png}
    try:
        body_image = request.files.to_dict()['body_image']
    except Exception as e:
        result = {
            'result': False,
            'error': f'Missing data: {str(e)}'
        }
        return json.dumps(result, ensure_ascii=False), 400

    # Verify if mandatory information is not null.
    if not body_image:
        result = {
            'result': False,
            'error': 'Null is not allowed.'
        }
        return json.dumps(result, ensure_ascii=False), 400

    connection = login_to_db()
    cursor = connection.cursor()
    verify_user = check_user_token(cursor, user_token)
    if verify_user['result'] is False:
        connection.close()
        message = 'No token at request header.' if user_token is None else 'Unauthorized user.'
        result = {
            'result': False,
            'error': message
        }
        return json.dumps(result, ensure_ascii=False), 401
    user_id = verify_user['user_id']
    user_nickname = verify_user['user_nickname']

    if request.method == 'POST':
        """
        이미지 서버 임시 저장 & 업로드 코드 추가 필요
          - 눈바디 이미지, 앳플리 이미지 S3 업로드 후 URL 가져오는 코드 추가해야 함!
        """
        bodylabs = Table('bodylabs')
        bodylab_analyze_bodies = Table('bodylab_analyze_bodies')
        user_questions = Table('user_questions')
        files = Table('files')

        now = datetime.now().strftime('%Y%m%d%H%M%S')
        # S3 업로드 - 바디랩 이미지: 신체 사진(눈바디)
        body_analysis = validate_and_save_to_s3('body', body_image, user_id, now)
        if body_analysis['result'] is False:
            result = {
                'result': False,
                'error': body_analysis['error']
            }
            return json.dumps(result, ensure_ascii=False), 400
        body_input_image_dict = body_analysis['input_image_dict']
        resized_body_images_list = body_analysis['resized_images_list']

        try:
            sql = f"""
                SELECT 
                    id 
                FROM 
                    user_weeks 
                WHERE 
                    user_id={user_id} 
                AND 
                    start_date=(SELECT ADDDATE(CURDATE(), - WEEKDAY(CURDATE())))"""
            cursor.execute(sql)
            user_week_id = cursor.fetchall()[0][0]
        except Exception as e:
            raise HandleException(user_ip=ip,
                                  nickname=user_nickname,
                                  user_id=user_id,
                                  api=endpoint,
                                  error_message=str(e),
                                  method=request.method,
                                  query=sql,
                                  status_code=500,
                                  payload=None,
                                  result=False)
        try:
            sql = f"""
                SELECT 
                    id 
                FROM 
                    bodylabs 
                WHERE 
                    user_id={user_id} 
                ORDER BY id DESC LIMIT 1"""
            cursor.execute(sql)
            latest_bodylab_id = cursor.fetchall()[0][0]
        except Exception as e:
            raise HandleException(user_ip=ip,
                                  nickname=user_nickname,
                                  user_id=user_id,
                                  api=endpoint,
                                  error_message=str(e),
                                  method=request.method,
                                  query=sql,
                                  status_code=500,
                                  payload=None,
                                  result=False)

        # DB 저장 1 - files에 바디랩 body input 원본 데이터 저장
        try:
            sql = Query.into(
                files
            ).columns(
                files.created_at,
                files.updated_at,
                files.pathname,
                files.original_name,
                files.mime_type,
                files.size,
                files.width,
                files.height
            ).insert(
                fn.Now(),
                fn.Now(),
                body_input_image_dict['pathname'],
                body_input_image_dict['original_name'],
                body_input_image_dict['mime_type'],
                body_input_image_dict['size'],
                body_input_image_dict['width'],
                body_input_image_dict['height']
            ).get_sql()
            cursor.execute(sql)
            connection.commit()
            file_id_body_input_image = cursor.lastrowid

            # DB 저장 1 - files에 바디랩 body input resized 데이터 저장
            for data in resized_body_images_list:
                sql = Query.into(
                    files
                ).columns(
                    files.created_at,
                    files.updated_at,
                    files.pathname,
                    files.original_name,
                    files.mime_type,
                    files.size,
                    files.width,
                    files.height,
                    files.original_file_id
                ).insert(
                    fn.Now(),
                    fn.Now(),
                    data['pathname'],
                    data['original_name'],
                    data['mime_type'],
                    data['size'],
                    data['width'],
                    data['height'],
                    int(file_id_body_input_image)
                ).get_sql()
                cursor.execute(sql)
            connection.commit()

            # sql = Query.into(
            #     bodylabs
            # ).columns(
            #     bodylabs.file_id_body_input
            # ).insert(
            #     int(file_id_body_input_image)
            # ).where(
            #     bodylabs.id == latest_bodylab_id
            # ).get_sql()
            # cursor.execute(sql)
            # connection.commit()

            # Analyze user's image and store the result.
            body_analysis = json.loads(analyze_body_images(user_id, body_input_image_dict['pathname']))
            result_code = body_analysis['status_code']
            if result_code == 200:
                try:
                    analyze_result = body_analysis['result']
                    body_output_image_dict = analyze_result['body_output_image_dict']
                    resized_body_output_image_list = analyze_result['resized_body_output_image_list']

                    sql = Query.into(
                        files
                    ).columns(
                        files.created_at,
                        files.updated_at,
                        files.pathname,
                        files.original_name,
                        files.mime_type,
                        files.size,
                        files.width,
                        files.height
                    ).insert(
                        fn.Now(),
                        fn.Now(),
                        body_output_image_dict['pathname'],
                        body_output_image_dict['original_name'],
                        body_output_image_dict['mime_type'],
                        body_output_image_dict['size'],
                        body_output_image_dict['width'],
                        body_output_image_dict['height']
                    ).get_sql()
                    cursor.execute(sql)
                    connection.commit()
                    file_id_body_output_image = cursor.lastrowid
                except Exception as e:
                    connection.close()
                    raise HandleException(user_ip=ip,
                                          nickname=user_nickname,
                                          user_id=user_id,
                                          api=endpoint,
                                          error_message=str(e),
                                          query=sql,
                                          method=request.method,
                                          status_code=500,
                                          payload=json.dumps(data, ensure_ascii=False),
                                          result=False)

                # DB 저장 1 - files에 바디랩 body input resized 데이터 저장
                try:
                    for data in resized_body_output_image_list:
                        sql = Query.into(
                            files
                        ).columns(
                            files.created_at,
                            files.updated_at,
                            files.pathname,
                            files.original_name,
                            files.mime_type,
                            files.size,
                            files.width,
                            files.height,
                            files.original_file_id
                        ).insert(
                            fn.Now(),
                            fn.Now(),
                            data['pathname'],
                            data['original_name'],
                            data['mime_type'],
                            data['size'],
                            data['width'],
                            data['height'],
                            int(file_id_body_output_image)
                        ).get_sql()
                        cursor.execute(sql)
                        connection.commit()
                except Exception as e:
                    connection.close()
                    raise HandleException(user_ip=ip,
                                          nickname=user_nickname,
                                          user_id=user_id,
                                          api=endpoint,
                                          error_message=str(e),
                                          query=sql,
                                          method=request.method,
                                          status_code=500,
                                          payload=json.dumps(data, ensure_ascii=False),
                                          result=False)
                try:
                    sql = Query.update(
                        bodylabs
                    ).set(
                        bodylabs.shoulder_width, analyze_result['shoulder_width']
                    ).set(
                        bodylabs.shoulder_ratio, analyze_result['shoulder_ratio']
                    ).set(
                        bodylabs.hip_width, analyze_result['hip_width']
                    ).set(
                        bodylabs.hip_ratio, analyze_result['hip_ratio']
                    ).set(
                        bodylabs.nose_to_shoulder_center, analyze_result['nose_to_shoulder_center']
                    ).set(
                        bodylabs.shoulder_center_to_hip_center, analyze_result['shoulder_center_to_hip_center']
                    ).set(
                        bodylabs.hip_center_to_ankle_center, analyze_result['hip_center_to_ankle_center']
                    ).set(
                        bodylabs.shoulder_center_to_ankle_center, analyze_result['shoulder_center_to_ankle_center']
                    ).set(
                        bodylabs.whole_body_length, analyze_result['whole_body_length']
                    ).where(
                        Criterion.all([
                            bodylabs.user_id == user_id,
                            bodylabs.user_week_id == user_week_id
                        ])
                    ).get_sql()
                    cursor.execute(sql)
                    connection.commit()
                except Exception as e:
                    connection.close()
                    raise HandleException(user_ip=ip,
                                          nickname=user_nickname,
                                          user_id=user_id,
                                          api=endpoint,
                                          error_message=str(e),
                                          query=sql,
                                          method=request.method,
                                          status_code=500,
                                          payload=data,
                                          result=False)

                try:
                    sql = Query.into(
                        bodylab_analyze_bodies
                    ).columns(
                        bodylab_analyze_bodies.bodylab_id,
                        bodylab_analyze_bodies.file_id,
                        bodylab_analyze_bodies.type
                    ).insert(
                        (latest_bodylab_id, file_id_body_input_image, 'input'),
                        (latest_bodylab_id, file_id_body_output_image, 'output')
                    ).get_sql()

                    cursor.execute(sql)
                    connection.commit()
                except Exception as e:
                    connection.close()
                    raise HandleException(user_ip=ip,
                                          nickname=user_nickname,
                                          user_id=user_id,
                                          api=endpoint,
                                          error_message=str(e),
                                          query=sql,
                                          method=request.method,
                                          status_code=500,
                                          payload=data,
                                          result=False)

                connection.close()
                result = {'result': True}
                return json.dumps(result, ensure_ascii=False), 201
            elif result_code == 400:
                connection.close()
                result = {
                    'result': False,
                    'error': f"Failed to analysis requested image({user_id}, {body_input_image_dict['pathname']}): {body_analysis['error']}"
                }
                return json.dumps(result, ensure_ascii=False), 400
            elif result_code == 500:
                connection.close()
                raise HandleException(user_ip=ip,
                                      nickname=user_nickname,
                                      user_id=user_id,
                                      api=endpoint,
                                      error_message=f"Failed to analysis requested image({body_image}): {body_analysis['error']}",
                                      query=sql,
                                      method=request.method,
                                      status_code=500,
                                      payload=data,
                                      result=False)
            else:
                pass
        except Exception as e:
            connection.close()
            raise HandleException(user_ip=ip,
                                  nickname=user_nickname,
                                  user_id=user_id,
                                  api=endpoint,
                                  error_message=f"Failed to execute POST request: {str(e)}",
                                  query=sql,
                                  method=request.method,
                                  status_code=500,
                                  payload=data,
                                  result=False)
    else:
        result = {'result': False, 'error': 'Method Not Allowed.'}
        return json.dumps(result, ensure_ascii=False), 405


@api.route('/user/<user_id>/bodylab', methods=['GET'])
def get_user_bodylab(user_id):
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.get_user_bodylab', user_id=user_id)

    """Define tables required to execute SQL."""
    bodylabs = Table('bodylabs')
    bodylab_analyze_bodies = Table('bodylab_analyze_bodies')  # bodylab_body_images = Table('bodylab_body_images')
    user_questions = Table('user_questions')
    files = Table('files')

    connection = login_to_db()
    cursor = connection.cursor()

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
            'error': 'Failed to create 1 week free trial(Cannot find user or user_question data).'
        }
        return json.dumps(result, ensure_ascii=False), 400
    answer = json.loads(data[0][0].replace("\\", "\\\\"), strict=False)
    gender = answer['gender']

    columns = ["bodylab_id",
               "created_at",
               "body_input_url",
               "body_input_url_resized",
               "height",
               "weight",
               "bmi",
               "ideal_bmi",
               "bmi_status",
               "bmi_healthiness_score",
               "bmi_attractiveness_score",
               "muscle_mass",
               "ideal_muscle_mass",
               "muscle_mass_healthiness_score",
               "muscle_mass_attractiveness_score",
               "fat_mass",
               "ideal_fat_mass",
               "fat_mass_healthiness_score",
               "fat_mass_attractiveness_score",
               "body_output_url",
               "body_output_url_resized"
               "shoulder_width",
               "shoulder_ratio",
               "hip_width",
               "hip_ratio",
               "nose_to_shoulder_center",
               "shoulder_center_to_hip_center",
               "hip_center_to_ankle_center",
               "shoulder_center_to_ankle_center",
               "whole_body_length"]

    sql = f"""
        SELECT
            b.id,
            b.created_at,
            b.user_week_id,
            (SELECT 
                    f.pathname 
            FROM 
                    files f 
            INNER JOIN 
                    bodylabs 
            ON 
                f.id = bodylabs.file_id_body_input 
            WHERE bodylabs.id = b.id) AS body_input_url,
            (SELECT JSON_ARRAYAGG(JSON_OBJECT('width', ff.width, 'pathname', ff.pathname)) AS resized
            FROM
                 files ff
            INNER JOIN
                (SELECT
                       f.id,
                       f.pathname
                FROM
                     files f
                INNER JOIN
                     bodylabs
                ON
                    f.id = bodylabs.file_id_body_input
                WHERE
                      bodylabs.id = b.id) AS original
            ON
                original.id = ff.original_file_id) AS body_input_url_resized,
            b.height,
            b.weight,
            b.bmi,
            b.ideal_bmi,
            b.bmi_healthiness_score,
            b.bmi_attractiveness_score,
            b.bmi_status,
            b.muscle_mass,
            b.ideal_muscle_mass,
            b.muscle_mass_healthiness_score,
            b.muscle_mass_attractiveness_score,
            b.fat_mass,
            b.ideal_muscle_mass,
            b.muscle_mass_healthiness_score,
            b.muscle_mass_attractiveness_score,
            (SELECT 
                    f.pathname 
            FROM 
                files f 
            INNER JOIN 
                bodylab_analyze_bodies 
            ON 
                f.id = bodylab_analyze_bodies.file_id_body_output 
            WHERE 
                bodylab_analyze_bodies.id = bab.id) AS body_output_url,
            (SELECT
                   JSON_ARRAYAGG(JSON_OBJECT('width', ff.width, 'pathname', ff.pathname)) AS resized
            FROM
                 files ff
            INNER JOIN
                (SELECT 
                    f.id,
                    f.pathname 
                FROM 
                    files f 
                INNER JOIN 
                    bodylab_analyze_bodies 
                ON 
                    f.id = bodylab_analyze_bodies.file_id_body_output
                WHERE 
                    bodylab_analyze_bodies.id = bab.id) AS original
            ON
                original.id = ff.original_file_id) AS body_output_url_resized,
            bab.shoulder_width,
            bab.shoulder_ratio,
            bab.hip_width,
            bab.hip_ratio,
            bab.nose_to_shoulder_center,
            bab.shoulder_center_to_hip_center,
            bab.hip_center_to_ankle_center,
            bab.shoulder_center_to_ankle_center,
            bab.whole_body_length
        FROM
             bodylabs b
        INNER JOIN
            bodylab_analyze_bodies bab
        ON
            bab.bodylab_id = b.id
        WHERE
            b.user_id = {user_id}"""
    cursor.execute(sql)
    records = cursor.fetchall()
    connection.close()

    if query_result_is_none(records) is True:
        connection.close()
        result = {
            'result': False,
            'error': f'No bodylab data for user(id: {user_id})'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_message=result['error'], query=sql,
                                 method=request.method)
        return json.dumps(result, ensure_ascii=False), 400

    result_list = []
    for record in records:
        result_dict = {
            "id": record[0],
            "created_at": record[1].strftime('%Y-%m-%d %H:%M:%S'),
            "user_week_id": record[2],
            "bmi": {
                "user": record[7],
                "ideal": record[8],
                "healthiness_score": record[9],
                "attractiveness_score": record[10],
                "bmi_status": record[11]
            },
            "muscle": {
                "user": record[12],
                "ideal": record[13],
                "healthiness_score": record[14],
                "attractiveness_score": record[15]
            },
            "fat": {
                "user": record[16],
                "ideal": record[17],
                "healthiness_score": record[18],
                "attractiveness_score": record[19]
            },
            "body_image_analysis": {
                "body_input_url": record[3],
                "body_input_url_resized": json.loads(record[4]),
                "body_output_url": record[20],
                "body_output_url_resized": json.loads(record[21]),
                "user": {
                    "height": record[5],
                    "weight": record[6],
                    "shoulder_width": record[22],
                    "shoulder_ratio": record[23],
                    "hip_width": record[24],
                    "hip_ratio": record[25],
                    "nose_to_shoulder_center": record[26],
                    "shoulder_center_to_hip_center": record[27],
                    "hip_center_to_ankle_center": record[28],
                    "shoulder_center_to_ankle_center": record[29],
                    "whole_body_length": record[30]
                },
                "compare": BODY_IMAGE_ANALYSIS_CRITERIA[gender]
            }
        }
        # for index, value in enumerate(data):
        #     if type(value) == datetime:
        #         each_dict[columns[index]] = value.strftime('%Y-%m-%d %H:%M:%S')
        #     else:
        #         each_dict[columns[index]] = value
        # # 건강점수
        # each_dict['bmi_healthiness_score'] = healthiness_score(each_dict['ideal_bmi'], each_dict['bmi'])
        # each_dict['fat_mass_healthiness_score'] = healthiness_score(each_dict['ideal_fat_mass'], each_dict['fat_mass'])
        # each_dict['muscle_mass_healthiness_score'] = healthiness_score(each_dict['ideal_muscle_mass'], each_dict['muscle_mass'])
        # each_dict['body_image_compare'] = BODY_IMAGE_ANALYSIS_CRITERIA[gender]
        result_list.append(result_dict)

    result_dict = {
        'result': True,
        'bodylab_data': result_list
    }

    return json.dumps(result_dict, ensure_ascii=False), 200


@api.route('/user/<user_id>/bodylab/<start_date>', methods=['GET'])
def get_user_bodylab_single(user_id, start_date):
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.get_user_bodylab_single', user_id=user_id, start_date=start_date)

    """Define tables required to execute SQL."""
    bodylabs = Table('bodylabs')
    bodylab_analyze_bodies = Table('bodylab_analyze_bodies')  # bodylb_body_images = Table('bodylab_body_images')
    bodylab_analyze_atflees = Table('bodylab_analyze_atflees')
    user_questions = Table('user_questions')

    connection = login_to_db()
    cursor = connection.cursor()

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
        # return json.dumps(result, ensure_ascii=False), 400
        return json.dumps(return_dict_when_nothing_to_return(), ensure_ascii=False), 400
    answer = json.loads(data[0][0].replace("\\", "\\\\"), strict=False)
    gender = answer['gender']

    columns = ["bodylab_id",
               "created_at",
               "body_input_url",
               "body_input_url_resized",
               "height",
               "weight",
               "bmi",
               "ideal_bmi",
               "bmi_status",
               "bmi_healthiness_score",
               "bmi_attractiveness_score",
               "muscle_mass",
               "ideal_muscle_mass",
               "muscle_mass_healthiness_score",
               "muscle_mass_attractiveness_score",
               "fat_mass",
               "ideal_fat_mass",
               "fat_mass_healthiness_score",
               "fat_mass_attractiveness_score",
               "body_output_url",
               "body_output_url_resized"
               "shoulder_width",
               "shoulder_ratio",
               "hip_width",
               "hip_ratio",
               "nose_to_shoulder_center",
               "shoulder_center_to_hip_center",
               "hip_center_to_ankle_center",
               "shoulder_center_to_ankle_center",
               "whole_body_length"]
    sql = f"""
        SELECT
            b.id,
            b.created_at,
            b.user_week_id,
            (
                SELECT
                       f.pathname
                FROM
                        files f
                INNER JOIN
                        bodylab_analyze_bodies bab
                ON
                    f.id = bab.file_id
                WHERE
                    bab.bodylab_id = b.id
                AND
                    bab.type = 'input') AS body_input_url,
            (
                SELECT
                       JSON_ARRAYAGG(JSON_OBJECT('width', ff.width, 'pathname', ff.pathname)) AS resized
                FROM
                     files ff
                INNER JOIN
                         (SELECT
                               f.id,
                               f.pathname
                         FROM
                             files f
                         INNER JOIN
                                 bodylab_analyze_bodies bab
                        ON
                            f.id = bab.file_id
                        WHERE
                            bab.bodylab_id = b.id
                        AND
                            bab.type = 'input') AS original
                ON
                    original.id = ff.original_file_id
            ) AS body_input_url_resized,
            baa.height,
            baa.weight,
            baa.bmi,
            baa.ideal_bmi,
            baa.bmi_healthiness_score,
            baa.bmi_attractiveness_score,
            baa.bmi_status,
            baa.muscle_mass,
            baa.ideal_muscle_mass,
            baa.muscle_mass_healthiness_score,
            baa.muscle_mass_attractiveness_score,
            baa.fat_mass,
            baa.ideal_muscle_mass,
            baa.muscle_mass_healthiness_score,
            baa.muscle_mass_attractiveness_score,
            (
                SELECT
                       f.pathname
                FROM
                     files f
                INNER JOIN
                         bodylab_analyze_bodies
            ON
                f.id = bodylab_analyze_bodies.file_id
                WHERE
                      bodylab_analyze_bodies.bodylab_id = b.id
                AND bodylab_analyze_bodies.type = 'output'
            ) AS body_output_url,
            (
                SELECT
                       JSON_ARRAYAGG(JSON_OBJECT('width', ff.width, 'pathname', ff.pathname)) AS resized
                FROM
                     files ff
                INNER JOIN
                         (SELECT
                                 f.id,
                                 f.pathname
                         FROM
                              files f
                        INNER JOIN
                                  bodylab_analyze_bodies
                        ON
                            f.id = bodylab_analyze_bodies.file_id
                         WHERE
                               bodylab_analyze_bodies.bodylab_id = b.id
                           AND
                               bodylab_analyze_bodies.type = 'output'
                         ) AS original
                ON
                    original.id = ff.original_file_id
            ) AS body_output_url_resized,
            b.shoulder_width,
            b.shoulder_ratio,
            b.hip_width,
            b.hip_ratio,
            b.nose_to_shoulder_center,
            b.shoulder_center_to_hip_center,
            b.hip_center_to_ankle_center,
            b.shoulder_center_to_ankle_center,
            b.whole_body_length
        FROM
             bodylabs b
        INNER JOIN
            bodylab_analyze_bodies bab
        ON
            bab.bodylab_id = b.id
        INNER JOIN
                 bodylab_analyze_atflees baa
        ON
            baa.bodylab_id = b.id
        WHERE
            b.user_id = {user_id}
        AND b.user_week_id = (SELECT
                                    uw.id
                                FROM
                                    user_weeks uw
                                WHERE
                                    uw.user_id=b.user_id
                                AND
                                    start_date = (SELECT ADDDATE(%s, - WEEKDAY(%s)))
                                ORDER BY uw.id DESC LIMIT 1)
        ORDER BY b.id DESC LIMIT 1"""
    values = (start_date, start_date)
    cursor.execute(sql, values)
    record = cursor.fetchall()

    if query_result_is_none(record) is True:
        connection.close()
        # result = {
        #     'result': False,
        #     'error': f'No data for start_date({start_date})'
        # }
        # return json.dumps(result, ensure_ascii=False), 200
        return json.dumps(return_dict_when_nothing_to_return(), ensure_ascii=False), 400

    connection.close()
    record = record[0]
    result_dict = {
        "result": True,
        "id": record[0],
        "created_at": record[1].strftime('%Y-%m-%d %H:%M:%S'),
        "user_week_id": record[2],
        "bmi": {
            "user": record[7],
            "ideal": record[8],
            "healthiness_score": record[9],
            "attractiveness_score": record[10],
            "bmi_status": record[11]
        },
        "muscle": {
            "user": record[12],
            "ideal": record[13],
            "healthiness_score": record[14],
            "attractiveness_score": record[15]
        },
        "fat": {
            "user": record[16],
            "ideal": record[17],
            "healthiness_score": record[18],
            "attractiveness_score": record[19]
        },
        "body_image_analysis": {
            "body_input_url": record[3],
            "body_input_url_resized": json.loads(record[4]),
            "body_output_url": record[20],
            "body_output_url_resized": json.loads(record[21]),
            "user": {
                "height": record[5],
                "weight": record[6],
                "shoulder_width": record[22],
                "shoulder_ratio": record[23],
                "hip_width": record[24],
                "hip_ratio": record[25],
                "nose_to_shoulder_center": record[26],
                "shoulder_center_to_hip_center": record[27],
                "hip_center_to_ankle_center": record[28],
                "shoulder_center_to_ankle_center": record[29],
                "whole_body_length": record[30]
            },
            "compare": BODY_IMAGE_ANALYSIS_CRITERIA[gender]
        }
    }

    return json.dumps(result_dict, ensure_ascii=False), 200


@api.route('/atflee-ocr', methods=['POST'])
def post_atflee_ocr():
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.post_atflee_ocr')
    user_token = request.headers.get('Authorization')

    connection = login_to_db()
    cursor = connection.cursor()
    verify_user = check_user_token(cursor, user_token)
    atflee_image = request.files.to_dict()['atflee_image']

    if verify_user['result'] is False:
        connection.close()
        message = 'No token at request header.' if user_token is None else 'Unauthorized user.'
        result = {
            'result': False,
            'error': message
        }
        return json.dumps(result, ensure_ascii=False), 401
    user_id = verify_user['user_id']
    user_nickname = verify_user['user_nickname']

    secure_file = secure_filename(atflee_image.filename)
    atflee_image.save(secure_file)

    # 앳플리 이미지 복사본 생성: secure_file을 두 번 할 시 validate_and_save_to_s3()과 OCR 사이에서 파일 이동이 제대로 되지 않는 현상이 있음...
    copy_secure_file = f'/home/ubuntu/circlinMembersApi_python/circlinMembersApi_flask/copy_{atflee_image.filename}'
    shutil.copy2(secure_file, copy_secure_file)

    # S3 업로드 - 바디랩 이미지 1: 신체 사진(눈바디)
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    atflee_analysis = validate_and_save_to_s3('atflee', atflee_image, user_id, now)
    if atflee_analysis['result'] is False:
        result = {
            'result': False,
            'error': atflee_analysis['error']
        }
        return json.dumps(result, ensure_ascii=False), 400

    # OCR 분석 수행
    ocr_result = ocr_atflee_images(copy_secure_file)
    status_code = ocr_result['status_code']
    del ocr_result['status_code']
    if os.path.exists(copy_secure_file):
        os.remove(copy_secure_file)  # secure_file은 validate_and_save_to_s3() 함수에서 제거함.
    if ocr_result['result'] is False:
        connection.close()
        return json.dumps(ocr_result, ensure_ascii=False), status_code

    atflee_input_image_dict = atflee_analysis['input_image_dict']
    resized_atflee_images_list = atflee_analysis['resized_images_list']
    ocr_result['input_image_data'] = atflee_input_image_dict
    ocr_result['resized_image_data'] = resized_atflee_images_list

    return json.dumps(ocr_result, ensure_ascii=False), 200


@api.route('/atflee', methods=['POST'])
def post_atflee_image():
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.post_atflee_image')
    user_token = request.headers.get('Authorization')

    # data = request.form.to_dict()  # {'body': ~~~~~.png, 'atflee': ~~~~~.png}
    data = json.loads(request.get_data(), encoding='utf-8')
    try:
        user_weight = float(data['weight'])
        user_height = float(data['height'])
        bmi = float(data['bmi'])
        muscle_mass = float(data['muscle'])
        fat_mass = float(data['fat'])
        input_image_data = data['input_image_data']  # dictionary
        resized_image_data = data['resized_image_data']  # list
    except Exception as e:
        result = {
            'result': False,
            'error': f'Missing data: {str(e)}'
        }
        return json.dumps(result, ensure_ascii=False), 400

    # Verify if mandatory information is not null.
    if not (user_height and user_weight and bmi and muscle_mass and fat_mass and input_image_data and resized_image_data):
        result = {
            'result': False,
            'error': 'Null is not allowed.'
        }
        return json.dumps(result, ensure_ascii=False), 400

    connection = login_to_db()
    cursor = connection.cursor()
    verify_user = check_user_token(cursor, user_token)

    if verify_user['result'] is False:
        connection.close()
        message = 'No token at request header.' if user_token is None else 'Unauthorized user.'
        result = {
            'result': False,
            'error': message
        }
        return json.dumps(result, ensure_ascii=False), 401
    user_id = verify_user['user_id']
    user_nickname = verify_user['user_nickname']

    files = Table('files')
    user_questions = Table('user_questions')
    bodylabs = Table('bodylabs')
    bodylab_analyze_atflees = Table('bodylab_analyze_atflees')

    # user_week_id 없으면 생성하고, 이후 SELECT
    try:
        sql = f"""
            INSERT INTO
                    user_weeks(created_at, updated_at, user_id, start_date)
                SELECT (SELECT NOW()), (SELECT NOW()), {user_id}, (SELECT ADDDATE(CURDATE(), - WEEKDAY(CURDATE()))) FROM dual
            WHERE NOT EXISTS(
                        SELECT 
                            id 
                        FROM 
                            user_weeks 
                        WHERE 
                            user_id={user_id} 
                        AND 
                            start_date=(SELECT ADDDATE(CURDATE(), - WEEKDAY(CURDATE())))
            )"""
        cursor.execute(sql)
        connection.commit()

        sql = f"""
            SELECT 
                id 
            FROM 
                user_weeks 
            WHERE 
                user_id={user_id} 
            AND 
                start_date=(SELECT ADDDATE(CURDATE(), - WEEKDAY(CURDATE())))"""
        cursor.execute(sql)
        user_week_id = cursor.fetchall()[0][0]
    except Exception as e:
        raise HandleException(user_ip=ip,
                              nickname=user_nickname,
                              user_id=user_id,
                              api=endpoint,
                              error_message=str(e),
                              method=request.method,
                              query=sql,
                              status_code=500,
                              payload=None,
                              result=False)
    # DB 저장 1 - files에 바디랩 body input 원본 데이터 저장
    sql = Query.into(
        files
    ).columns(
        files.created_at,
        files.updated_at,
        files.pathname,
        files.original_name,
        files.mime_type,
        files.size,
        files.width,
        files.height
    ).insert(
        fn.Now(),
        fn.Now(),
        input_image_data['pathname'],
        input_image_data['original_name'],
        input_image_data['mime_type'],
        input_image_data['size'],
        input_image_data['width'],
        input_image_data['height']
    ).get_sql()
    cursor.execute(sql)
    connection.commit()
    file_id_atflee_input = cursor.lastrowid

    # DB 저장 1 - files에 바디랩 atflee input resized 데이터 저장
    for data in resized_image_data:
        sql = Query.into(
            files
        ).columns(
            files.created_at,
            files.updated_at,
            files.pathname,
            files.original_name,
            files.mime_type,
            files.size,
            files.width,
            files.height,
            files.original_file_id
        ).insert(
            fn.Now(),
            fn.Now(),
            data['pathname'],
            data['original_name'],
            data['mime_type'],
            data['size'],
            data['width'],
            data['height'],
            int(file_id_atflee_input)
        ).get_sql()
        cursor.execute(sql)
    connection.commit()

    # user_question 데이터 불러오기
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
            'error': 'Pre-survey answer is necessary.'
        }
        return json.dumps(result, ensure_ascii=False), 400
    answer = json.loads(data[0][0].replace("\\", "\\\\"), strict=False)
    gender = answer['gender']
    age_group = answer['age_group']

    if gender is not None and age_group is not None:
        ideal_fat_mass, ideal_muscle_mass, bmi_status, ideal_bmi = standard_healthiness_value(str(age_group), str(gender),
                                                                                              float(user_weight),
                                                                                              float(user_height),
                                                                                              float(bmi))
    else:
        connection.close()
        result = {
            'result': False,
            'error': 'Missing data in pre-survey answer: gender or age_group.'
        }
        return json.dumps(result, ensure_ascii=False), 400

    # 건강점수
    bmi_healthiness_score = healthiness_score(ideal_bmi, bmi)
    muscle_mass_healthiness_score = healthiness_score(ideal_muscle_mass, muscle_mass)
    fat_mass_healthiness_score = healthiness_score(ideal_fat_mass, fat_mass)

    # 매력점수
    bmi_attractiveness_score = attractiveness_score(ATTRACTIVENESS_SCORE_CRITERIA[gender]['bmi'], bmi)
    muscle_mass_attractiveness_score = attractiveness_score(ATTRACTIVENESS_SCORE_CRITERIA[gender]['muscle_mass'],
                                                            muscle_mass)
    fat_mass_attractiveness_score = attractiveness_score(ATTRACTIVENESS_SCORE_CRITERIA[gender]['fat_mass'], fat_mass)

     # Cannot add or update a child row: a foreign key constraint fails (`circlin_plus_test`.`bodylabs`, CONSTRAINT `bodylabs_FK_1` FOREIGN KEY (`file_id_body_input`) REFERENCES `files` (`id`))')
    sql = Query.into(
        bodylabs
    ).columns(
        bodylabs.user_id,
        bodylabs.user_week_id,
    ).insert(
        user_id,
        user_week_id
    ).get_sql()
    cursor.execute(sql)
    connection.commit()
    bodylab_id = cursor.lastrowid

    sql = Query.into(
        bodylab_analyze_atflees
    ).columns(
        bodylab_analyze_atflees.bodylab_id,
        bodylab_analyze_atflees.file_id,
        bodylab_analyze_atflees.height,
        bodylab_analyze_atflees.weight,
        bodylab_analyze_atflees.bmi,
        bodylab_analyze_atflees.bmi_status,
        bodylab_analyze_atflees.ideal_bmi,
        bodylab_analyze_atflees.bmi_healthiness_score,
        bodylab_analyze_atflees.bmi_attractiveness_score,
        bodylab_analyze_atflees.muscle_mass,
        bodylab_analyze_atflees.ideal_muscle_mass,
        bodylab_analyze_atflees.muscle_mass_healthiness_score,
        bodylab_analyze_atflees.muscle_mass_attractiveness_score,
        bodylab_analyze_atflees.fat_mass,
        bodylab_analyze_atflees.ideal_fat_mass,
        bodylab_analyze_atflees.fat_mass_healthiness_score,
        bodylab_analyze_atflees.fat_mass_attractiveness_score,
    ).insert(
        bodylab_id,
        file_id_atflee_input,
        user_height,
        user_weight,
        bmi,
        bmi_status,
        ideal_bmi,
        bmi_healthiness_score,
        bmi_attractiveness_score,
        muscle_mass,
        ideal_muscle_mass,
        muscle_mass_healthiness_score,
        muscle_mass_attractiveness_score,
        fat_mass,
        ideal_fat_mass,
        fat_mass_healthiness_score,
        fat_mass_attractiveness_score
    ).get_sql()
    cursor.execute(sql)
    connection.commit()

    connection.close()
    result = {'result': True}
    return json.dumps(result, ensure_ascii=False), 201
