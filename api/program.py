from global_things.constants import API_ROOT
from global_things.functions.slack import slack_error_notification
from global_things.functions.general import login_to_db, query_result_is_none
from global_things.functions.order import get_import_access_token
from . import api
from flask import url_for, request
import json
import pandas as pd

@api.route('/program', methods=['GET'])
def read_programs():
    ip = request.headers["X-Forwarded-For"]
    endpoint = API_ROOT + url_for('api.read_programs')
    """페이징 필요!!!"""

    connection = login_to_db()
    cursor = connection.cursor()
    sql = f"""
        SELECT
               p.id,
               DATE_FORMAT(p.released_at, '%Y-%m-%d %H:%i:%s') AS released_at,
                CASE
                    WHEN p.released_at > NOW() THEN 'comming'
                    ELSE 'released'
                END AS status,
               p.type,
               p.title,
               p.subtitle,
               p.description,
               JSON_ARRAYAGG(pt.tag) AS tags,
               (SELECT pathname FROM files WHERE id = p.intro_id) AS intro,               
               f.pathname AS thumbnail,
               (SELECT DISTINCT COUNT(round) FROM lectures WHERE program_id = p.id) AS num_rounds,
               (SELECT COUNT(*) FROM lectures WHERE program_id = p.id) AS num_lectures,
               JSON_OBJECT(
                   'id', c.id,
                   'title', c.name,
                   'thumbnail', (SELECT pathname FROM files WHERE id = c.profile_id),
                   'description', c.greeting,
                   'exercise', c.category,
                   'team', c.affiliation,
                   'intro', (SELECT pathname FROM files WHERE id = c.intro_id)
                ) AS coach,
                e.title AS exercise,
               JSON_ARRAYAGG(
                   JSON_OBJECT(
                       'id', prod.id,
                       'type', prod.type,
                       'code', prod.code,
                       'title', prod.title,
                       'description', prod.description,
                       'brandTitle', (SELECT title FROM brands WHERE id = prod.brand_id),
                       'original_price', prod.original_price,
                       'price', prod.price,
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
       LEFT JOIN
             program_tags as pt
        ON p.id = pt.program_id            
        WHERE p.deleted_at IS NULL
        GROUP BY p.id"""
    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()

    programs = pd.DataFrame(result, columns=['id', 'released_at', 'status', 'type',
                                             'title', 'subtitle', 'description', 'tags', 'intro',
                                             'thumbnail', 'num_rounds', 'num_lectures',
                                             'coach', 'exercise', 'products'])
    programs['coach'] = programs['coach'].apply(lambda x: json.loads(x))
    programs['tags'] = programs['tags'].apply(lambda x: json.loads(x))
    programs['products'] = programs['products'].apply(lambda x: json.loads(x))
    programs['products'] = programs['products'].apply(lambda x: list({data['id']: data for data in x}.values()))
    programs['products'] = programs['products'].apply(lambda x: [] if x[0]['id'] is None else x)

    result_dict = json.loads(programs.to_json(orient='records'))
    return json.dumps(result_dict, ensure_ascii=False), 200


@api.route('/program/<program_id>', methods=['GET'])
def read_a_program(program_id):
    ip = request.headers["X-Forwarded-For"]
    endpoint = API_ROOT + url_for('api.read_a_program', program_id=program_id)
    """페이징 필요!!!"""

    connection = login_to_db()
    cursor = connection.cursor()
    sql = f"""
        SELECT
               p.id,
               DATE_FORMAT(p.released_at, '%Y-%m-%d %H:%i:%s') AS released_at,
               CASE
                    WHEN p.released_at > NOW() THEN 'comming'
                    ELSE 'released'
                END AS status,
               p.type,
               p.title,
               p.subtitle,
               p.description,
               JSON_ARRAYAGG(pt.tag) AS tags,               
               (SELECT pathname FROM files WHERE id = p.intro_id) AS intro,
               f.pathname AS thumbnail,
               (SELECT DISTINCT COUNT(round) FROM lectures WHERE program_id = p.id) AS num_rounds,
               (SELECT COUNT(*) FROM lectures WHERE program_id = p.id) AS num_lectures,
               JSON_OBJECT(
                   'id', c.id,
                   'title', c.name,
                   'thumbnail', (SELECT pathname FROM files WHERE id = c.profile_id),
                   'description', c.greeting,
                   'exercise', c.category,
                   'team', c.affiliation,
                   'intro', (SELECT pathname FROM files WHERE id = c.intro_id)
                ) AS coach,
                e.title AS exercise,
               JSON_ARRAYAGG(
                   JSON_OBJECT(
                        'id', prod.id,
                       'type', prod.type,
                       'code', prod.code,
                       'title', prod.title,
                       'description', prod.description,
                       'brandTitle', (SELECT title FROM brands WHERE id = prod.brand_id),
                       'original_price', prod.original_price,
                       'price', prod.price,
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
        LEFT JOIN
             program_tags as pt
        ON 
            p.id = pt.program_id            
        WHERE p.deleted_at IS NULL
        AND p.id = {program_id}
        GROUP BY p.id"""
    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()

    if query_result_is_none(result) is True:
        result_dict = {}
        return json.dumps(result_dict, ensure_ascii=False), 200

    programs = pd.DataFrame(result, columns=['id', 'released_at', 'status', 'type',
                                             'title', 'subtitle', 'description', 'tags', 'intro',
                                             'thumbnail', 'num_rounds', 'num_lectures',
                                             'coach', 'exercise', 'products'])
    # programs = pd.DataFrame(result, columns=['id', 'released_at', 'status', 'type',
    #                                          'title', 'subtitle', 'description', 'tags', 'intro',
    #                                          'thumbnail', 'thumbnails', 'num_rounds', 'num_lectures',
    #                                          'coach', 'exercise', 'products'])
    programs['coach'] = programs['coach'].apply(lambda x: json.loads(x))
    programs['tags'] = programs['tags'].apply(lambda x: json.loads(x))
    programs['products'] = programs['products'].apply(lambda x: json.loads(x))
    programs['products'] = programs['products'].apply(lambda x: list({data['id']: data for data in x}.values()))
    programs['products'] = programs['products'].apply(lambda x: [] if x[0]['id'] is None else x)
    # products_df['thumbnails'] = products_df['thumbnails'].apply(lambda x: [] if x is None else json.loads(x))

    result_list = json.loads(programs.to_json(orient='records'))
    if len(result_list) == 0:
        result_dict = {}
    else:
        result_dict = result_list[0]
    return json.dumps(result_dict, ensure_ascii=False), 200

