from app import db
from global_things.functions import slack_error_notification, analyze_image
from models import BodylabModel, BodylabImageModel
from . import api
from flask import request, jsonify

@api.route('/bodylab/add', methods=['POST'])
def add_weekly_data():
  try:
    if request.method == 'POST':
      user_id = request.form.get('user_id')
      height = request.form.get('height')
      weight = request.form.get('weight')
      bmi = request.form.get('bmi')
      muscle_mass = request.form.get('muscle_mass')
      fat_mass = request.form.get('fat_mass')
      body_image = request.form.get('body_image')

      if not (user_id or height or weight or bmi or muscle_mass or fat_mass or body_image):
        return jsonify({'error': f'Missing data in request.'}), 400

      bodylab_data = BodylabModel()
      bodylab_data.user_id = user_id
      bodylab_data.height = height
      bodylab_data.weight = weight
      bodylab_data.bmi = bmi
      bodylab_data.muscle_mass = muscle_mass
      bodylab_data.fat_mass = fat_mass

      #Insert into database(bodylab)
      db.session.add(bodylab_data)
      db.session.commit()

      #Get users's latest bodylab data = User's data inserted just before.
      bodylab_id = db.session.query(bodylab_data).\
        filter(bodylab_data.user_id == user_id).\
        order_by(bodylab_data.created_at.desc())

      bodylab_image_analysis = BodylabImageModel()
      try:
        image_analysis_result = analyze_image(user_id, body_image)
        bodylab_image_analysis.bodylab_id = bodylab_id
        bodylab_image_analysis.original_url = body_image
        bodylab_image_analysis.analyzed_url = image_analysis_result.output_url
        bodylab_image_analysis.shoulder_ratio = image_analysis_result.shoulder_ratio
        bodylab_image_analysis.hip_ratio = image_analysis_result.hip_ratio
        bodylab_image_analysis.shoulder_width = image_analysis_result.shoulder_width
        bodylab_image_analysis.hip_width = image_analysis_result.hip_width
        bodylab_image_analysis.nose_to_shoulder_center = image_analysis_result.nose_to_shoulder_center
        bodylab_image_analysis.shoulder_center_to_hip_center = image_analysis_result.shoulder_center_to_hip_center
        bodylab_image_analysis.hip_center_to_ankle_center = image_analysis_result.hip_center_to_ankle_center
        bodylab_image_analysis.whole_body_length = image_analysis_result.whole_body_length
        bodylab_image_analysis.hip_width = image_analysis_result.upperbody_lowerbody

        # Insert into database(bodylab_image)
        db.session.add(bodylab_image_analysis)
        db.session.commit()
      except Exception as e:
        ip = request.remote_addr
        slack_error_notification(user_ip=ip, user_id=user_id, api='/api/bodylab/add', error_log=e)
        return jsonify({'error': 'Server Error.'}), 500

      return jsonify({'success': 'Successfully processed request.'}), 201

    else:
      return jsonify({'error': 'Method Not Allowed.'}), 403

  except Exception as e:
    ip = request.remote_addr
    slack_error_notification(user_ip=ip, user_id=user_id, api='/api/bodylab/add', error_log=e)
    return jsonify({'error': 'Server Error.'}), 500


@api.route('/bodylab/weekly/<user_id>', methods=['GET'])
def read_weekly_score():
  return ''