import json
import pandas as pd
from pypika import MySQLQuery as Query, Criterion, Table, Order, functions as fn


def make_explore_query(word: str = "", user_id: int = 0, sort_by: str = "latest"):
    """
    WHERE == FILTER!
      (1) p.title LIKE "%피%"
      (2) ex.title LIKE "%피%"
      (3) eq.name LIKE "%피%"
      (4) pur.title LIKE "%피%"
    :param word:
    :param user_id:
    :param sort_by:
    :return:
    """

    if sort_by == "rating":
        sort_standard = "p.created_at"  # average_rating
    elif sort_by == "frequency":
        sort_standard = "p.created_at"  # frequency_week
    else:
        sort_standard = "p.created_at"

    sql_program = f"""
        SELECT
              p.id AS program_id,
              p.created_at,
              p.title,
              ex.title AS exercise,
              prod.title AS equipments,
              pur.title AS purposes,
              (SELECT pathname FROM files WHERE id = p.thumbnail_id) AS thumbnail,
              JSON_ARRAYAGG(JSON_OBJECT('pathname', f.pathname)) AS thumbnails,
              (SELECT COUNT(*) FROM lectures WHERE program_id = p.id) AS num_lectures,
               IFNULL(cl.num_completed_lectures, 0) AS num_completed_lectures
          FROM
              programs p
                        LEFT JOIN
                                (SELECT
                                    completed_lectures.program_id,
                                    COUNT(completed_lectures.program_id) AS num_completed_lectures
                                FROM
                                    (SELECT
                                        DISTINCT ul.lecture_id,
                                        l.program_id,
                                        (SELECT COUNT(*) from lectures WHERE id=ul.lecture_id AND program_id = l.program_id) AS num_lectures
                                    FROM
                                        user_lectures ul
                                    INNER JOIN lectures l on (l.id = ul.lecture_id)
                                    WHERE ul.completed_at IS NOT NULL
                                    AND ul.user_id={user_id}) completed_lectures
                                GROUP BY completed_lectures.program_id) cl
                            ON cl.program_id = p.id,
              files f,
              exercises ex,
              program_exercises pex,
              products prod,
              program_products ppo,
              purposes pur,
              program_purposes ppu
          WHERE
               p.title LIKE '%{word}%'
            AND
              f.original_file_id = p.thumbnail_id
            AND
              (ex.id = pex.exercise_id AND p.id = pex.program_id)
            AND
              (prod.id = ppo.product_id AND p.id = ppo.program_id)
            AND
              (pur.id = ppu.purpose_id AND ppu.program_id = p.id)
        GROUP BY
              p.id, ex.id, prod.id, pur.id
        ORDER BY
              {sort_standard} DESC"""

    sql_coach = f"""
        SELECT
            p.id AS program_id,
            p.created_at,
            p.title,
            ex.title AS exercise,
            prod.title AS equipments,
            pur.title AS purposes,
            (SELECT pathname FROM files WHERE id = p.thumbnail_id) AS thumbnail,
            JSON_ARRAYAGG(JSON_OBJECT('pathname', f.pathname)) AS thumbnails,
            (SELECT COUNT(*) FROM lectures WHERE program_id = p.id) AS num_lectures,
            IFNULL(cl.num_completed_lectures, 0) AS num_completed_lectures
        FROM
            programs p
                LEFT JOIN
                        (SELECT
                            completed_lectures.program_id,
                            COUNT(completed_lectures.program_id) AS num_completed_lectures
                        FROM
                            (SELECT
                                DISTINCT ul.lecture_id,
                                l.program_id,
                                (SELECT COUNT(*) from lectures WHERE id=ul.lecture_id AND program_id = l.program_id) AS num_lectures
                            FROM
                                user_lectures ul
                            INNER JOIN lectures l on (l.id = ul.lecture_id)
                            WHERE ul.completed_at IS NOT NULL
                            AND ul.user_id={user_id}) completed_lectures
                        GROUP BY completed_lectures.program_id) cl
                ON cl.program_id = p.id,
            files f,
            coaches AS c,
            exercises ex,
            program_exercises pex,
            products prod,
            program_products ppo,
            purposes pur,
            program_purposes ppu
        WHERE
            c.name LIKE '%{word}%'
        AND
            p.coach_id = (SELECT id FROM coaches WHERE name=c.name)
        AND
            f.original_file_id = p.thumbnail_id
        AND
            (ex.id = pex.exercise_id AND p.id = pex.program_id)
        AND
            (prod.id = ppo.product_id AND p.id = ppo.program_id)
        AND
            (pur.id = ppu.purpose_id AND ppu.program_id = p.id)
        GROUP BY
            p.id, ex.id, prod.id, pur.id
        ORDER BY
            {sort_standard} DESC"""

    sql_exercise = f"""
        SELECT
              p.id,
              p.created_at,
              p.title,
              ex.title AS exercise,
              prod.title AS equipments,
              pur.title AS purposes,
              (SELECT pathname FROM files WHERE id = p.thumbnail_id) AS thumbnail,
              JSON_ARRAYAGG(JSON_OBJECT('pathname', f.pathname)) AS thumbnails,
              (SELECT COUNT(*) FROM lectures WHERE program_id = p.id) AS num_lectures,
              IFNULL(cl.num_completed_lectures, 0) AS num_completed_lectures
          FROM
              programs p
                        LEFT JOIN
                                (SELECT
                                    completed_lectures.program_id,
                                    COUNT(completed_lectures.program_id) AS num_completed_lectures
                                FROM
                                    (SELECT
                                        DISTINCT ul.lecture_id,
                                        l.program_id,
                                        (SELECT COUNT(*) from lectures WHERE id=ul.lecture_id AND program_id = l.program_id) AS num_lectures
                                    FROM
                                        user_lectures ul
                                    INNER JOIN lectures l on (l.id = ul.lecture_id)
                                    WHERE ul.completed_at IS NOT NULL
                                    AND ul.user_id={user_id}) completed_lectures
                                GROUP BY completed_lectures.program_id) cl
                            ON cl.program_id = p.id,
              files f,
              exercises ex,
              program_exercises pex,
              products prod,
              program_products ppo,
              purposes pur,
              program_purposes ppu
          WHERE
              ex.title LIKE '%{word}%'
            AND
              pex.exercise_id = (SELECT id FROM exercises WHERE title = ex.title)
            AND
              f.original_file_id = p.thumbnail_id
            AND
              (ex.id = pex.exercise_id AND p.id = pex.program_id)
            AND
              (prod.id = ppo.product_id AND p.id = ppo.program_id)
            AND
              (pur.id = ppu.purpose_id AND ppu.program_id = p.id)
        GROUP BY
              p.id, ex.id, prod.id, pur.id
        ORDER BY
              {sort_standard} DESC"""

    sql_equipment = f"""
        SELECT
              p.id,
              p.created_at,
              p.title,
              ex.title AS exercise,
              prod.title AS equipments,
              pur.title AS purposes,
              (SELECT pathname FROM files WHERE id = p.thumbnail_id) AS thumbnail,
              JSON_ARRAYAGG(JSON_OBJECT('pathname', f.pathname)) AS thumbnails,
              (SELECT COUNT(*) FROM lectures WHERE program_id = p.id) AS num_lectures,
              IFNULL(cl.num_completed_lectures, 0) AS num_completed_lectures
          FROM
              programs p
                        LEFT JOIN
                                (SELECT
                                    completed_lectures.program_id,
                                    COUNT(completed_lectures.program_id) AS num_completed_lectures
                                FROM
                                    (SELECT
                                        DISTINCT ul.lecture_id,
                                        l.program_id,
                                        (SELECT COUNT(*) from lectures WHERE id=ul.lecture_id AND program_id = l.program_id) AS num_lectures
                                    FROM
                                        user_lectures ul
                                    INNER JOIN lectures l on (l.id = ul.lecture_id)
                                    WHERE ul.completed_at IS NOT NULL
                                    AND ul.user_id={user_id}) completed_lectures
                                GROUP BY completed_lectures.program_id) cl
                            ON cl.program_id = p.id,
              files f,
              exercises ex,
              program_exercises pex,
              products prod,
              program_products ppo,
              purposes pur,
              program_purposes ppu
          WHERE
              prod.title LIKE '%{word}%'
            AND
              pex.exercise_id = (SELECT id FROM exercises WHERE title = ex.title)
            AND
              f.original_file_id = p.thumbnail_id
            AND
              (ex.id = pex.exercise_id AND p.id = pex.program_id)
            AND
              (prod.id = ppo.product_id AND p.id = ppo.program_id)
            AND
              (pur.id = ppu.purpose_id AND ppu.program_id = p.id)
        GROUP BY
              p.id, ex.id, prod.id, pur.id
        ORDER BY
              {sort_standard} DESC"""

    return sql_program, sql_coach, sql_exercise, sql_equipment


def filter_dataframe(filter_exercise: list, filter_purpose: list, filter_equipment: list, programs_df: pd.DataFrame):
    programs = programs_df.copy()
    # Apply search filter ==> 필터 순서에 따라 결과가 달라질까???
    if len(filter_exercise) == 0 and len(filter_purpose) == 0 and len(filter_equipment) == 0:
        pass
    elif len(filter_exercise) > 0 and len(filter_purpose) == 0 and len(filter_equipment) == 0:
        programs = programs[programs['exercise'].isin(filter_exercise)]
    elif len(filter_exercise) == 0 and len(filter_purpose) > 0 and len(filter_equipment) == 0:
        programs = programs[programs['purposes'].isin(filter_purpose)]
    elif len(filter_exercise) == 0 and len(filter_purpose) == 0 and len(filter_equipment) > 0:
        programs = programs[programs['equipments'].isin(filter_equipment)]
    elif len(filter_exercise) > 0 and len(filter_purpose) > 0 and len(filter_equipment) == 0:
        programs = programs[programs['exercise'].isin(filter_exercise) &
                            programs['purposes'].isin(filter_purpose)]
    elif len(filter_exercise) > 0 and len(filter_purpose) == 0 and len(filter_equipment) > 0:
        programs = programs[programs['exercise'].isin(filter_exercise) &
                            programs['equipments'].isin(filter_equipment)]
    elif len(filter_exercise) == 0 and len(filter_purpose) > 0 and len(filter_equipment) > 0:
        programs = programs[programs['purposes'].isin(filter_purpose) &
                            programs['equipments'].isin(filter_equipment)]
    else:
        programs = programs[programs['exercise'].isin(filter_exercise) &
                            programs['purposes'].isin(filter_purpose) &
                            programs['equipments'].isin(filter_equipment)]

    program_ids = programs['program_id'].unique()

    result_list = []
    for each_id in program_ids:
        each_id = int(each_id)
        df_by_id = programs[programs['program_id'] == each_id]
        title = df_by_id['title'].unique()[0]  # For error 'TypeError: Object of type int64 is not JSON serializable'
        thumbnail = df_by_id['thumbnail'].unique()[0]
        thumbnails = list(set(df_by_id['thumbnails'].values.tolist()[0].strip('][').split(', ')))
        thumbnails = sorted(thumbnails, key=lambda x: int(x.split('_')[1].split('w')[0]), reverse=True)  # Thumbnails needs be sorted from big size to small size(1080 -> ... 150).
        num_lectures = int(df_by_id['num_lectures'].unique()[0])
        num_completed_lectures = int(df_by_id['num_completed_lectures'].unique()[0])
        thumbnails_list = []
        for image in thumbnails:
            thumbnails_list.append(json.loads(image))

        result = {
            "id": each_id,
            "title": title,
            "thumbnail": thumbnail,
            "thumbnails": thumbnails_list,
            "num_lectures": num_lectures,
            "num_completed_lectures": num_completed_lectures
        }
        result_list.append(result)

    return result_list


def make_query_to_find_related_terms(word: str):
    programs = Table('programs')
    coaches = Table('coaches')
    exercises = Table('exercises')
    products = Table('products')

    query_program = Query.from_(
        programs
    ).select(
        programs.id,
        programs.title
    ).where(
        programs.title.like(f'%{word}%')
    ).orderby(fn.Length(programs.title)).get_sql()

    query_coach = Query.from_(
        coaches
    ).select(
        coaches.id,
        coaches.name
    ).where(
        coaches.name.like(f'%{word}%')
    ).orderby(fn.Length(coaches.name)).get_sql()

    query_exercise = Query.from_(
        exercises
    ).select(
        exercises.id,
        exercises.title
    ).where(
        exercises.title.like(f'%{word}%')
    ).orderby(fn.Length(exercises.title)).get_sql()

    query_equipment = Query.from_(
        products
    ).select(
        products.id,
        products.title
    ).where(
        Criterion.all([
            products.title.like(f'%{word}%'),
            products.type == 'equipment'   # item?
        ])
    ).orderby(fn.Length(products.title)).get_sql()

    return query_program, query_coach, query_exercise, query_equipment


def make_query_get_every_titles():
    programs = Table('programs')
    coaches = Table('coaches')
    exercises = Table('exercises')
    products = Table('products')

    sql_programs = Query.from_(
        programs
    ).select(
        programs.id,
        programs.title
    ).orderby(fn.Length(programs.title)).get_sql()

    sql_coaches = Query.from_(
        coaches
    ).select(
        coaches.id,
        coaches.name
    ).orderby(fn.Length(coaches.name)).get_sql()

    sql_exercises = Query.from_(
        exercises
    ).select(
        exercises.id,
        exercises.title
    ).orderby(fn.Length(exercises.title)).get_sql()

    sql_equipments = Query.from_(
        products
    ).select(
        products.id,
        products.title
    ).where(
        products.type == 'equipment'
    ).orderby(fn.Length(products.title)).get_sql()

    return sql_programs, sql_coaches, sql_exercises, sql_equipments
