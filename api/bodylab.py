from flask import request, jsonify
from . import api

@api.route('/bodylab/add', methods=['POST'])
def add_weekly_data():
  if request.method == 'POST':
    userid = request.form.get('userid') #request.args.get('userid')
    height = request.form.get('height')  # request.args.get('userid')
    weight = request.form.get('weight')  # request.args.get('userid')
    bmi = request.form.get('bmi')  # request.args.get('userid')
    muscle_mass = request.form.get('muscle_mass')  # request.args.get('userid')
    fat_mass = request.form.get('fat_mass')  # request.args.get('userid')
    bodyimage = request.files['bodyimage']  # request.args.get('userid')

  return jsonify(userid, height, weight, bmi, muscle_mass, fat_mass, bodyimage.filename)

@api.route('/bodylab/read', methods=['GET'])
def hello():
  return "hello bodylab!"


@api.route('/bodylab/weekly/<id>', methods=['GET'])
def read_weekly_score():
  return ''