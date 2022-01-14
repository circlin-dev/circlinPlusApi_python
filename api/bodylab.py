from global_things.functions import slack_error_notification, analyze_image, login_to_db
from global_things.constants import ATTRACTIVENESS_SCORE_CRITERIA
from . import api
from flask import request
import json

@api.route('/bodylab/add', methods=['POST'])
def add_weekly_data():
  ip = request.remote_addr
  endpoint = '/api/bodylab/add'
  user_id = request.form.get('user_id')
  height = request.form.get('height')
  weight = request.form.get('weight')
  bmi = request.form.get('bmi')
  muscle_mass = request.form.get('muscle_mass')
  fat_mass = request.form.get('fat_mass')
  body_image = request.form.get('body_image')

  if request.method == 'POST':
    if not(user_id and height and weight and bmi and muscle_mass and fat_mass and body_image):
      result = {
        'result': False,
        'error': f'Missing data in request.',
        'values': [user_id, height, weight, bmi, muscle_mass, fat_mass, body_image]
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
    query = f'''
                INSERT INTO bodylab(
                    user_id, 
                    height, 
                    weight, 
                    bmi, 
                    muscle_mass, 
                    fat_mass)
                VALUES (
                    {user_id},
                    {height},
                    {weight},
                    {bmi},
                    {muscle_mass},
                    {fat_mass})'''
    try:
      cursor.execute(query)
      connection.commit()
    except Exception as e:
      connection.close()
      error = str(e)
      result = {
        'result': False,
        'error': f'Server Error while executing INSERT query(bodylab): {error}'
      }
      slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
      return json.dumps(result, ensure_ascii=False), 500

    # Get users latest bodylab data = User's data inserted just before.
    query = f'''
      SELECT 
            id
        FROM
            bodylab
        WHERE
            user_id={user_id}
        ORDER BY id DESC
            LIMIT 1'''
    try:
      cursor.execute(query)
      latest_bodylab_id = cursor.fetchall()[0][0]
    except Exception as e:
      connection.close()
      error = str(e)
      result = {
        'result': False,
        'error': f'Server error while searching latest bodylab data from database(bodylab): {error}'
      }
      slack_error_notification(user_ip=ip, user_id=user_id, api=api, error_log=result['error'], query=query)
      return json.dumps(result, ensure_ascii=False), 500

    if len(latest_bodylab_id) == 0 or latest_bodylab_id == '' or latest_bodylab_id is None:
      result = {
        'result': False,
        'error': f'Cannot find requested bodylab data of user(bodylab): {user_id}'
      }
      slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
      return json.dumps(result, ensure_ascii=False), 400

    # Analyze user's image and store the result.
    image_analysis_result = analyze_image(user_id, body_image)
    image_analysis_result_json = json.loads(image_analysis_result)
    status_code = image_analysis_result_json['status_code']
    if status_code == 200:
      analyze_result = image_analysis_result_json['result']
      query = f" \
        INSERT INTO bodylab_image \
                (bodylab_id, original_url, \
                analyzed_url, shoulder_ratio, \
                hip_ratio, shoulder_width, \
                hip_width, nose_to_shoulder_center, \
                shoulder_center_to_hip_center, hip_center_to_ankle_center, \
                whole_body_length, upperbody_lowerbody) \
        VALUES (%s, %s, \
                %s, %s, \
                %s, %s, \
                %s, %s, \
                %s, %s, \
                %s, %s)"
      values = (latest_bodylab_id, body_image,
                analyze_result['output_url'], analyze_result['shoulder_ratio'],
                analyze_result['hip_ratio'], analyze_result['shoulder_width'],
                analyze_result['hip_width'], analyze_result['nose_to_shoulder_center'],
                analyze_result['shoulder_center_to_hip_center'], analyze_result['hip_center_to_ankle_center'],
                analyze_result['whole_body_length'], analyze_result['upper_body_lower_body'])
      try:
        cursor.execute(query, values)
        connection.commit()
      except Exception as e:
        connection.close()
        error = str(e)
        result = {
          'result': False,
          'error': f'Server error while executing INSERT query(bodylab_image): {error}'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
        return json.dumps(result, ensure_ascii=False), 400

      connection.close()
      result = {'result': True}
      return json.dumps(result, ensure_ascii=False), 201
    elif status_code == 400:
      connection.close()
      result = {
        'result': False,
        'error': f"Failed to analysis requested image({body_image}): {image_analysis_result_json['error']}"
      }
      slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
      return json.dumps(result, ensure_ascii=False), 400
    elif status_code == 500:
      connection.close()
      result = {
        'result': False,
        'error': f"Failed to analysis requested image({body_image}): {image_analysis_result_json['error']}"
      }
      slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
      return json.dumps(result, ensure_ascii=False), 500

  else:
    result = {
      'result': False,
      'error': 'Method Not Allowed'
    }
    slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
    return json.dumps(result, ensure_ascii=False), 403


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