from global_things.constants import API_ROOT
from global_things.functions.slack import slack_error_notification
from global_things.functions.explore import make_explore_query, filter_dataframe, make_query_to_find_related_terms, make_query_get_every_titles
from global_things.functions.general import login_to_db, check_session, query_result_is_none
from . import api
from flask import url_for, request
import json
import pandas as pd
from soynlp.hangle import jamo_levenshtein


@api.route('/explore', methods=['POST'])
def explore():
    """
    header: Authorization
    body: filter{exercises, purposes, equipments}, sort_by, word,
    """
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    endpoint = API_ROOT + url_for('api.explore')
    # token = request.headers['Authorization']
    parameters = json.loads(request.get_data(), encoding='utf-8')

    user_id = parameters['user_id']
    filter_list_exercises = parameters['filter']['exercise']  # default: Everything
    filter_list_purposes = parameters['filter']['purposes']  # default: everything
    filter_list_equipments = parameters['filter']['equipments']
    sort_by = parameters["sort_by"]
    word_for_search = parameters["word"].strip()

    try:
        connection = login_to_db()
    except Exception as e:
        error = str(e)
        result = {
            'result': False,
            'error': f'Server Error while connecting to DB: {error}'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
        return json.dumps(result, ensure_ascii=False), 500

    cursor = connection.cursor()
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
                                                                           'num_completed_lectures'])
            program_list_by_program = filter_dataframe(filter_list_exercises, filter_list_purposes, filter_list_equipments, programs_by_program)

            cursor.execute(query_coach)
            programs_by_coach = pd.DataFrame(cursor.fetchall(), columns=['program_id', 'created_at', 'title',
                                                                         'exercise', 'equipments', 'purposes',
                                                                         'thumbnail', 'thumbnails', 'num_lectures',
                                                                         'num_completed_lectures'])
            program_list_by_coach = filter_dataframe(filter_list_exercises, filter_list_purposes, filter_list_equipments, programs_by_coach)

            cursor.execute(query_exercise)
            programs_by_exercise = pd.DataFrame(cursor.fetchall(), columns=['program_id', 'created_at', 'title',
                                                                            'exercise', 'equipments', 'purposes',
                                                                            'thumbnail', 'thumbnails', 'num_lectures',
                                                                            'num_completed_lectures'])
            program_list_by_exercise = filter_dataframe(filter_list_exercises, filter_list_purposes, filter_list_equipments, programs_by_exercise)

            cursor.execute(query_equipment)
            programs_by_equipment = pd.DataFrame(cursor.fetchall(), columns=['program_id', 'created_at', 'title',
                                                                             'exercise', 'equipments', 'purposes',
                                                                             'thumbnail', 'thumbnails', 'num_lectures',
                                                                             'num_completed_lectures'])
            program_list_by_equipment = filter_dataframe(filter_list_exercises, filter_list_purposes, filter_list_equipments, programs_by_equipment)

            search_total = program_list_by_program + program_list_by_coach + program_list_by_exercise + program_list_by_equipment
            for element in search_total:
                if element not in result_list:
                    result_list.append(element)
        except Exception as e:
            connection.rollback()
            connection.close()
            error = str(e)
            result = {
                'result': False,
                'error': f'Server Error while executing INSERT query(explore): {error}'
            }

    # Store search logs.
    ids = []
    if len(result_list) > 0:
        for data in result_list:
            ids.append(data['id'])
    else:
        pass
    json_data = json.dumps({"program_id": ids}, ensure_ascii=False)
    query = f"""INSERT INTO search_logs(user_id, search_term, search_result) VALUES({user_id}, '{word_for_search}', '{json_data}')"""

    try:
        cursor.execute(query)
        connection.commit()
    except Exception as e:
        connection.rollback()
        connection.close()
        error = str(e)
        result = {
            'result': False,
            'error': f'Server Error while executing INSERT query(explore): {error}'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
        return json.dumps(result, ensure_ascii=False), 500

    connection.close()
    result_dict = {
        "result": True,
        "search_results": result_list
    }

    return json.dumps(result_dict, ensure_ascii=False), 200


@api.route('/explore/related', methods=['GET'])
def get_related_terms_list():
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    endpoint = API_ROOT + url_for('api.get_related_terms_list')
    # session_id = request.headers['Authorization']
    # check_session(session_id)

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

    query_parameter = request.args.to_dict()
    word = ''
    for key in query_parameter.keys():
        if key == 'word':
            word += request.args[key].strip()
    related_programs_list = []
    related_coaches_list = []
    related_exercises_list = []
    related_equipments_list = []

    cursor = connection.cursor()
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

        related_programs_list = sorted(related_programs_list, key=lambda x: x['similarity'])[:3]
        related_coaches_list = sorted(related_coaches_list, key=lambda x: x['similarity'])[:3]
        related_exercises_list = sorted(related_exercises_list, key=lambda x: x['similarity'])[:3]
        related_equipments_list = sorted(related_equipments_list, key=lambda x: x['similarity'])[:3]
        all_searched_result = sorted(related_programs_list + related_coaches_list + related_exercises_list + related_equipments_list, key=lambda x: x['similarity'])

    connection.close()
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
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    endpoint = API_ROOT + url_for('api.explore_log', user_id=user_id)
    # session_id = request.headers['Authorization']
    # check_session(session_id)

    try:
        connection = login_to_db()
    except Exception as e:
        error = str(e)
        result = {
            'result': False,
            'error': f'DB connection error: {error}'
        }
        slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
        return json.dumps(result, ensure_ascii=False), 500
    cursor = connection.cursor()

    if request.method == 'GET':  # 검색 기록 조회
        query = f"""
            SELECT DISTINCT
                            sl.id, 
                            sl.search_term 
                        FROM 
                            search_logs sl
                       WHERE 
                            sl.user_id={user_id}
                        AND
                            sl.deleted_at IS NULL
                    GROUP BY search_term
                    ORDER BY sl.created_at DESC"""  # 검색어 중복 제거하여 목록 반환
        try:
            cursor.execute(query)
            search_records = cursor.fetchall()
        except Exception as e:
            connection.rollback()
            connection.close()
            error = str(e)
            result = {
                'result': False,
                'error': f'Cannot delete the requested search record: {error}'
            }
            slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
            return json.dumps(result, ensure_ascii=False), 400

        if query_result_is_none(search_records) is True:
            connection.close()
            result = {
                'result': True,
                'logs': []
            }
            return json.dumps(result, ensure_ascii=False), 200

        logs = []
        for log in search_records:
            data = {'id': log[0], 'searched_word': log[1]}
            logs.append(data)

        connection.close()
        result_dict = {
            'result': True,
            'logs': logs
        }
        return json.dumps(result_dict, ensure_ascii=False), 200
    elif request.method == 'DELETE':  # 검색 기록 삭제
        try:
            connection = login_to_db()
        except Exception as e:
            error = str(e)
            result = {
                'result': False,
                'error': f'Server Error while connecting to DB: {error}'
            }
            slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'])
            return json.dumps(result, ensure_ascii=False), 500

        query_parameter = request.args.to_dict()
        word_to_delete = ''
        for key in query_parameter.keys():
            if key == 'word':
                word_to_delete += request.args[key].strip()

        if len(word_to_delete) > 0 or word_to_delete != '' or word_to_delete is not None:
            # 단건 삭제
            """
            만약 검색기록 조회 결과를 중복을 제거해서 보내준다면, id만으로 삭제하면 다음 번에 삭제한 단어를 또 보게 될 수 있다.
            따라서 아래와 같이 search_log_id가 아닌 user_id와 search_term을 함께 조회하여, 중복되는 단어를 전부 삭제 처리한다.
            """
            query = f"""
                UPDATE
                      search_logs
                  SET
                      deleted_at=(SELECT NOW())
                WHERE
                    search_term=%s
                  AND
                    user_id={user_id}
                  AND
                    deleted_at IS NULL"""
            values =(word_to_delete)
            try:
                cursor.execute(query)
            except Exception as e:
                connection.rollback()
                connection.close()
                error = str(e)
                result = {
                    'result': False,
                    'error': f'Cannot delete the requested search record: {error}'
                }
                slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
                return json.dumps(result, ensure_ascii=False), 400

            connection.commit()
            connection.close()
            result_dict = {
                'result': True,
                'message': "Successfully deleted the requested search record"
            }
            return json.dumps(result_dict, ensure_ascii=False), 200
        else:
            # 전체 삭제
            """
            만약 검색기록 조회 결과를 중복을 제거해서 보내준다면, id만으로 삭제하면 다음 번에 삭제한 단어를 또 보게 될 수 있다.
            따라서 아래와 같이 search_log_id가 아닌 user_id와 search_term을 함께 조회하여, 중복되는 단어를 전부 삭제 처리한다.
            """
            query = f"""
                  UPDATE
                        search_logs
                    SET
                        deleted_at=(SELECT NOW())
                  WHERE
                      user_id={user_id}
                  AND
                      deleted_at IS NULL"""
            try:
                cursor.execute(query)
            except Exception as e:
                connection.rollback()
                connection.close()
                error = str(e)
                result = {
                    'result': False,
                    'error': f'Cannot delete the requested search record: {error}'
                }
                slack_error_notification(user_ip=ip, user_id=user_id, api=endpoint, error_log=result['error'], query=query)
                return json.dumps(result, ensure_ascii=False), 400

            connection.commit()
            connection.close()
            result_dict = {
                'result': True,
                'message': "Successfully deleted the requested search record"
            }
            return json.dumps(result_dict, ensure_ascii=False), 200
    else:
        result_dict = {'result': False, 'error': 'Method not allowed'}
        return json.dumps(result_dict, ensure_ascii=False), 405
