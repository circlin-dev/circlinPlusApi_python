from . import api
from global_things.constants import IMAGE_ANALYSYS_SERVER, SLACK_NOTIFICATION_WEBHOOK
from config.database import DB_CONFIG
import datetime
from flask import request
import json
import pymysql
from pymysql.converters import escape_string
import requests




@api.route('/explore/<filter>/<word>', methods=['GET'])
def explore(filter, word):
  '''

  :param filter: 필터명(잠정: 운동, 강사, 기구, 목표
  :param word: 검색어
  :return:
  '''
  ip = request.remote_addr
  endpoint = '/explore/<word>'

  return None