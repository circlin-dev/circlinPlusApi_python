from global_things.functions import slack_error_notification, analyze_image, login_to_db
from . import api
from flask import request
import json

@api.route('/bodylab/add', methods=['POST'])
def add_weekly_data():
  if request.method == 'POST':
    ip = request.remote_addr

    user_id = request.form.get('user_id')
    height = request.form.get('height')
    weight = request.form.get('weight')
    bmi = request.form.get('bmi')
    muscle_mass = request.form.get('muscle_mass')
    fat_mass = request.form.get('fat_mass')
    body_image = request.form.get('body_image')

    if not(user_id and height and weight and bmi and muscle_mass and fat_mass and body_image):
      return json.dumps({'error': f'Missing data in request.', 'values': [user_id, height, weight, bmi, muscle_mass, fat_mass, body_image]}, ensure_ascii=False), 400

    try:
      connection = login_to_db()
    except Exception as e:
      slack_error_notification(user_ip=ip, user_id=user_id, api='/api/bodylab/add', error_log=e)
      return json.dumps({'error': f'Server Error while connecting to DB: {e}'}, ensure_ascii=False), 500

    cursor = connection.cursor()
    query = f'''
      INSERT INTO bodylab
              (user_id, 
              height, 
              weight, 
              bmi, 
              muscle_mass, 
              fat_mass)
      VALUES ({user_id},
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
      slack_error_notification(user_ip=ip, user_id=user_id, api='/api/bodylab/add', error_log=e, query=query)
      return json.dumps({'error': f'Server Error while executing INSERT query: {e}'}, ensure_ascii=False), 500

    #Get users's latest bodylab data = User's data inserted just before.
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
    latest_bodylab_id = cursor.fetchall()

    #Analyze user's image.
    image_analysis_result = analyze_image(user_id, body_image)
    image_analysis_result = json.loads(image_analysis_result)
    status_code = image_analysis_result['status_code']
    if status_code == 200:
      analyze_result = image_analysis_result['result']
      query = f'''
        INSERT INTO bodylab_image
                (bodylab_id, 
                original_url, 
                analyzed_url, 
                shoulder_ratio, 
                hip_ratio, 
                shoulder_width,
                hip_width,
                nose_to_shoulder_center,
                shoulder_center_to_hip_center,
                hip_center_to_ankle_center,
                whole_body_length,
                upperbody_lowerbody)
        VALUES ({latest_bodylab_id},
                {body_image},
                {analyze_result["output_url"]},
                {analyze_result["shoulder_ratio"]},
                {analyze_result["hip_ratio"]},
                {analyze_result["shoulder_width"]},
                {analyze_result["hip_width"]},
                {analyze_result["nose_to_shoulder_center"]},
                {analyze_result["shoulder_center_to_hip_center"]},
                {analyze_result["hip_center_to_ankle_center"]},
                {analyze_result["whole_body_length"]},
                {analyze_result["upper_body_lower_body"]})'''
      cursor.execute(query)
      connection.commit()
      connection.close()
      return json.dumps({'success': 'Successfully processed request.'}, ensure_ascii=False), 201
    elif status_code == 400:
      connection.close()
      return json.dumps({'error': image_analysis_result['error']}, ensure_ascii=False), 400
    elif status_code == 500:
      connection.close()
      return json.dumps({'error': image_analysis_result['error']}, ensure_ascii=False), 500

  else:
    return json.dumps({'error': 'Method Not Allowed.'}, ensure_ascii=False), 403


@api.route('/bodylab/weekly/<user_id>', methods=['GET'])
def read_weekly_score():
  return ''