from global_things.constants import API_ROOT
from global_things.functions.slack import slack_error_notification, slack_purchase_notification
from global_things.functions.general import login_to_db, check_session, query_result_is_none
from global_things.functions.order import get_import_access_token
from . import api
import ast
from datetime import datetime
from flask import jsonify, url_for, request
import json
import requests
import pandas as pd
from pypika import MySQLQuery as Query, Criterion, Interval, Table, Field, Order, functions as fn

@api.route('/program', methods=['GET'])
def read_programs():
    ip = request.headers["X-Forwarded-For"]
    endpoint = API_ROOT + url_for('api.read_products')
    # session_id = request.headers['Authorization']
    # check_session(session_id)
    """페이징 필요!!!"""

    try:
        connection = login_to_db()
    except Exception as e:
        error = str(e)
        result = {
            'result': False,
            'error': f'Server Error while connecting to DB: {error}'
        }
        slack_error_notification(user_ip=ip, user_id=0, api=endpoint, error_message=result['error'], method=request.method)
        return json.dumps(result, ensure_ascii=False), 500

    cursor = connection.cursor()
    sql = f"""
        SELECT
               p.id,
               DATE_FORMAT(p.release_at, '%Y-%m-%d %H:%i:%s') AS release_at,
                CASE
                    WHEN p.release_at > NOW() THEN 'comming'
                    ELSE 'released'
                END AS status,
               p.type,
               p.title,
               p.subtitle,
               p.description,
               f.pathname,
               (SELECT DISTINCT COUNT(round) FROM lectures WHERE program_id = p.id) AS num_rounds,
               (SELECT COUNT(*) FROM lectures WHERE program_id = p.id) AS num_lectures,
               JSON_OBJECT(
                   'id', c.id,
                   'name', c.name,
                   'thumbnail', (SELECT pathname FROM files WHERE id = c.profile_id),
                   'description', c.greeting,
                   'exercise', c.category,
                   'team', CASE WHEN c.affiliation = '' THEN NULL ELSE c.affiliation END,
                   'intro', (SELECT pathname FROM files WHERE id = c.intro_id)
                ) AS coach,
                e.title AS exercises,
               JSON_ARRAYAGG(
                   JSON_OBJECT(
                       'id', prod.id,
                       'title', prod.title,
                       'thumbnail', (SELECT pathname FROM files WHERE id = (SELECT pi.file_id FROM product_images pi WHERE pi.product_id = prod.id AND pi.type = 'thumbnail')),
                       'stocks', prod.stocks,
                       'is_hidden', prod.is_hidden
                   )
               ) AS products
        FROM
             programs p
        INNER JOIN
            files f
        ON
            p.thumbnail_id = f.id
        INNER JOIN
            coaches c
        ON
            p.coach_id = c.id
        INNER JOIN
            program_exercises pe
        ON
            p.id = pe.program_id
        INNER JOIN
            exercises e
        ON
            pe.exercise_id = e.id
        LEFT OUTER JOIN
            program_products pp
        ON
            pp.program_id = p.id
        LEFT OUTER JOIN
            products prod
        ON
            pp.product_id = prod.id
        WHERE p.deleted_at IS NULL
        GROUP BY p.id"""
    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()

    programs = pd.DataFrame(result, columns=['id', 'release_at', 'status', 'type',
                                             'title', 'subtitle', 'description',
                                             'pathname', 'num_rounds', 'num_lectures',
                                             'coach', 'exercises', 'products'])
    programs['coach'] = programs['coach'].apply(lambda x: json.loads(x))
    programs['products'] = programs['products'].apply(lambda x: json.loads(x))
    programs['products'] = programs['products'].apply(lambda x: list({data['id']: data for data in x}.values()))
    programs['products'] = programs['products'].apply(lambda x: [] if x[0]['id'] is None else x)

    result_dict = json.loads(programs.to_json(orient='records'))
    return json.dumps(result_dict, ensure_ascii=False), 200


@api.route('/program/<program_id>', methods=['GET'])
def read_programs(program_id):
    ip = request.headers["X-Forwarded-For"]
    endpoint = API_ROOT + url_for('api.read_products')
    # session_id = request.headers['Authorization']
    # check_session(session_id)
    """페이징 필요!!!"""

    try:
        connection = login_to_db()
    except Exception as e:
        error = str(e)
        result = {
            'result': False,
            'error': f'Server Error while connecting to DB: {error}'
        }
        slack_error_notification(user_ip=ip, user_id=0, api=endpoint, error_message=result['error'], method=request.method)
        return json.dumps(result, ensure_ascii=False), 500

    cursor = connection.cursor()
    sql = f"""
        SELECT
               p.id,
               DATE_FORMAT(p.release_at, '%Y-%m-%d %H:%i:%s') AS release_at,
               CASE
                    WHEN p.release_at > NOW() THEN 'comming'
                    ELSE 'released'
                END AS status,
               p.type,
               p.title,
               p.subtitle,
               p.description,
               f.pathname,
               (SELECT DISTINCT COUNT(round) FROM lectures WHERE program_id = p.id) AS num_rounds,
               (SELECT COUNT(*) FROM lectures WHERE program_id = p.id) AS num_lectures,
               JSON_OBJECT(
                   'id', c.id,
                   'name', c.name,
                   'thumbnail', (SELECT pathname FROM files WHERE id = c.profile_id),
                   'description', c.greeting,
                   'exercise', c.category,
                   'team', CASE WHEN c.affiliation = '' THEN NULL ELSE c.affiliation END,
                   'intro', (SELECT pathname FROM files WHERE id = c.intro_id)
                ) AS coach,
                e.title AS exercises,
               JSON_ARRAYAGG(
                   JSON_OBJECT(
                       'id', prod.id,
                       'title', prod.title,
                       'thumbnail', (SELECT pathname FROM files WHERE id = (SELECT pi.file_id FROM product_images pi WHERE pi.product_id = prod.id AND pi.type = 'thumbnail')),
                       'stocks', prod.stocks,
                       'is_hidden', prod.is_hidden
                   )
               ) AS products
        FROM
             programs p
        INNER JOIN
            files f
        ON
            p.thumbnail_id = f.id
        INNER JOIN
            coaches c
        ON
            p.coach_id = c.id
        INNER JOIN
            program_exercises pe
        ON
            p.id = pe.program_id
        INNER JOIN
            exercises e
        ON
            pe.exercise_id = e.id
        LEFT OUTER JOIN
            program_products pp
        ON
            pp.program_id = p.id
        LEFT OUTER JOIN
            products prod
        ON
            pp.product_id = prod.id
        WHERE p.deleted_at IS NULL
        GROUP BY p.id"""
    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()

    programs = pd.DataFrame(result, columns=['id', 'release_at', 'status', 'type',
                                             'title', 'subtitle', 'description',
                                             'pathname', 'num_rounds', 'num_lectures',
                                             'coach', 'exercises', 'products'])
    programs['coach'] = programs['coach'].apply(lambda x: json.loads(x))
    programs['products'] = programs['products'].apply(lambda x: json.loads(x))
    programs['products'] = programs['products'].apply(lambda x: list({data['id']: data for data in x}.values()))
    programs['products'] = programs['products'].apply(lambda x: [] if x[0]['id'] is None else x)

    result_dict = json.loads(programs.to_json(orient='records'))
    return json.dumps(result_dict, ensure_ascii=False), 200
