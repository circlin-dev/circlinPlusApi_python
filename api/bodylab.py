from global_things.functions import slack_error_notification, analyze_image, login_to_db
from . import api
from flask import request, jsonify

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
      return jsonify({'error': f'Missing data in request.', 'values': [user_id, height, weight, bmi, muscle_mass, fat_mass, body_image]}), 400

    try:
      connection = login_to_db()
    except Exception as e:
      slack_error_notification(user_ip=ip, user_id=user_id, api='/api/bodylab/add', error_log=e)
      return jsonify({'error': f'Server Error while connecting to DB: {e}'}), 500

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
      return jsonify({'error': f'Server Error while executing INSERT query: {e}'}), 500

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
    if image_analysis_result['status_code'] == 200:
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
                {image_analysis_result.output_url},
                {image_analysis_result.shoulder_ratio},
                {image_analysis_result.hip_ratio},
                {image_analysis_result.shoulder_width},
                {image_analysis_result.hip_width},
                {image_analysis_result.nose_to_shoulder_center},
                {image_analysis_result.shoulder_center_to_hip_center},
                {image_analysis_result.hip_center_to_ankle_center},
                {image_analysis_result.whole_body_length},
                {image_analysis_result.upperbody_lowerbody})
      '''
      cursor.execute(query)
      connection.commit()
      connection.close()
      return jsonify({'success': 'Successfully processed request.'}), 201
    elif image_analysis_result['status_code'] == 400:
      connection.close()
      return jsonify({'error': image_analysis_result['error']}), 400
    elif image_analysis_result['status_code'] == 500:
      connection.close()
      return jsonify({'error': image_analysis_result['error']}), 500

  else:
    return jsonify({'error': 'Method Not Allowed.'}), 403


@api.route('/bodylab/weekly/<user_id>', methods=['GET'])
def read_weekly_score():
  return ''