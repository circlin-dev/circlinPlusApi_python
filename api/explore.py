from global_things.functions.slack import slack_error_notification
from global_things.functions.general import login_to_db, check_user, query_result_is_none
from . import api
import datetime
from flask import request
import json
import pandas as pd
import pymysql
import requests


@api.route('/explore/<filter>/<word>', methods=['GET'])
def explore(filter, word):
  """
  :param filter: 필터명(잠정: program, exercise, coach, equipment, purpose)
  :param word: 검색어
  :return: {"id": 0,
            "title": "",
            "thumbnail": "",
            "thumbnails": [{pathname: "320w.png"}, {pathname: "240w.png",}],
            "num_lectures": 0}
  """
  ip = request.remote_addr
  endpoint = '/explore/<filter>/<word>'

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

  if filter == 'program':
    query = f"""
      SELECT
            p.id AS program_id,
            p.title,
            (SELECT pathname FROM files WHERE id = p.thumbnail_id) AS thumbnail            
            f.pathname AS thumbnails,
            (SELECT COUNT(*) FROM program_lectures WHERE program_id = 1) AS num_lectures,
    
        FROM
            programs p,
            files f
        WHERE 
            p.title LIKE "%{word}%"
        AND
            f.original_file_id = p.thumbnail_id"""
  else:
    pass

  cursor.execute(query)
  programs_df = pd.DataFrame(cursor.fetchall(), columns=['program_id', 'title', 'thumbnail', 'thumbnails', 'num_lectures'])
  program_ids = programs_df['program_id'].unique()

  result_list = []
  for each_id in program_ids:
    df_by_id = programs_df[programs_df['program_id'] == each_id]
    title = df_by_id['title'].unique()[0]
    thumbnail = df_by_id['thumbnail'].unique()[0]
    thumbnails = df_by_id['thumbnails'].sort_values(ascending=True)  # Thumbnail needs be sorted from big size to small size(1080 -> ... 150).
    num_lectures = df_by_id['num_lectures'].unique()[0]
    thumbnails_list = []
    for image in thumbnails:
      each_dict = {"pathname": image}
      thumbnails.append(each_dict)

    result = {
      "id": each_id,
      "title": title,
      "thumbnail": thumbnail,
      "thumbnails": thumbnails,
      "num_lectures": num_lectures
    }
    result_list.append(result)

  result_dict = {
    "result": True,
    "search_results": result_list
  }
  return json.dumps(result_dict, ensure_ascii=False), 200