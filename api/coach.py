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
        JSON_OBJECT(
            'id', f.id, 
            'thumbnail', f.pathname
        ) AS coach_thumbnail,
        c.greeting AS introducing,
        c.category AS related_exercise,
        c.affiliation AS team,
        JSON_OBJECT(
            'id', p.id, 
            'title', p.title,
            'thumbnail', (SELECT pathname FROM files WHERE id=p.thumbnail_id)            
        ) AS related_program,
        p.release_at,
        CASE
            WHEN p.release_at > NOW() THEN 'future'
            ELSE 'on_sale'
        END AS status,
        JSON_ARRAYAGG(JSON_OBJECT('id', pt.id, 'tag', pt.tag)) AS tag,
        JSON_OBJECT(
            'id', prod.id,
            'title', prod.title,
            'thumbnail', (SELECT files.pathname FROM files WHERE files.id=(SELECT file_id FROM product_images WHERE product_id = prod.id AND type='thumbnail'))
        ) AS related_product
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
    coaches = pd.DataFrame(cursor.fetchall(),
                           columns=['id', 'name', 'thumbnail', 'introducing',
                                    'exercise', 'team', 'related_program',
                                    'release_at', 'status', 'tag', 'related_product'])
    coach_ids = coaches['id'].unique()
    result_list = []
    for each_id in coach_ids:
        each_id = int(each_id)
        df_by_id = coaches[coaches['id'] == each_id]
        thumbnail = json.loads(df_by_id['thumbnail'].unique()[0])
        introducing = df_by_id['introducing'].unique()[0]
        exercise = df_by_id['exercise'].unique()[0]
        team = df_by_id['team'].unique()[0]
        related_program = json.loads(df_by_id['related_program'].unique()[0])
        if df_by_id['release_at'].unique()[0].dt is None:
            release_at = None
        else:
            release_at = pd.to_datetime(df_by_id['release_at'].unique()[0]).dt.strftime('%Y-%m-%d %H:%M:%S')
        status = df_by_id['status'].unique()[0]
        tag_list = json.loads(df_by_id['tag'].unique()[0])
        related_product = json.loads(df_by_id['related_product'].unique()[0])

        result_dict = {
            "id": each_id,
            "thumbnail": thumbnail,
            "introducing": introducing,
            "exercise": exercise,
            "team": team,
            "related_program": related_program,
            "release_at": release_at,
            "status": status,
            "tag_list": tag_list,
            "related_product": related_product
        }
        result_list.append(result_dict)

    result = {
        'result': True,
        'data': result_list
    }
    return json.dumps(result, ensure_ascii=False), 200


@api.route('/coach/<coach_id>', methods=['GET'])
def get_coach(coach_id):
    ip = request.headers["X-Forwarded-For"]
    endpoint = API_ROOT + url_for('api.get_coach', coach_id=coach_id)
    # token = request.headers['Authorization']

    sql = f"""
        SELECT
            c.id,
            c.name,
            JSON_OBJECT('id', f.id, 'thumbnail', f.pathname) AS coach_thumbnail,
            c.greeting AS introducing,
            c.category AS exercise,
            c.affiliation AS team,
            JSON_OBJECT('id', p.id, 'title', p.title) AS program_title,
            p.release_at,
            CASE
                WHEN p.release_at > NOW() THEN 'future'
                ELSE 'on_sale'
            END AS status,
            JSON_ARRAYAGG(JSON_OBJECT('id', pt.id, 'tag', pt.tag)) AS tag,
            JSON_OBJECT(
                'id', prod.id,
                'title', prod.title,
                'thumbnail', (SELECT files.pathname FROM files WHERE files.id=(SELECT file_id FROM product_images WHERE product_id = prod.id AND type='thumbnail'))
            ) AS product
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