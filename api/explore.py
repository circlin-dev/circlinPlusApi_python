from global_things.constants import API_ROOT
from global_things.functions.slack import slack_error_notification
from global_things.functions.explore import explore_query, filtering_dataframe
from global_things.functions.general import login_to_db, check_token
from . import api
from collections import OrderedDict
from flask import url_for, request
import json
import pandas as pd


@api.route('/explore', methods=['POST'])
def explore():
  """
  header: Authorization
  body: filter{exercises, purposes, equipments}, sort_by, word,
  """
  # ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
  ip = request.headers["X-Forwarded-For"]  # Both public & private.
  endpoint = API_ROOT + url_for('api.explore')
  # token = request.headers['Authorization']
  parameters = json.loads(request.get_data(), encoding='utf-8')
  # 필터: {"filter": {"exercises": [], "purposes": [], "equipments": []}, "word": "", "sort_by": ""}
  filter_list_exercises = parameters['filter']['exercise']  # default: Everything
  filter_list_purposes = parameters['filter']['purposes']  # default: everything
  filter_list_equipments = parameters['filter']['equipments']
  sort_by = parameters["sort_by"]
  word_for_search = parameters["word"].strip()

  try:
    connection = login_to_db()
  except Exception as e:
    error = str(e)
    result = {
      'result': False,
      'error': f'Server Error while connecting to DB: {error}'
    }
    slack_error_notification(user_ip=ip, api=endpoint, error_log=result['error'])
    return json.dumps(result, ensure_ascii=False), 500

  cursor = connection.cursor()
  result_list = []
  if word_for_search != "" or len(word_for_search) >= 0 or word_for_search is not None:
    query_program, query_coach, query_exercise, query_equipment = explore_query(word_for_search, sort_by)

    cursor.execute(query_program)
    programs_by_program = pd.DataFrame(cursor.fetchall(), columns=['program_id', 'created_at', 'title',
                                                                   'exercise', 'equipments', 'purposes',
                                                                   'thumbnail', 'thumbnails', 'num_lectures'])
    program_list_by_program = filtering_dataframe(filter_list_exercises, filter_list_purposes, filter_list_equipments, programs_by_program)

    cursor.execute(query_coach)
    programs_by_coach = pd.DataFrame(cursor.fetchall(), columns=['program_id', 'created_at', 'title',
                                                                 'exercise', 'equipments', 'purposes',
                                                                 'thumbnail', 'thumbnails', 'num_lectures'])
    program_list_by_coach = filtering_dataframe(filter_list_exercises, filter_list_purposes, filter_list_equipments, programs_by_coach)

    cursor.execute(query_exercise)
    programs_by_exercise = pd.DataFrame(cursor.fetchall(), columns=['program_id', 'created_at', 'title',
                                                                    'exercise', 'equipments', 'purposes',
                                                                    'thumbnail', 'thumbnails', 'num_lectures'])
    program_list_by_exercise = filtering_dataframe(filter_list_exercises, filter_list_purposes, filter_list_equipments, programs_by_exercise)

    cursor.execute(query_equipment)
    programs_by_equipment = pd.DataFrame(cursor.fetchall(), columns=['program_id', 'created_at', 'title',
                                                                     'exercise', 'equipments', 'purposes',
                                                                     'thumbnail', 'thumbnails', 'num_lectures'])
    program_list_by_equipment = filtering_dataframe(filter_list_exercises, filter_list_purposes, filter_list_equipments, programs_by_equipment)

    search_total = program_list_by_program + program_list_by_coach + program_list_by_exercise + program_list_by_equipment
    for element in search_total:
      if element not in result_list:
        result_list.append(element)
  else:
    pass

  result_dict = {
    "result": True,
    "word": word_for_search,
    "search_results": result_list
  }

  return json.dumps(result_dict, ensure_ascii=False), 200
