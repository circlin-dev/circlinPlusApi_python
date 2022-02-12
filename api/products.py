from global_things.constants import API_ROOT
from global_things.functions.slack import slack_error_notification, slack_purchase_notification
from global_things.functions.general import login_to_db, check_session, query_result_is_none
from global_things.functions.purchase import get_import_access_token
from . import api
import ast
from flask import jsonify, url_for, request
import json
import requests
import pandas as pd
from pypika import MySQLQuery as Query, Criterion, Interval, Table, Field, Order, functions as fn


@api.route('/products', methods=['GET'])
def read_products():
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    endpoint = API_ROOT + url_for('api.read_products')
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
        slack_error_notification(user_ip=ip, user_id=0, api=endpoint, error_log=result['error'])
        return json.dumps(result, ensure_ascii=False), 500

    query_parameter = request.args.to_dict()  # type: equipment(기구), starterkit(스타터키트), item(상품)
    parameters = []
    for key in query_parameter.keys():
        parameters.append(request.args[key].strip())

    cursor = connection.cursor()
    if parameters == [] or len(parameters) == 0:
        """GET everything in 'products' table. => Don't use 'where' clause in sql."""
        # sql = f"""
        #     SELECT
        #        products.id,
        #        products.type,
        #        products.code,
        #        products.title as name,
        #        p.description, '',
        #        brands.title as brand_name,
        #        products.price as price_origin,
        #        products.sales_price as price_sales,
        #        IFNULL(p.stocks, 0),
        #        products.thumbnail,
        #        JSON_ARRAYAGG(IFNULL(files.pathname, '')) AS details
        #     FROM
        #         products
        #     INNER JOIN
        #         product_images
        #     ON product_images.product_id = products.id
        #     INNER JOIN
        #         files f
        #     ON f.id = pi.file_id
        #     INNER JOIN
        #         brands
        #     ON products.brand_id = brands.id
        #     WHERE products.`type`='{parameters[0]}'
        #     GROUP BY products.id"""
        pass

    # related_program이 복수이면 JSON_ARRAYAGG()로 합치고, GROUP BY에 prog.id 또는 pp.program_id 추가해야 할듯.
    sql = f"""
        SELECT
           p.id,
           p.type,
           p.code,
           p.title as name,
           p.description,
           b.title as brand_name,
           p.price as price_origin,
           p.sales_price as price_sales,
           IFNULL(p.stocks, 0),
           p.thumbnail,
           JSON_ARRAYAGG(IFNULL(f.pathname, '')) AS details,
           JSON_ARRAYAGG(IFNULL(prog.title, '')) AS related_program
        FROM
            products p
        INNER JOIN
                brands b
            ON b.id = p.brand_id
        LEFT OUTER JOIN
                product_images pi
            ON pi.product_id = p.id
        LEFT OUTER JOIN
                files f
            ON f.id = pi.file_id
        LEFT OUTER JOIN
                program_products pp
            ON p.id = pp.product_id
        LEFT OUTER JOIN
                programs prog
            ON prog.id = pp.program_id
        WHERE p.`type` = 'item'
        GROUP BY p.id"""
    cursor.execute(sql)
    result = cursor.fetchall()

    if query_result_is_none(result):
        connection.close()
        result_dict = {}
        return json.dumps(result_dict, ensure_ascii=False), 200

    products_df = pd.DataFrame(result, columns=['id', 'type', 'code',
                                                'name', 'description', 'brand_name',
                                                'price_origin', 'price_sales', 'quantity',
                                                'thumbnail', 'details', 'related_program'])
    try:
        products_df['details'] = products_df['details'].apply(lambda x: [ast.literal_eval(el) for el in (list(set(x.strip('][').split(', '))))])
        products_df['details'] = products_df['details'].apply(lambda x: sorted(x, key=lambda y: y.split('/')[-1].split('_')[-1].split('.')[0]))
        products_df['details'] = products_df['details'].apply(lambda x: [] if x[0] == "" else x)
    except:
        connection.close()
        result_dict = json.loads(products_df.to_json(orient='records'))  # Array type으로 가고있음
        return json.dumps(result_dict, ensure_ascii=False), 200
    try:
        products_df['related_program'] = products_df['related_program'].apply(lambda x: [ast.literal_eval(el) for el in json.loads(x)])
        products_df['related_program'] = products_df['related_program'].apply(lambda x: [] if x[0] == "" else x)
    except:
        connection.close()
        result_dict = json.loads(products_df.to_json(orient='records'))  # Array type으로 가고있음
        return json.dumps(result_dict, ensure_ascii=False), 200


    connection.close()
    result_dict = json.loads(products_df.to_json(orient='records'))  # Array type으로 가고있음
    return json.dumps(result_dict, ensure_ascii=False), 200


@api.route('/products/<product_id>', methods=['GET'])
def read_a_product(product_id: int):
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
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
        slack_error_notification(user_ip=ip, user_id=0, api=endpoint, error_log=result['error'])
        return json.dumps(result, ensure_ascii=False), 500

    cursor = connection.cursor()

    # related_program이 복수이면 JSON_ARRAYAGG()로 합치고, GROUP BY에 prog.id 또는 pp.program_id 추가해야 할듯.
    sql = f"""
        SELECT
           prod.id,
           prod.type,
           prod.code,
           prod.title as name,
           prod.description,
           b.title as brand_name,
           prod.price as price_origin,
           prod.sales_price as price_sales,
           IFNULL(prod.stocks, 0),
           prod.thumbnail,
           JSON_ARRAYAGG(IFNULL(f.pathname, '')) AS details,
           JSON_ARRAYAGG(IFNULL(prog.title, '')) AS related_program
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
        result_dict = {}
        return json.dumps(result_dict, ensure_ascii=False), 200

    products_df = pd.DataFrame(result, columns=['id', 'type', 'code',
                                                'name', 'description', 'brand_name',
                                                'price_origin', 'price_sales', 'quantity',
                                                'thumbnail', 'details', 'related_program'])
    try:
        products_df['details'] = products_df['details'].apply(lambda x: [ast.literal_eval(el) for el in list(set(x.strip('][').split(', ')))])
        products_df['details'] = products_df['details'].apply(lambda x: sorted(x, key=lambda y: y.split('/')[-1].split('_')[-1].split('.')[0]))
        products_df['details'] = products_df['details'].apply(lambda x: [] if x[0] == "" else x)
    except:
        connection.close()
        # 썸네일만 없는 경우.
        result_dict = json.loads(products_df.to_json(orient='records'))[0]  # Array type으로 가고있음
        return json.dumps(result_dict, ensure_ascii=False), 200
    try:
        #products_df['related_program'] = products_df['related_program'].apply(lambda x: [ast.literal_eval(el) for el in list(set(list(set(x.strip('][').split('", ')))))])
        products_df['related_program'] = products_df['related_program'].apply(lambda x: [ast.literal_eval(el) for el in json.loads(x)])
        products_df['related_program'] = products_df['related_program'].apply(lambda x: [] if x[0] == "" else x)
    except:
        connection.close()
        result_dict = json.loads(products_df.to_json(orient='records'))[0]  # Array type으로 가고있음
        return json.dumps(result_dict, ensure_ascii=False), 200
    connection.close()
    result_dict = json.loads(products_df.to_json(orient='records'))[0]  # Array type으로 가고있음
    return json.dumps(result_dict, ensure_ascii=False), 200


