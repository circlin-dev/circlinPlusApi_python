# from pypika import MySQLQuery as Query, Table, Criterion, functions as fn
from . import api
from global_things.constants import API_ROOT
from global_things.functions.general import login_to_db, check_user_token, query_result_is_none
from flask import url_for, request
import json
import pandas as pd

@api.route('/coming-soon', methods=['GET'])
def get_coming_soon():
    ip = request.headers["X-Forwarded-For"]  # Both public & private.
    endpoint = API_ROOT + url_for('api.get_coming_soon')
    # user_token = request.headers.get('Authorization')
    # coming_soon_list = Table('coming_soon_list')
    # files = Table('files')
    # coaches = Table('coaches')

    connection = login_to_db()
    cursor = connection.cursor()

    sql = """
        SELECT
           csl.order AS id,
           csl.released_at AS released_at,
           csl.title AS title,
           f.pathname,
           (SELECT pathname FROM files WHERE id = c.profile_id) AS thumbnail,
           (SELECT JSON_ARRAYAGG(JSON_OBJECT('pathname', pathname)) FROM files WHERE original_file_id = c.profile_id) AS thumbnails,
           (SELECT pathname from files WHERE id = csl.intro_id) AS intro,
           csl.description,
           JSON_ARRAYAGG(JSON_OBJECT(
               'id', c.id,
               'team', c.affiliation,
               'intro', (SELECT pathname FROM files WHERE id = c.intro_id),
               'title', c.name,
               'thumbnail', (SELECT pathname FROM files WHERE id = c.profile_id),
               'thumbnails', (SELECT JSON_ARRAYAGG(JSON_OBJECT('pathname', pathname)) FROM files WHERE original_file_id = c.profile_id),
               'exercise', c.category,
               'description', c.greeting
           )) AS coach
        FROM
             coming_soon_list csl
        INNER JOIN
                 coaches c
            ON
                c.id = csl.coach_id
        INNER JOIN
                 files f
            ON csl.intro_id = f.id
        WHERE csl.deleted_at IS NULL
        GROUP BY csl.order
        ORDER BY csl.order"""
    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()

    if query_result_is_none(result) is True:
        result = {}
        return json.dumps(result, ensure_ascii=False), 200

    data = result[0][0]
    df = pd.DataFrame(data, columns=['id', 'released_at', 'title',
                                     'thumbnail', 'thumbnails',
                                     'intro', 'descriptions', 'coach'])
    df['thumbnails'] = df['thumbnails'].apply(lambda x: json.loads(x))
    df['coach'] = df['coach'].apply(lambda x: json.loads(x))

    result_dict = json.loads(df.to_json(orient='records'))

    return json.dumps(result_dict, ensure_ascii=False), 200
