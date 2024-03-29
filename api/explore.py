from global_things.constants import API_ROOT
from global_things.error_handler import HandleException
from global_things.functions.explore import make_explore_query, filter_dataframe, make_query_to_find_related_terms, make_query_get_every_titles
from global_things.functions.general import login_to_db, check_user_token, query_result_is_none
from . import api
from flask import url_for, request
import json
import pandas as pd
from pypika import MySQLQuery as Query, Criterion, Table, Order, functions as fn
from soynlp.hangle import jamo_levenshtein


@api.route('/explore', methods=['POST'])
def explore():
    """
    header: Authorization
    body: filter{exercises, purposes, equipments}, sort_by, word,
    """
    ip = request.headers["X-Forwarded-For"]
    endpoint = API_ROOT + url_for('api.explore')
    user_token = request.headers.get('Authorization')
    """Define tables required to execute SQL."""
    search_logs = Table('search_logs')

    parameters = json.loads(request.get_data(), encoding='utf-8')
    try:
        user_id = parameters['user_id']
        filter_list_exercises = parameters['filter']['exercise']  # default: Everything
        filter_list_purposes = parameters['filter']['purposes']  # default: everything
        filter_list_equipments = parameters['filter']['equipments']
        sort_by = parameters["sort_by"]
        word_for_search = parameters["word"].strip()
    except Exception as e:
        raise HandleException(user_ip=ip,
                              api=endpoint,
                              error_message=f'KeyError: {str(e)}',
                              method=request.method,
                              status_code=400,
                              payload=json.dumps(parameters, ensure_ascii=False),
                              result=False)

    connection = login_to_db()
    cursor = connection.cursor()
    verify_user = check_user_token(cursor, user_token)
    if verify_user['result'] is False:
        connection.close()
        result = {
            'result': False,
            'error': 'Unauthorized user.'
        }
        return json.dumps(result), 401
    # user_id = verify_user['user_id']
    # user_nickname = verify_user['user_nickname']

    result_list = []
    if word_for_search == "" or len(word_for_search) == 0 or word_for_search is None:
        pass
    else:
        query_program, query_coach, query_exercise, query_equipment = make_explore_query(word_for_search, user_id, sort_by)

        try:
            cursor.execute(query_program)
            programs_by_program = pd.DataFrame(cursor.fetchall(), columns=['program_id', 'created_at', 'title',
                                                                           'exercise', 'equipments', 'purposes',
                                                                           'thumbnail', 'thumbnails', 'num_lectures',
                                                                           'num_completed_lectures', 'type'])
            program_list_by_program = filter_dataframe(filter_list_exercises, filter_list_purposes, filter_list_equipments, programs_by_program)

            cursor.execute(query_coach)
            programs_by_coach = pd.DataFrame(cursor.fetchall(), columns=['program_id', 'created_at', 'title',
                                                                         'exercise', 'equipments', 'purposes',
                                                                         'thumbnail', 'thumbnails', 'num_lectures',
                                                                         'num_completed_lectures', 'type'])
            program_list_by_coach = filter_dataframe(filter_list_exercises, filter_list_purposes, filter_list_equipments, programs_by_coach)

            cursor.execute(query_exercise)
            programs_by_exercise = pd.DataFrame(cursor.fetchall(), columns=['program_id', 'created_at', 'title',
                                                                            'exercise', 'equipments', 'purposes',
                                                                            'thumbnail', 'thumbnails', 'num_lectures',
                                                                            'num_completed_lectures', 'type'])
            program_list_by_exercise = filter_dataframe(filter_list_exercises, filter_list_purposes, filter_list_equipments, programs_by_exercise)

            cursor.execute(query_equipment)
            programs_by_equipment = pd.DataFrame(cursor.fetchall(), columns=['program_id', 'created_at', 'title',
                                                                             'exercise', 'equipments', 'purposes',
                                                                             'thumbnail', 'thumbnails', 'num_lectures',
                                                                             'num_completed_lectures', 'type'])
            program_list_by_equipment = filter_dataframe(filter_list_exercises, filter_list_purposes, filter_list_equipments, programs_by_equipment)

            search_total = program_list_by_program + program_list_by_coach + program_list_by_exercise + program_list_by_equipment
            for element in search_total:
                if element not in result_list:
                    result_list.append(element)
        except Exception as e:
            connection.rollback()
            connection.close()
            raise HandleException(user_ip=ip,
                                  user_id=user_id,
                                  api=endpoint,
                                  error_message=str(e),
                                  query=f'{query_program} | {query_coach} | {query_exercise}  | {query_equipment}',
                                  method=request.method,
                                  status_code=500,
                                  payload=None,
                                  result=False)

    # Store search logs.
    ids = []
    if len(result_list) > 0:
        for data in result_list:
            ids.append(data['id'])
    else:
        pass
    json_data = json.dumps({"program_id": ids}, ensure_ascii=False)
    sql = Query.into(
        search_logs
    ).columns(
        'user_id', 'search_term', 'search_result'
    ).insert(
        user_id, word_for_search, json_data
    ).get_sql()

    try:
        cursor.execute(sql)
        connection.commit()
        connection.close()
    except Exception as e:
        connection.rollback()
        connection.close()
        raise HandleException(user_ip=ip,
                              user_id=user_id,
                              api=endpoint,
                              error_message=str(e),
                              query=sql,
                              method=request.method,
                              status_code=500,
                              payload=None,
                              result=False)
    result_dict = {
        "result": True,
        "search_results": result_list
    }

    return json.dumps(result_dict, ensure_ascii=False), 200


@api.route('/explore/related', methods=['GET'])
def get_related_terms_list():
    ip = request.headers["X-Forwarded-For"]
    endpoint = API_ROOT + url_for('api.get_related_terms_list')
    user_token = request.headers.get('Authorization')

    query_parameter = request.args.to_dict()
    word = ''
    for key in query_parameter.keys():
        if key == 'word':
            word += request.args[key].strip()
    related_programs_list = []
    related_coaches_list = []
    related_exercises_list = []
    related_equipments_list = []

    connection = login_to_db()
    cursor = connection.cursor()
    verify_user = check_user_token(cursor, user_token)
    if verify_user['result'] is False:
        connection.close()
        message = 'No token at request header.' if user_token is None else 'Unauthorized user.'
        result = {
            'result': False,
            'message': message
        }
        return json.dumps(result, ensure_ascii=False), 401
    # user_id = verify_user['user_id']
    # user_nickname = verify_user['user_nickname']

    if word == "" or len(word) == 0 or word is None:
        pass
    else:
        query_program, query_coach, query_exercise, query_equipment = make_query_to_find_related_terms(word)
        cursor.execute(query_program)
        related_programs = cursor.fetchall()
        cursor.execute(query_coach)
        related_coaches = cursor.fetchall()
        cursor.execute(query_exercise)
        related_exercises = cursor.fetchall()
        cursor.execute(query_equipment)
        related_equipments = cursor.fetchall()

        for program in related_programs:
            program_dict = {'id': program[0], 'value': program[1]}
            related_programs_list.append(program_dict)

        for coach in related_coaches:
            coach_dict = {'id': coach[0], 'value': coach[1]}
            related_coaches_list.append(coach_dict)

        for exercise in related_exercises:
            exercise_dict = {'id': exercise[0], 'value': exercise[1]}
            related_exercises_list.append(exercise_dict)

        for equipment in related_equipments:
            exercise_dict = {'id': equipment[0], 'value': equipment[1]}
            related_equipments_list.append(exercise_dict)

    all_searched_result = related_programs_list + related_coaches_list + related_exercises_list + related_equipments_list

    if len(all_searched_result) == 0 and word != '' and len(word) > 0:
        """
        MySQL LIKE 연산자로 추려낸 연관검색어의 결과가 0건일 경우, 
        각 카테고리의 모든 목록 이름과 검색어의 형태적 유사도를 자모단위로 쪼개 비교하여, 
        가장 비슷한 순(=jamo_levenshtein() 수치가 낮은 순)으로 정렬하여 반환한다.
        """
        query_programs, query_coaches, query_exercises, query_equipments = make_query_get_every_titles()
        cursor.execute(query_programs)
        programs = cursor.fetchall()
        cursor.execute(query_coaches)
        coaches = cursor.fetchall()
        cursor.execute(query_exercises)
        exercises = cursor.fetchall()
        cursor.execute(query_equipments)
        equipments = cursor.fetchall()

        connection.close()

        for program in programs:
            program_dict = {'id': program[0], 'value': program[1], 'similarity': jamo_levenshtein(word, program[1])}
            related_programs_list.append(program_dict)

        for coach in coaches:
            coach_dict = {'id': coach[0], 'value': coach[1], 'similarity': jamo_levenshtein(word, coach[1])}
            related_coaches_list.append(coach_dict)

        for exercise in exercises:
            exercise_dict = {'id': exercise[0], 'value': exercise[1], 'similarity': jamo_levenshtein(word, exercise[1])}
            related_exercises_list.append(exercise_dict)

        for equipment in equipments:
            equipment_dict = {'id': equipment[0], 'value': equipment[1], 'similarity': jamo_levenshtein(word, equipment[1])}
            related_equipments_list.append(equipment_dict)

        related_programs_list = sorted(related_programs_list, key=lambda x: x['similarity'], reverse=True)[:3]
        related_coaches_list = sorted(related_coaches_list, key=lambda x: x['similarity'], reverse=True)[:3]
        related_exercises_list = sorted(related_exercises_list, key=lambda x: x['similarity'], reverse=True)[:3]
        related_equipments_list = sorted(related_equipments_list, key=lambda x: x['similarity'], reverse=True)[:3]
        all_searched_result = sorted(related_programs_list + related_coaches_list + related_exercises_list + related_equipments_list, key=lambda x: x['similarity'], reverse=True)

    result_dict = {
        "result": True,
        "related_terms": {
            "all": all_searched_result,
            "programs": related_programs_list,
            "coaches": related_coaches_list,
            "exercises": related_exercises_list,
            "equipments": related_equipments_list
        }
    }

    return json.dumps(result_dict, ensure_ascii=False), 200


@api.route('/explore/log/<user_id>', methods=['DELETE', 'GET'])
def explore_log(user_id: int):
    ip = request.headers["X-Forwarded-For"]
    endpoint = API_ROOT + url_for('api.explore_log', user_id=user_id)
    user_token = request.headers.get('Authorization')

    """Define tables required to execute SQL."""
    search_logs = Table('search_logs')

    connection = login_to_db()
    cursor = connection.cursor()

    verify_user = check_user_token(cursor, user_token)
    if verify_user['result'] is False:
        connection.close()
        message = 'No token at request header.' if user_token is None else 'Unauthorized user.'
        result = {
            'result': False,
            'message': message
        }
        return json.dumps(result, ensure_ascii=False), 401
    verified_user_id = verify_user['user_id']

    if request.method == 'GET':  # 검색 기록 조회
        sql = Query.from_(
            search_logs
        ).select(
            search_logs.id,
            search_logs.search_term
        ).where(
            Criterion.all([
                search_logs.user_id == verified_user_id,
                search_logs.deleted_at.isnull()
            ])
        ).groupby(
            search_logs.search_term
        ).orderby(
            search_logs.created_at, order=Order.desc
        ).get_sql()
        try:
            cursor.execute(sql)
            search_records = cursor.fetchall()
            connection.close()
        except Exception as e:
            connection.close()
            result = {
                'result': False,
                'error': f'Cannot find requested search record: {str(e)}'
            }
            return json.dumps(result, ensure_ascii=False), 400

        if query_result_is_none(search_records) is True:
            result = {
                'result': True,
                'logs': []
            }
            return json.dumps(result, ensure_ascii=False), 200

        logs = []
        for log in search_records:
            data = {'id': log[0], 'searched_word': log[1]}
            logs.append(data)

        result_dict = {
            'result': True,
            'logs': logs
        }
        return json.dumps(result_dict, ensure_ascii=False), 200
    elif request.method == 'DELETE':  # 검색 기록 삭제
        query_parameter = request.args.to_dict()
        word_to_delete = ''
        for key in query_parameter.keys():
            if key == 'word':
                word_to_delete += request.args[key].strip()

        if word_to_delete != '' and word_to_delete is not None:
            # 단건 삭제
            """
            만약 검색기록 조회 결과를 중복을 제거해서 보내준다면, id만으로 삭제하면 다음 번에 삭제한 단어를 또 보게 될 수 있다.
            따라서 아래와 같이 search_log_id가 아닌 user_id와 search_term을 함께 조회하여, 중복되는 단어를 전부 삭제 처리한다.
            """
            sql = Query.update(
                search_logs
            ).set(
                search_logs.deleted_at, fn.Now()
            ).where(
                Criterion.all([
                    search_logs.search_term == word_to_delete,
                    search_logs.user_id == verified_user_id,
                    search_logs.deleted_at.isnull()
                ])
            ).get_sql()
            try:
                cursor.execute(sql)
                connection.commit()
                connection.close()
                result_dict = {
                    'result': True,
                    'message': f"Successfully deleted the requested search term({word_to_delete})."
                }
                return json.dumps(result_dict, ensure_ascii=False), 200
            except Exception as e:
                connection.rollback()
                connection.close()
                result = {
                    'result': False,
                    'error': f'Cannot delete the requested search term: {str(e)}'
                }
                return json.dumps(result, ensure_ascii=False), 400
        else:
            # 전체 삭제
            """
            만약 검색기록 조회 결과를 중복을 제거해서 보내준다면, id만으로 삭제하면 다음 번에 삭제한 단어를 또 보게 될 수 있다.
            따라서 아래와 같이 search_log_id가 아닌 user_id와 search_term을 함께 조회하여, 중복되는 단어를 전부 삭제 처리한다.
            """
            sql = Query.update(
                search_logs
            ).set(
                search_logs.deleted_at, fn.Now()
            ).where(
                Criterion.all([
                    search_logs.user_id == verified_user_id,
                    search_logs.deleted_at.isnull()
                ])
            ).get_sql()
            try:
                cursor.execute(sql)
                connection.commit()
                connection.close()
            except Exception as e:
                connection.rollback()
                connection.close()
                result = {
                    'result': False,
                    'error': f'Cannot delete the requested whole search log: {str(e)}'
                }
                return json.dumps(result, ensure_ascii=False), 400
            result_dict = {
                'result': True,
                'message': f"Successfully deleted the requested whole search log({word_to_delete})."
            }
            return json.dumps(result_dict, ensure_ascii=False), 200
