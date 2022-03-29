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
           DATE_FORMAT(csl.released_at, '%Y-%m-%d') AS released_at,
           csl.title AS title,
           (SELECT pathname FROM files WHERE id = csl.thumbnail_id) AS thumbnail,
            (
                SELECT
                       JSON_ARRAYAGG(JSON_OBJECT('pathname', f.pathname))
                FROM
                     files f
                WHERE
                    f.original_file_id = csl.thumbnail_id
            ) AS thumbnails,
           (SELECT pathname from files WHERE id = csl.intro_id) AS intro,
           (SELECT mime_type from files WHERE id = csl.intro_id) AS mime_type,
           csl.description
        FROM
             coming_soon_list csl
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

    df = pd.DataFrame(result, columns=['id', 'released_at', 'title',
                                       'thumbnail', 'thumbnails',
                                       'intro', 'mime_type', 'descriptions'])
    df['thumbnails'] = df['thumbnails'].apply(lambda x: json.loads(x) if x is not None else None)

    result_dict = json.loads(df.to_json(orient='records'))

    return json.dumps(result_dict, ensure_ascii=False), 200
