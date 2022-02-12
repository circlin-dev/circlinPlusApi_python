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
        #        products.description,
        #        brands.title as brand_name,
        #        products.price as price_origin,
        #        products.sales_price as price_sales,
        #        products.stocks,
        #        products.thumbnail,
        #        JSON_ARRAYAGG(product_images.url) AS details
        #     FROM
        #         products
        #     INNER JOIN
        #         product_images
        #     ON product_images.product_id = products.id
        #     INNER JOIN
        #         brands
        #     ON products.brand_id = brands.id
        #     WHERE products.`type`='{parameters[0]}'
        #     GROUP BY products.id"""
        pass

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
           p.stocks,
           p.thumbnail,
           JSON_ARRAYAGG(f.pathname) AS details
        FROM
            products p
        INNER JOIN 
                product_images pi
            ON pi.product_id = p.id
        INNER JOIN 
                files f
            ON f.id = pi.file_id
        INNER JOIN
                brands b
            ON p.brand_id = b.id
        WHERE p.`type`='{parameters[0]}'
        GROUP BY p.id"""
    cursor.execute(sql)

    products_df = pd.DataFrame(cursor.fetchall(), columns=['id', 'type', 'code',
                                                           'name', 'description', 'brand_name',
                                                           'price_origin', 'price_sales', 'quantity',
                                                           'thumbnail', 'details'])
    products_df['details'] = products_df['details'].apply(lambda x: [ast.literal_eval(el) for el in list(set(x.strip('][').split(', ')))])
    products_df['details'] = products_df['details'].apply(lambda x: sorted(x, key=lambda y: y.split('/')[-1].split('_')[-1].split('.')[0]))

    result_dict = json.loads(products_df.to_json(orient='records'))

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
           p.stocks,
           p.thumbnail,
           JSON_ARRAYAGG(pi.url) AS details
        FROM
            products p
        INNER JOIN
                product_images pi
            ON pi.product_id = p.id
        INNER JOIN 
                files f
            ON f.id = pi.file_id        
        INNER JOIN
                brands b
            ON p.brand_id = b.id
        WHERE p.id = {product_id}"""
    cursor.execute(sql)

    result = cursor.fetchall()
    if query_result_is_none(result) is True:
        connection.close()
        result_dict = {}
        return json.dumps(result_dict, ensure_ascii=False), 200

    products_df = pd.DataFrame(result, columns=['id', 'type', 'code',
                                                'name', 'description', 'brand_name',
                                                'price_origin', 'price_sales', 'quantity',
                                                'thumbnail', 'details'])
    products_df['details'] = products_df['details'].apply(lambda x: [ast.literal_eval(el) for el in list(set(x.strip('][').split(', ')))])
    products_df['details'] = products_df['details'].apply(lambda x: sorted(x, key=lambda y: y.split('/')[-1].split('_')[-1].split('.')[0]))

    connection.close()
    result_dict = json.loads(products_df.to_json(orient='records'))[0]  # Array type으로 가고있음
    return json.dumps(result_dict, ensure_ascii=False), 200


