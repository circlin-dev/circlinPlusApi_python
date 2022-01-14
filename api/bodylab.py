from global_things.functions import slack_error_notification, analyze_image, get_date_range_from_week, login_to_db
from global_things.constants import ATTRACTIVENESS_SCORE_CRITERIA
from . import api
from flask import request
import json

@api.route('/bodylab/add', methods=['POST'])
def add_weekly_data():
  ip = request.remote_addr
  endpoint = '/api/bodylab/add'
  period = request.form.get('period')  # Value format: yyyy-Www(Week 01, 2017 ==> "2017-W01")
  user_id = request.form.get('user_id')
  height = request.form.get('height')
  weight = request.form.get('weight')
  bmi = request.form.get('bmi')
  muscle_mass = request.form.get('muscle_mass')
  fat_mass = request.form.get('fat_mass')
  body_image = request.form.get('body_image')

  if request.method == 'POST':
    if not(period and user_id and height and weight and bmi and muscle_mass and fat_mass and body_image):
      result = {
        'result': False,
        'error': f'Missing data in request.',
        'values': {
          'period': period,
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

    year = period.split('-W')[0]
    week_number_of_year = period.split('-W')[1]
    firstdate_of_week, lastdate_of_week = get_date_range_from_week(year, week_number_of_year)

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
    query = f"INSERT INTO bodylab( \
                          user_id, year, \
                          week_number_of_year, firstdate_of_week, \
                          lastdate_of_week, height,\
                          weight, bmi, \
                          muscle_mass, fat_mass) \
                  VALUES(%s, %s, \
                        %s, %s, \
                        %s, %s, \
                        %s, %s, \
                        %s, %s, \
                        %s, %s)"
    values = (user_id, int(year),
              int(week_number_of_year), firstdate_of_week,
              lastdate_of_week, height,
              weight, bmi,
              muscle_mass, fat_mass)
    try:
      cursor.execute(query, values)
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

    cursor.execute(query)
    latest_bodylab_id_tuple = cursor.fetchall()
    if len(latest_bodylab_id_tuple) == 0 or latest_bodylab_id_tuple == ():
      result = {
        'result': False,
        'error': f'Cannot find requested bodylab data of user(id: {user_id})(bodylab)'
      }
      slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
      return json.dumps(result, ensure_ascii=False), 400
    else:
      latest_bodylab_id = latest_bodylab_id_tuple[0][0]

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

# @api.route('/bodylab/weekly/<user_id>/<period>', methods=['GET'])
# def read_weekly_score(user_id, period):
#   endpoint = '/api/bodylab/weekly/<user_id>'
#   ip = request.remote_addr
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
#     slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=error)
#     return json.dumps(result, ensure_ascii=False), 500
#
#   cursor = connection.cursor()
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
#     slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=error, query=query)
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
