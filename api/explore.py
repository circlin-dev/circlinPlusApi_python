from global_things.functions.slack import slack_error_notification
from global_things.functions.explore import explore_query
from global_things.functions.general import login_to_db, check_user, query_result_is_none
from . import api
import datetime
from flask import request
import json
import pandas as pd
import pymysql
import requests


@api.route('/explore/<search_filter>/<word>', methods=['GET'])
def explore(search_filter, word):
  """
  :param search_filter: 필터명(잠정: program, exercise, coach, equipment, purpose)
  :param word: 검색어
  :return: {"id": 0,
            "title": "",
            "thumbnail": "",
            "thumbnails": [{pathname: "320w.png"}, {pathname: "240w.png",}],
            "num_lectures": 0}
  """
  ip = request.remote_addr
  endpoint = '/explore/<search_filter>/<word>'

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

  query = explore_query(search_filter, word)

  cursor.execute(query)
  programs_df = pd.DataFrame(cursor.fetchall(), columns=['program_id', 'title', 'thumbnail', 'thumbnails', 'num_lectures'])
  program_ids = programs_df['program_id'].unique()

  result_list = []
  for each_id in program_ids:
    each_id = int(each_id)
    df_by_id = programs_df[programs_df['program_id'] == each_id]
    title = df_by_id['title'].unique()[0]  # For error 'TypeError: Object of type int64 is not JSON serializable'
    thumbnail = df_by_id['thumbnail'].unique()[0]
    thumbnails = df_by_id['thumbnails'].sort_values()  # Thumbnail needs be sorted from big size to small size(1080 -> ... 150).
    num_lectures = int(df_by_id['num_lectures'].unique()[0])
    thumbnails_list = []
    for image in thumbnails:
      each_dict = {"pathname": image}
      thumbnails_list.append(each_dict)

    result = {
      "id": each_id,
      "title": title,
      "thumbnail": thumbnail,
      "thumbnails": thumbnails_list,
      "num_lectures": num_lectures
    }
    result_list.append(result)

  result_dict = {
    "result": True,
    "search_results": result_list
  }
  return json.dumps(result_dict, ensure_ascii=False), 200
