from global_things.constants import API_ROOT
from global_things.functions.slack import slack_error_notification
from global_things.functions.general import login_to_db, check_session, query_result_is_none
from . import api
from flask import url_for, request
import json
import pandas as pd


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
               prod.title as title,
               prod.description,
               b.title as brandTitle,
               prod.original_price as original_price,
               prod.price as price,
               CASE
                   WHEN (IFNULL(prod.stocks, 0) - IFNULL((SELECT SUM(qty) FROM order_products WHERE product_id=prod.id), 0)) <= 0 THEN 0
                   WHEN (IFNULL(prod.stocks, 0) - IFNULL((SELECT SUM(qty) FROM order_products WHERE product_id=prod.id), 0)) > 0 THEN (IFNULL(prod.stocks, 0) - IFNULL((SELECT SUM(qty) FROM order_products WHERE product_id=prod.id), 0))
               END AS stock,
               (
                   SELECT
                       f2.pathname
                   FROM
                        files f2
                    INNER JOIN product_images pi2
                   ON pi2.file_id = f2.id
                    WHERE pi2.type='thumbnail' AND pi2.product_id=prod.id
                ) AS thumbnail,
--                (
--                    SELECT JSON_ARRAYAGG(pathname) FROM files
--                        INNER JOIN product_images
--                             ON product_images.file_id = files.original_file_id
--                    WHERE product_images.product_id = prod.id AND product_images.type = 'thumbnail'
--                ) AS thumbnails,
               (
                   SELECT JSON_ARRAYAGG(pathname) FROM files
                       INNER JOIN product_images
                           ON product_images.file_id = files.id
                   WHERE product_images.type = 'detail' AND product_images.product_id = prod.id
               ) AS details,
--                (
--                    SELECT JSON_ARRAYAGG(pathname) FROM files
--                        INNER JOIN product_images
--                             ON product_images.file_id = files.original_file_id
--                    WHERE product_images.type = 'detail' AND product_images.product_id = prod.id
--                ) AS detail_thumbnails,
               JSON_ARRAYAGG(
                    JSON_OBJECT(
                        'id', prog.id,
                        'title', prog.title,
                        'thumbnail', (SELECT pathname FROM files WHERE id = prog.thumbnail_id),
                        'thumbnails', (SELECT JSON_ARRAYAGG(pathname) FROM files WHERE original_file_id = prog.thumbnail_id),
                        'intro', (SELECT pathname FROM files WHERE id = prog.intro_id),
                        'num_lectures', (SELECT COUNT(*) FROM lectures WHERE program_id = prog.id),
                        'exercise', (SELECT title FROM exercises e INNER JOIN program_exercises pe ON e.id = pe.exercise_id WHERE pe.program_id=prog.id),
                        'type', prog.type
                    )
                ) AS related_programs,
                DATE_FORMAT(prod.released_at, '%Y-%m-%d %H:%i:%s') AS released_at,
                CASE
                    WHEN prod.released_at > NOW() THEN 'comming'
                    ELSE 'released'
                END AS status,
                prod.is_hidden,
                e.title AS exercises
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
            LEFT OUTER JOIN
                    product_exercises pe
                    ON prod.id = pe.product_id
            LEFT OUTER JOIN
                    exercises e
                        ON pe.exercise_id = e.id
            WHERE prod.is_hidden = 1
            AND prod.deleted_at IS NULL
            GROUP BY prod.id, prog.id"""
    else:
        sql = f"""
            SELECT
               prod.id,
               prod.type,
               prod.code,
               prod.title as title,
               prod.description,
               b.title as brandTitle,
               prod.original_price as original_price,
               prod.price as price,
               CASE
                   WHEN (IFNULL(prod.stocks, 0) - IFNULL((SELECT SUM(qty) FROM order_products WHERE product_id=prod.id), 0)) <= 0 THEN 0
                   WHEN (IFNULL(prod.stocks, 0) - IFNULL((SELECT SUM(qty) FROM order_products WHERE product_id=prod.id), 0)) > 0 THEN (IFNULL(prod.stocks, 0) - IFNULL((SELECT SUM(qty) FROM order_products WHERE product_id=prod.id), 0))
               END AS stock,
               (
                   SELECT
                       f2.pathname
                   FROM
                        files f2
                    INNER JOIN product_images pi2
                   ON pi2.file_id = f2.id
                    WHERE pi2.type='thumbnail' AND pi2.product_id=prod.id
                ) AS thumbnail,
        --        (
        --            SELECT JSON_ARRAYAGG(pathname) FROM files
        --                INNER JOIN product_images
        --                     ON product_images.file_id = files.original_file_id
        --            WHERE product_images.product_id = prod.id AND product_images.type = 'thumbnail'
        --        ) AS thumbnails,
               (
                   SELECT JSON_ARRAYAGG(pathname) FROM files
                       INNER JOIN product_images
                           ON product_images.file_id = files.id
                   WHERE product_images.type = 'detail' AND product_images.product_id = prod.id
               ) AS details,
        --        (
        --            SELECT JSON_ARRAYAGG(pathname) FROM files
        --                INNER JOIN product_images
        --                     ON product_images.file_id = files.original_file_id
        --            WHERE product_images.type = 'detail' AND product_images.product_id = prod.id
        --        ) AS detail_thumbnails,
               JSON_ARRAYAGG(
                    JSON_OBJECT(
                        'id', prog.id,
                        'title', prog.title,
                        'thumbnail', (SELECT pathname FROM files WHERE id = prog.thumbnail_id),
                        'thumbnails', (SELECT JSON_ARRAYAGG(pathname) FROM files WHERE original_file_id = prog.thumbnail_id),
                        'intro', (SELECT pathname FROM files WHERE id = prog.intro_id),
                        'num_lectures', (SELECT COUNT(*) FROM lectures WHERE program_id = prog.id),
                        'exercise', (SELECT title FROM exercises e INNER JOIN program_exercises pe ON e.id = pe.exercise_id WHERE pe.program_id=prog.id),
                        'type', prog.type
                    )
                ) AS related_programs,
                DATE_FORMAT(prod.released_at, '%Y-%m-%d %H:%i:%s') AS released_at,
                CASE
                    WHEN prod.released_at > NOW() THEN 'comming'
                    ELSE 'released'
                END AS status,
                prod.is_hidden,
                e.title AS exercises
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
            LEFT OUTER JOIN
                    product_exercises pe
                    ON prod.id = pe.product_id
            LEFT OUTER JOIN
                    exercises e
                        ON pe.exercise_id = e.id
            WHERE prod.type='{parameters[0]}'
--                 AND prod.is_hidden = 1
            AND prod.deleted_at IS NULL
            GROUP BY prod.id, prog.id"""
    cursor.execute(sql)
    result = cursor.fetchall()
    connection.close()

    if query_result_is_none(result):
        result_dict = {}
        return json.dumps(result_dict, ensure_ascii=False), 200

    products_df = pd.DataFrame(result, columns=['id', 'type', 'code',
                                                'title', 'description', 'brandTitle',
                                                'original_price', 'price', 'stocks',
                                                'thumbnail', 'details', 'related_programs',
                                                'released_at', 'status', 'is_hidden', 'exercises'])
    # products_df = pd.DataFrame(result, columns=['id', 'type', 'code',
    #                                             'title', 'description', 'brandTitle',
    #                                             'original_price', 'price', 'stocks',
    #                                             'thumbnail', 'thumbnails', 'details', 'detail_thumbnails',
    #                                             'related_programs', 'released_at', 'status',
    #                                             'is_hidden', 'exercises'])
    try:
        products_df['details'] = products_df['details'].apply(lambda x: [] if x is None else json.loads(x))
        # products_df['detail_thumbnails'] = products_df['detail_thumbnails'].apply(lambda x: [] if x is None else json.loads(x))
    except:
        result_dict = json.loads(products_df.to_json(orient='records'))  # Array type으로 가고있음
        return json.dumps(result_dict, ensure_ascii=False), 200
    # try:
    #     products_df['thumbnails'] = products_df['thumbnails'].apply(lambda x: [] if x is None else json.loads(x))
    # except:
    #     result_dict = json.loads(products_df.to_json(orient='records'))  # Array type으로 가고있음
    #     return json.dumps(result_dict, ensure_ascii=False), 200
    try:
        products_df['related_programs'] = products_df['related_programs'].apply(lambda x: json.loads(x))
        products_df['related_programs'] = products_df['related_programs'].apply(lambda x: list({data['id']: data for data in x}.values()))
        products_df['related_programs'] = products_df['related_programs'].apply(lambda x: [] if x[0]['id'] is None else x)

        products_df = products_df.sort_values(by=['stocks', 'price'], ascending=False)
        # products_df = products_df.sort_values(by=['stocks'], ascending=False)
        sorter = ['released', 'comming', 'sold_out']
        products_df.status = products_df.status.astype('category')
        products_df.status.cat.set_categories(sorter, inplace=True)
    except:
        result_dict = json.loads(products_df.to_json(orient='records'))  # Array type으로 가고있음

        """정렬
        (1) status == 'on_sale' and stocks > 0 : 잔여수량 순 -> 가격 높은 순
        (2) status == 'future'
        (3) stocks < 0
        """
        result_dict = sorted(result_dict, key=lambda x: (x['stocks'], x['price']), reverse=True)

        return json.dumps(result_dict, ensure_ascii=False), 200

    result_dict = json.loads(products_df.to_json(orient='records'))  # Array type으로 가고있음
    return json.dumps(result_dict, ensure_ascii=False), 200


@api.route('/products/<product_id>', methods=['GET'])
def read_a_product(product_id: int):
    ip = request.headers["X-Forwarded-For"]
    endpoint = API_ROOT + url_for('api.read_a_product', product_id=product_id)
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
        SELECT DISTINCT
           prod.id,
           prod.type,
           prod.code,
           prod.title as title,
           prod.description,
           b.title as brandTitle,
           prod.original_price as original_price,
           prod.price as price,
           CASE
               WHEN (IFNULL(prod.stocks, 0) - IFNULL((SELECT SUM(qty) FROM order_products WHERE product_id=prod.id), 0)) <= 0 THEN 0
               WHEN (IFNULL(prod.stocks, 0) - IFNULL((SELECT SUM(qty) FROM order_products WHERE product_id=prod.id), 0)) > 0 THEN (IFNULL(prod.stocks, 0) - IFNULL((SELECT SUM(qty) FROM order_products WHERE product_id=prod.id), 0))
           END AS stock,
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
                    'intro', (SELECT pathname FROM files WHERE id = prog.intro_id),                    
                    'num_lectures', (SELECT COUNT(*) FROM lectures WHERE program_id = prog.id),
                    'exercise', (SELECT title FROM exercises e INNER JOIN program_exercises pe ON e.id = pe.exercise_id WHERE pe.program_id=prog.id),
                    'type', prog.type
                )) AS related_programs,
            DATE_FORMAT(prod.released_at, '%Y-%m-%d %H:%i:%s') AS released_at,
            CASE
                WHEN prod.released_at > NOW() THEN 'comming'
                ELSE 'released'
            END AS status,
            prod.is_hidden,
            e.title AS exercises            
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
        LEFT OUTER JOIN
                product_exercises pe
                ON prod.id = pe.product_id
        LEFT OUTER JOIN
                exercises e
                    ON pe.exercise_id = e.id            
        WHERE prod.id = {product_id}
--         AND prod.is_hidden = 1
        AND prod.deleted_at IS NULL
        GROUP BY prod.id"""
    cursor.execute(sql)

    result = cursor.fetchall()
    connection.close()
    if query_result_is_none(result) is True:
        result_dict = {}
        return json.dumps(result_dict, ensure_ascii=False), 200

    products_df = pd.DataFrame(result, columns=['id', 'type', 'code',
                                                'title', 'description', 'brandTitle',
                                                'original_price', 'price', 'stocks',
                                                'thumbnail', 'details', 'related_programs',
                                                'released_at', 'status', 'is_hidden', 'exercises'])
    # products_df = pd.DataFrame(result, columns=['id', 'type', 'code',
    #                                             'title', 'description', 'brandTitle',
    #                                             'original_price', 'price', 'stocks',
    #                                             'thumbnail', 'thumbnails', 'details', 'detail_thumbnails',
    #                                             'related_programs', 'released_at', 'status',
    #                                             'is_hidden', 'exercises'])
    try:
        products_df['details'] = products_df['details'].apply(lambda x: [] if x is None else json.loads(x))
        # products_df['detail_thumbnails'] = products_df['detail_thumbnails'].apply(lambda x: [] if x is None else json.loads(x))
    except:
        # 썸네일만 없는 경우.
        result_dict = json.loads(products_df.to_json(orient='records'))[0]  # Array type으로 가고있음
        return json.dumps(result_dict, ensure_ascii=False), 200
    # try:
    #     products_df['thumbnails'] = products_df['thumbnails'].apply(lambda x: [] if x is None else json.loads(x))
    # except:
    #     result_dict = json.loads(products_df.to_json(orient='records'))  # Array type으로 가고있음
    #     return json.dumps(result_dict, ensure_ascii=False), 200
    try:
        products_df['related_programs'] = products_df['related_programs'].apply(lambda x: json.loads(x))
        products_df['related_programs'] = products_df['related_programs'].apply(lambda x: list({data['id']: data for data in x}.values()))
        products_df['related_programs'] = products_df['related_programs'].apply(lambda x: [] if x[0]['id'] is None else x)
    except:
        result_dict = json.loads(products_df.to_json(orient='records'))[0]  # Array type으로 가고있음
        return json.dumps(result_dict, ensure_ascii=False), 200

    result_list = json.loads(products_df.to_json(orient='records'))
    if len(result_list) == 0:
        result_dict = {}
    else:
        result_dict = result_list[0]

    return json.dumps(result_dict, ensure_ascii=False), 200


