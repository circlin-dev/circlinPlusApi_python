from global_things.constants import API_ROOT
from global_things.functions.slack import slack_error_notification
from global_things.functions.explore import explore_query
from global_things.functions.general import login_to_db, check_token, query_result_is_none
from . import api
import datetime
from flask import url_for, request
import json
import pandas as pd
import pymysql
import requests


@api.route('/explore', methods=['POST'])
def explore():
  """
  :param search_filter: 필터명(잠정: program, exercise, coach, equipment, purpose)
  :param word: 검색어
  :return: {"id": 0,
            "title": "",
            "thumbnail": "",
            "thumbnails": [{pathname: "320w.png"}, {pathname: "240w.png",}],
            "num_lectures": 0}
  """
  # ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
  ip = request.headers["X-Forwarded-For"]  # Both public & private.
  endpoint = API_ROOT + url_for('api.explore')
  # token = request.headers['Authorization']
  parameters = json.loads(request.get_data(), encoding='utf-8')
  # {"filter": {"exercises": [], "purposes": [], "equipments": []}, "word": "", "sort_by": ""}
  filter_list_exercises = parameters['filter']['exercises'] #default: Everything
  filter_list_purposes = parameters['filter']['purposes'] #default: everything
  filter_list_equipments = parameters['filter']['equipments']
  sort_by = parameters["sort_by"]
  word_for_search = parameters["word"]

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

  query = explore_query(word_for_search, sort_by)
  cursor.execute(query)

  programs_df = pd.DataFrame(cursor.fetchall(), columns=['program_id', 'created_at', 'title',
                                                         'exercise', 'equipments', 'purposes',
                                                         'thumbnail', 'thumbnails', 'num_lectures'])

  # Apply search filter ==> 필터 순서에 따라 결과가 달라질까???
  if len(filter_list_exercises) == 0 and len(filter_list_purposes) == 0 and len(filter_list_equipments) == 0:
    pass
  elif len(filter_list_exercises) > 0 and len(filter_list_purposes) == 0 and len(filter_list_equipments) == 0:
    programs_df = programs_df[programs_df['exercise'].isin([filter_list_exercises])]
  elif  len(filter_list_exercises) == 0 and len(filter_list_purposes) > 0 and len(filter_list_equipments) == 0:
    programs_df = programs_df[programs_df['purposes'].isin([filter_list_purposes])]
  elif len(filter_list_exercises) == 0 and len(filter_list_purposes) == 0 and len(filter_list_equipments) > 0:
    programs_df = programs_df[programs_df['equipments'].isin([filter_list_equipments])]
  elif len(filter_list_exercises) > 0 and len(filter_list_purposes) > 0 and len(filter_list_equipments) == 0:
    programs_df = programs_df[programs_df['exercise'].isin([filter_list_exercises]) &
                              programs_df['purposes'].isin([filter_list_purposes])]
  elif len(filter_list_exercises) > 0 and len(filter_list_purposes) == 0 and len(filter_list_equipments) > 0:
    programs_df = programs_df[programs_df['exercise'].isin([filter_list_exercises]) &
                              programs_df['equipments'].isin([filter_list_equipments])]
  elif len(filter_list_exercises) == 0 and len(filter_list_purposes) > 0 and len(filter_list_equipments) > 0:
    programs_df = programs_df[programs_df['purposes'].isin([filter_list_purposes]) &
                              programs_df['equipments'].isin([filter_list_equipments])]
  else:
    programs_df = programs_df[programs_df['exercise'].isin([filter_list_exercises]) &
                              programs_df['purposes'].isin([filter_list_purposes]) &
                              programs_df['equipments'].isin([filter_list_equipments])]
  program_ids = programs_df['program_id'].unique()

  result_list = []
  for each_id in program_ids:
    each_id = int(each_id)
    df_by_id = programs_df[programs_df['program_id'] == each_id]
    title = df_by_id['title'].unique()[0]  # For error 'TypeError: Object of type int64 is not JSON serializable'
    thumbnail = df_by_id['thumbnail'].unique()[0]
    thumbnails = df_by_id['thumbnails']
    thumbnails = sorted(thumbnails, key=lambda x: int(x.split('_')[1].split('w')[0]), reverse=True)  # Thumbnails needs be sorted from big size to small size(1080 -> ... 150).
    num_lectures = int(df_by_id['num_lectures'].unique()[0])
    # thumbnails_list = []
    # for image in thumbnails:
    #   each_dict = {"pathname": image}
    #   thumbnails_list.append(each_dict)

    result = {
      "id": each_id,
      "title": title,
      "thumbnail": thumbnail,
      "thumbnails": json.dumps(thumbnails).strip('][').split(', '),
      "num_lectures": num_lectures
    }
    result_list.append(result)

  result_dict = {
    "result": True,
    "search_results": result_list
  }
  return json.dumps(result_dict, ensure_ascii=False), 200
