from global_things.constants import API_ROOT
from global_things.functions.slack import slack_error_notification, slack_purchase_notification
from global_things.functions.general import login_to_db, check_session, query_result_is_none
from global_things.functions.order import get_import_access_token
from . import api
import ast
from flask import jsonify, url_for, request
import json
import requests
import pandas as pd
from pypika import MySQLQuery as Query, Criterion, Interval, Table, Field, Order, functions as fn


@api.route('/products', methods=['GET'])
def read_products():
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

    query_parameter = request.args.to_dict()  # type: equipment(기구), starterkit(스타터키트), item(상품)
    parameters = []
    for key in query_parameter.keys():
        parameters.append(request.args[key].strip())

    cursor = connection.cursor()
    if parameters == [] or len(parameters) == 0:
        """GET everything in 'products' table. => Don't use 'where' clause in sql."""
        sql = f"""
            SELECT
               prod.id,
               prod.type,
               prod.code,
               prod.title as name,
               prod.description,
               b.title as brand_name,
               prod.original_price as original_price,
               prod.price as price,
               IFNULL(prod.stocks, 0),
               (SELECT
                       f2.pathname
               FROM
                    files f2
                INNER JOIN product_images pi2
               ON pi2.file_id = f2.id
                WHERE pi2.type='thumbnail' AND pi2.product_id=prod.id) AS thumbnail,
               JSON_ARRAYAGG(IFNULL(f.pathname, '')) AS details,
               JSON_ARRAYAGG(
                    JSON_OBJECT(
                        'id', prog.id,
                        'title', prog.title,
                        'thumbnail', (SELECT pathname FROM files WHERE id = prog.thumbnail_id),
                        'num_lectures', (SELECT COUNT(*) FROM lectures WHERE program_id = prog.id),
                        'exercise', (SELECT title FROM exercises e INNER JOIN program_exercises pe ON e.id = pe.exercise_id WHERE pe.program_id=prog.id)
                    )
                ) AS related_program,
                 prod.status
            FROM
                products prod
            INNER JOIN
                    brands b
                ON b.id = prod.brand_id
            LEFT OUTER JOIN
                    product_images pi
                ON pi.product_id = prod.id
            LEFT OUTER JOIN
                    files f
                ON f.id = pi.file_id
            LEFT OUTER JOIN
                    program_products pp
                ON prod.id = pp.product_id
            LEFT OUTER JOIN
                    programs prog
                ON prog.id = pp.program_id       
            GROUP BY prod.id"""
    else:
        sql = f"""
                SELECT DISTINCT
                   prod.id,
                   prod.type,
                   prod.code,
                   prod.title as title,
                   prod.description,
                   b.title as brandTitle,
                   prod.original_price as original_price,
                   prod.price as price,
                   IFNULL(prod.stocks, 0),
                   (SELECT
                           f2.pathname
                   FROM
                        files f2
                    INNER JOIN product_images pi2
                   ON pi2.file_id = f2.id
                    WHERE pi2.type='thumbnail' AND pi2.product_id=prod.id) AS thumbnail,
                   JSON_ARRAYAGG(IFNULL(f.pathname, '')) AS details,
                   JSON_ARRAYAGG(
                        JSON_OBJECT(
                            'id', prog.id,
                            'title', prog.title,
                            'thumbnail', (SELECT pathname FROM files WHERE id = prog.thumbnail_id),
                            'num_lectures', (SELECT COUNT(*) FROM lectures WHERE program_id = prog.id),
                            'exercise', (SELECT title FROM exercises e INNER JOIN program_exercises pe ON e.id = pe.exercise_id WHERE pe.program_id=prog.id)
                        )) AS related_program,
                    prod.status
                FROM
                    products prod
                INNER JOIN
                        brands b
                    ON b.id = prod.brand_id
                LEFT OUTER JOIN
                        product_images pi
                    ON pi.product_id = prod.id
                LEFT OUTER JOIN
                        files f
                    ON f.id = pi.file_id
                LEFT OUTER JOIN
                        program_products pp
                    ON prod.id = pp.product_id
                LEFT OUTER JOIN
                        programs prog
                    ON prog.id = pp.program_id
                WHERE prod.type='{parameters[0]}'
                GROUP BY prod.id"""
    cursor.execute(sql)
    result = cursor.fetchall()

    if query_result_is_none(result):
        connection.close()
        result_dict = {}
        return json.dumps(result_dict, ensure_ascii=False), 200

    products_df = pd.DataFrame(result, columns=['id', 'type', 'code',
                                                'title', 'description', 'brandTitle',
                                                'original_price', 'price', 'stocks',
                                                'thumbnail', 'details', 'related_program', 'status'])
    try:
        products_df['details'] = products_df['details'].apply(lambda x: json.loads(x))
        products_df['details'] = products_df['details'].apply(lambda x: [] if x[0] == "" else x)
    except:
        connection.close()
        result_dict = json.loads(products_df.to_json(orient='records'))  # Array type으로 가고있음
        return json.dumps(result_dict, ensure_ascii=False), 200
    try:
        products_df['related_program'] = products_df['related_program'].apply(lambda x: json.loads(x))
        products_df['related_program'] = products_df['related_program'].apply(lambda x: list({data['id']: data for data in x}.values()))
        products_df['related_program'] = products_df['related_program'].apply(lambda x: [] if x[0]['id'] is None else x)
    except:
        connection.close()
        result_dict = json.loads(products_df.to_json(orient='records'))  # Array type으로 가고있음
        return json.dumps(result_dict, ensure_ascii=False), 200

    connection.close()
    result_dict = json.loads(products_df.to_json(orient='records'))  # Array type으로 가고있음
    return json.dumps(result_dict, ensure_ascii=False), 200


@api.route('/products/<product_id>', methods=['GET'])
def read_a_product(product_id: int):
    ip = request.headers["X-Forwarded-For"]
    endpoint = API_ROOT + url_for('api.read_a_product', product_id=product_id)
    # session_id = request.headers['Authorization']
    # check_session(session_id)
    programs = Table('programs')
    products = Table('products')
    program_products = Table('program_products')
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

    # related_program이 복수이면 JSON_ARRAYAGG()로 합치고, GROUP BY에 prog.id 또는 pp.program_id 추가해야 할듯.
    # sql = f"""
    #     SELECT
    #        prod.id,
    #        prod.type,
    #        prod.code,
    #        prod.title as title,
    #        prod.description,
    #        b.title as brandTitle,
    #        prod.original_price as original_price,
    #        prod.price as price,
    #        IFNULL(prod.stocks, 0),
    #        prod.thumbnail,
    #        JSON_ARRAYAGG(IFNULL(f.pathname, '')) AS details,
    #        JSON_ARRAYAGG(
    #             JSON_OBJECT(
    #                 'id', prog.id,
    #                 'title', prog.title,
    #                 'thumbnail', (SELECT pathname FROM files WHERE id = prog.thumbnail_id),
    #                 'num_lectures', (SELECT COUNT(*) FROM lectures WHERE program_id = prog.id),
    #                 'exercise', (SELECT title FROM exercises e INNER JOIN program_exercises pe ON e.id = pe.exercise_id WHERE pe.program_id=prog.id)
    #             )
    #         ) AS related_program,
    #         prod.status
    #     FROM
    #         products prod
    #     INNER JOIN
    #             brands b
    #         ON b.id = prod.brand_id
    #     LEFT OUTER JOIN
    #             product_images pi
    #         ON pi.product_id = prod.id
    #     LEFT OUTER JOIN
    #             files f
    #         ON f.id = pi.file_id
    #     LEFT OUTER JOIN
    #             program_products pp
    #         ON prod.id = pp.product_id
    #     LEFT OUTER JOIN
    #             programs prog
    #         ON prog.id = pp.program_id
    #     WHERE prod.id = {product_id}
    #     GROUP BY prod.id"""
    sql = f"""
        SELECT DISTINCT
           prod.id,
           prod.type,
           prod.code,
           prod.title as title,
           prod.description,
           b.title as brandTitle,
           prod.original_price as original_price,
           prod.price as price,
           IFNULL(prod.stocks, 0),
           (SELECT
                   f2.pathname
           FROM
                files f2
            INNER JOIN product_images pi2
           ON pi2.file_id = f2.id
            WHERE pi2.type='thumbnail' AND pi2.product_id=prod.id) AS thumbnail,
           JSON_ARRAYAGG(IFNULL(f.pathname, '')) AS details,
           JSON_ARRAYAGG(
                JSON_OBJECT(
                    'id', prog.id,
                    'title', prog.title,
                    'thumbnail', (SELECT pathname FROM files WHERE id = prog.thumbnail_id),
                    'num_lectures', (SELECT COUNT(*) FROM lectures WHERE program_id = prog.id),
                    'exercise', (SELECT title FROM exercises e INNER JOIN program_exercises pe ON e.id = pe.exercise_id WHERE pe.program_id=prog.id)
                )) AS related_program,
            prod.status
        FROM
            products prod
        INNER JOIN
                brands b
            ON b.id = prod.brand_id
        LEFT OUTER JOIN
                product_images pi
            ON pi.product_id = prod.id
        LEFT OUTER JOIN
                files f
            ON f.id = pi.file_id
        LEFT OUTER JOIN
                program_products pp
            ON prod.id = pp.product_id
        LEFT OUTER JOIN
                programs prog
            ON prog.id = pp.program_id
        WHERE prod.id = {product_id}
        GROUP BY prod.id"""
    cursor.execute(sql)

    result = cursor.fetchall()
    if query_result_is_none(result) is True:
        connection.close()
        result_dict = {}
        return json.dumps(result_dict, ensure_ascii=False), 200

    products_df = pd.DataFrame(result, columns=['id', 'type', 'code',
                                                'title', 'description', 'brandTitle',
                                                'original_price', 'price', 'stocks',
                                                'thumbnail', 'details', 'related_program', 'status'])
    try:
        products_df['details'] = products_df['details'].apply(lambda x: json.loads(x))
        products_df['details'] = products_df['details'].apply(lambda x: [] if x[0] == "" else x)
    except:
        connection.close()
        # 썸네일만 없는 경우.
        result_dict = json.loads(products_df.to_json(orient='records'))[0]  # Array type으로 가고있음
        return json.dumps(result_dict, ensure_ascii=False), 200
    try:
        products_df['related_program'] = products_df['related_program'].apply(lambda x: json.loads(x))
        products_df['related_program'] = products_df['related_program'].apply(lambda x: list({data['id']: data for data in x}.values()))
        products_df['related_program'] = products_df['related_program'].apply(lambda x: [] if x[0]['id'] is None else x)
    except:
        connection.close()
        result_dict = json.loads(products_df.to_json(orient='records'))[0]  # Array type으로 가고있음
        return json.dumps(result_dict, ensure_ascii=False), 200
    connection.close()
    result_dict = json.loads(products_df.to_json(orient='records'))[0]  # Array type으로 가고있음
    return json.dumps(result_dict, ensure_ascii=False), 200


