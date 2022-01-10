from flask import request
from . import api

@api.route('/bodylab/add', methods=['POST'])
def add_weekly_data():
  if request.method == 'POST':
    userid = request.form.get('userid') #request.args.get('userid')
  return ''


@api.route('/bodylab/weekly/<id>', methods=['GET'])
def read_weekly_score():
  return ''