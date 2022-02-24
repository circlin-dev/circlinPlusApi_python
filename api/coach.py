from global_things.constants import API_ROOT
from global_things.error_handler import HandleException
from global_things.functions.general import login_to_db, check_session, query_result_is_none
from global_things.functions.slack import slack_error_notification
from . import api
from datetime import datetime
from flask import url_for, request
import json
import pandas as pd
from pypika import MySQLQuery as Query, Criterion, Table, Order, functions as fn


@api.route('/coach', methods=['GET'])
def get_coaches():
    ip = request.headers["X-Forwarded-For"]
    endpoint = API_ROOT + url_for('api.get_coaches')
    # token = request.headers['Authorization']

    try:
        connection = login_to_db()
    except Exception as e:
        error = str(e)
        result = {
            'result': False,
            'error': f'Server Error while connecting to DB: {error}'
        }
        slack_error_notification(user_ip=ip, api=endpoint, error_message=result['error'], method=request.method)
        return json.dumps(result, ensure_ascii=False), 500
    cursor = connection.cursor()

    sql = f"""
    SELECT
        c.id,
        c.name,
        f.pathname AS coach_thumbnail,
        c.greeting AS introducing,
        c.category AS exercise,
        CASE
            WHEN c.affiliation = '' THEN NULL
            ELSE c.affiliation
        END AS team,
        JSON_ARRAY(JSON_OBJECT(
            'id', p.id,
            'title', p.title,
            'thumbnail', (SELECT pathname FROM files WHERE id=p.thumbnail_id),
            'release_at', p.release_at
        )) AS related_program,
        c.release_at,
        CASE
            WHEN c.release_at > NOW() THEN 'comming'
            ELSE 'released'
        END AS status,
        JSON_ARRAYAGG(pt.tag) AS tag,
        JSON_OBJECT(
            'id', prod.id,
            'title', prod.title,
            'thumbnail', (SELECT files.pathname FROM files WHERE files.id=(SELECT file_id FROM product_images WHERE product_id = prod.id AND type='thumbnail'))
        ) AS product,
       (SELECT files.pathname FROM files WHERE files.id=c.intro_id) AS intro
    FROM
         coaches c
    LEFT JOIN
        programs p
    ON p.coach_id = c.id
    LEFT JOIN
         program_tags as pt
    ON p.id = pt.program_id
    LEFT JOIN
        program_exercises pe
    ON
        pe.program_id = p.id
    LEFT JOIN
        exercises e
    ON
        pe.exercise_id = e.id
    LEFT JOIN
        files f
    ON
        c.profile_id = f.id
    LEFT JOIN
        program_products pp
    ON
        p.id = pp.program_id
    LEFT JOIN
        products prod
    ON
        pp.product_id = prod.id
    WHERE c.deleted_at IS NULL
    GROUP BY c.id"""
    cursor.execute(sql)
    coaches = cursor.fetchall()
    connection.close()

    result_list = []
    for coach in coaches:
        if coach[7] is None:
            release_at = None
        else:
            release_at = coach[7].strftime('%Y-%m-%d %H:%M:%S')
        if coach[11] is None:
            intro = None
        else:
            intro = coach[11]
        related_program = json.loads(coach[6])
        if json.loads(coach[9])[0] is None:
            tags = None
        else:
            tags = json.loads(coach[9])
        for x in related_program:
            if x['id'] is None:
                related_program.remove(x)

        result_dict = {
            "id": coach[0],
            "title": coach[1],
            "thumbnail": coach[2],
            "description": coach[3],
            "exercise": coach[4],
            "team": coach[5],
            "related_program": related_program,
            "release_at": release_at,
            "status": coach[8],
            "tag_list": tags,
            "related_equipment": json.loads(coach[10]),
            "intro": intro
        }
        result_list.append(result_dict)

    # result = {
    #     'result': True,
    #     'data': result_list
    # }
    return json.dumps(result_list, ensure_ascii=False), 200


@api.route('/coach/<coach_id>', methods=['GET'])
def get_coach(coach_id):
    ip = request.headers["X-Forwarded-For"]
    endpoint = API_ROOT + url_for('api.get_coach', coach_id=coach_id)
    # token = request.headers['Authorization']

    try:
        connection = login_to_db()
    except Exception as e:
        error = str(e)
        result = {
            'result': False,
            'error': f'Server Error while connecting to DB: {error}'
        }
        slack_error_notification(user_ip=ip, api=endpoint, error_message=result['error'], method=request.method)
        return json.dumps(result, ensure_ascii=False), 500
    cursor = connection.cursor()

    sql = f"""
        SELECT
            c.id,
            c.name,
            f.pathname AS coach_thumbnail,
            c.greeting AS introducing,
            c.category AS exercise,
            CASE
                WHEN c.affiliation = '' THEN NULL
                ELSE c.affiliation
            END AS team,
            JSON_ARRAY(JSON_OBJECT(
                'id', p.id,
                'title', p.title,
                'thumbnail', (SELECT pathname FROM files WHERE id=p.thumbnail_id),
                'release_at', p.release_at
            )) AS related_program,
            c.release_at,
            CASE
                WHEN c.release_at > NOW() THEN 'comming'
                ELSE 'released'
            END AS status,
            JSON_ARRAYAGG(pt.tag) AS tag,
            JSON_OBJECT(
                'id', prod.id,
                'title', prod.title,
                'thumbnail', (SELECT files.pathname FROM files WHERE files.id=(SELECT file_id FROM product_images WHERE product_id = prod.id AND type='thumbnail'))
            ) AS product,
           (SELECT files.pathname FROM files WHERE files.id=c.intro_id) AS intro
        FROM
             coaches c
        LEFT JOIN
            programs p
        ON p.coach_id = c.id
        LEFT JOIN
             program_tags as pt
        ON p.id = pt.program_id
        LEFT JOIN
            program_exercises pe
        ON
            pe.program_id = p.id
        LEFT JOIN
            exercises e
        ON
            pe.exercise_id = e.id
        LEFT JOIN
            files f
        ON
            c.profile_id = f.id
        LEFT JOIN
            program_products pp
        ON
            p.id = pp.program_id
        LEFT JOIN
            products prod
        ON
            pp.product_id = prod.id
        WHERE c.deleted_at IS NULL
        AND c.id={coach_id}
        GROUP BY c.id"""

    cursor.execute(sql)
    coach = cursor.fetchall()
    connection.close()

    if coach[0][7] is None:
        release_at = None
    else:
        release_at = coach[0][7].strftime('%Y-%m-%d %H:%M:%S')
    if coach[0][11] is None:
        intro = None
    else:
        intro = coach[0][11]
    related_program = json.loads(coach[0][6])
    if json.loads(coach[0][9])[0] is None:
        tags = None
    else:
        tags = json.loads(coach[0][9])
    for x in related_program:
        if x['id'] is None:
            related_program.remove(x)
    if json.loads(coach[0][10])['id'] is None:
        related_equipment = {}
    else:
        related_equipment = json.loads(coach[0][10])

    result_dict = {
        "id": coach[0][0],
        "title": coach[0][1],
        "thumbnail": coach[0][2],
        "description": coach[0][3],
        "exercise": coach[0][4],
        "team": coach[0][5],
        "related_program": related_program,
        "release_at": release_at,
        "status": coach[0][8],
        "tag_list": tags,
        "related_equipment": related_equipment,
        "intro": intro
    }

    return json.dumps(result_dict, ensure_ascii=False), 200
