from global_things.constants import API_ROOT
from global_things.error_handler import HandleException
from global_things.functions.general import login_to_db, check_session, query_result_is_none
from global_things.functions.slack import slack_error_notification
from . import api
from flask import url_for, request
import json
import pandas as pd


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
            (
                SELECT JSON_ARRAYAGG(f2.pathname) FROM files f
                INNER JOIN files f2 ON f.id = f2.original_file_id
                WHERE f.id = c.profile_id
            ) AS thumbnails,
            c.greeting AS description,
            c.category AS exercise,
            c.affiliation AS team,
            JSON_ARRAY(JSON_OBJECT(
                'id', p.id,
                'title', p.title,
                'thumbnail', (SELECT pathname FROM files WHERE id=p.thumbnail_id),
                'thumbnails', (SELECT JSON_ARRAYAGG(pathname) FROM files WHERE original_file_id = p.thumbnail_id),
                'intro', (SELECT pathname FROM files WHERE id=p.intro_id),
                'num_lectures', (SELECT COUNT(*) FROM lectures WHERE program_id = p.id),                
                'release_at', p.release_at
            )) AS related_programs,
            DATE_FORMAT(c.release_at, '%Y-%m-%d %H:%i:%s') AS release_at,
            CASE
                WHEN c.release_at > NOW() THEN 'comming'
                ELSE 'released'
            END AS status,
            JSON_ARRAYAGG(pt.tag) AS tag,
            JSON_OBJECT(
                'id', prod.id,
                'title', prod.title,
                'thumbnail', (SELECT files.pathname FROM files WHERE files.id=(SELECT file_id FROM product_images WHERE product_id = prod.id AND type='thumbnail')),
                'thumbnails', (
                    SELECT JSON_ARRAYAGG(pathname) FROM files
                        INNER JOIN product_images
                            ON product_images.file_id = files.original_file_id
                    WHERE product_images.product_id = prod.id AND product_images.type = 'thumbnail')
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
    result = cursor.fetchall()
    connection.close()

    coaches = pd.DataFrame(result, columns=['id', 'title',
                                            'thumbnail', 'thumbnails',
                                            'description', 'exercise',
                                            'team', 'related_programs',
                                            'release_at', 'status',
                                            'tags', 'product',
                                            'intro'])
    coaches['thumbnails'] = coaches['thumbnails'].apply(lambda x: json.loads(x))
    coaches['related_programs'] = coaches['related_programs'].apply(lambda x: json.loads(x))
    coaches['tags'] = coaches['tags'].apply(lambda x: json.loads(x))
    coaches['product'] = coaches['product'].apply(lambda x: json.loads(x))

    coaches['thumbnails'] = coaches['thumbnails'].apply(lambda x: [] if x[0] is None else x)
    coaches['tags'] = coaches['tags'].apply(lambda x: [] if x[0] is None else x)
    coaches['related_programs'] = coaches['related_programs'].apply(lambda x: [] if x[0]['id'] is None else x)
    coaches['product'] = coaches['product'].apply(lambda x: [] if x['id'] is None else x)

    result_dict = json.loads(coaches.to_json(orient='records'))
    return json.dumps(result_dict, ensure_ascii=False), 200


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
            (
                SELECT JSON_ARRAYAGG(f2.pathname) FROM files f
                INNER JOIN files f2 ON f.id = f2.original_file_id
                WHERE f.id = c.profile_id
            ) AS thumbnails,
            c.greeting AS description,
            c.category AS exercise,
            c.affiliation AS team,
            JSON_ARRAY(JSON_OBJECT(
                'id', p.id,
                'title', p.title,
                'thumbnail', (SELECT pathname FROM files WHERE id=p.thumbnail_id),
                'thumbnails', (SELECT JSON_ARRAYAGG(pathname) FROM files WHERE original_file_id = p.thumbnail_id),
                'intro', (SELECT pathname FROM files WHERE id=p.intro_id),
                'num_lectures', (SELECT COUNT(*) FROM lectures WHERE program_id = p.id),                
                'release_at', p.release_at
            )) AS related_programs,
            DATE_FORMAT(c.release_at, '%Y-%m-%d %H:%i:%s') AS release_at,
            CASE
                WHEN c.release_at > NOW() THEN 'comming'
                ELSE 'released'
            END AS status,
            JSON_ARRAYAGG(pt.tag) AS tag,
            JSON_OBJECT(
                'id', prod.id,
                'title', prod.title,
                'thumbnail', (SELECT files.pathname FROM files WHERE files.id=(SELECT file_id FROM product_images WHERE product_id = prod.id AND type='thumbnail')),
                'thumbnails', (
                    SELECT JSON_ARRAYAGG(pathname) FROM files
                        INNER JOIN product_images
                            ON product_images.file_id = files.original_file_id
                    WHERE product_images.product_id = prod.id AND product_images.type = 'thumbnail')
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
        AND c.id = {coach_id}
        GROUP BY c.id"""

    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()

    if query_result_is_none(result) is True:
        result_dict = {}
        return json.dumps(result_dict, ensure_ascii=False), 200

    coach = pd.DataFrame(result, columns=['id', 'title',
                                          'thumbnail', 'thumbnails',
                                          'description', 'exercise',
                                          'team', 'related_programs',
                                          'release_at', 'status',
                                          'tags', 'product',
                                          'intro'])
    coach['thumbnails'] = coach['thumbnails'].apply(lambda x: json.loads(x))
    coach['related_programs'] = coach['related_programs'].apply(lambda x: json.loads(x))
    coach['tags'] = coach['tags'].apply(lambda x: json.loads(x))
    coach['product'] = coach['product'].apply(lambda x: json.loads(x))

    coach['thumbnails'] = coach['thumbnails'].apply(lambda x: [] if x[0] is None else x)
    coach['tags'] = coach['tags'].apply(lambda x: [] if x[0] is None else x)
    coach['related_programs'] = coach['related_programs'].apply(lambda x: [] if x[0]['id'] is None else x)
    coach['product'] = coach['product'].apply(lambda x: [] if x['id'] is None else x)

    result_list = json.loads(coach.to_json(orient='records'))
    if len(result_list) == 0:
        result_dict = {}
    else:
        result_dict = result_list[0]
    return json.dumps(result_dict, ensure_ascii=False), 200


