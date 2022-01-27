import json
import pandas as pd


def make_explore_query(word: str = "", sort_by: str = "latest"):
  """
  WHERE == FILTER!
    (1) p.title LIKE "%피%"
    (2) ex.title LIKE "%피%"
    (3) eq.name LIKE "%피%"
    (4) pur.title LIKE "%피%"
  :param word:
  :param sort_by:
  :return:
  """

  if sort_by == "rating":
    sort_standard = "p.created_at"  # average_rating
  elif sort_by == "frequency":
    sort_standard = "p.created_at"  # frequency_week
  else:
    sort_standard = "p.created_at"

  query_program = f"""
    SELECT
          p.id AS program_id,
          p.created_at,
          p.title,
          ex.title AS exercise,
          eq.name AS equipments,
          pur.title AS purposes,
          (SELECT pathname FROM files WHERE id = p.thumbnail_id) AS thumbnail,
          JSON_ARRAYAGG(JSON_OBJECT('pathname', f.pathname)) AS thumbnails,
          (SELECT COUNT(*) FROM program_lectures WHERE program_id = p.id) AS num_lectures
      FROM
          programs p,
          files f,
          exercises ex,
          program_exercises pex,
          equipments eq,
          program_equipments peq,
          purposes pur,
          program_purposes ppu
      WHERE
          p.title LIKE "%{word}%"
        AND
          f.original_file_id = p.thumbnail_id
        AND
          (ex.id = pex.exercise_id AND p.id = pex.program_id)
        AND
          (eq.id = peq.equipment_id AND p.id = peq.program_id)
        AND
          (pur.id = ppu.purpose_id AND ppu.program_id = p.id)
    GROUP BY 
          p.id, ex.id, eq.id, pur.id
    ORDER BY 
          {sort_standard} DESC"""

  query_coach = f"""
    SELECT
          p.id AS program_id,
          p.created_at,
          p.title,
          ex.title AS exercise,
          eq.name AS equipments,
          pur.title AS purposes,
          (SELECT pathname FROM files WHERE id = p.thumbnail_id) AS thumbnail,
          JSON_ARRAYAGG(JSON_OBJECT('pathname', f.pathname)) AS thumbnails,
          (SELECT COUNT(*) FROM program_lectures WHERE program_id = p.id) AS num_lectures
      FROM
          programs p,
          files f,
          coaches AS c,
          exercises ex,
          program_exercises pex,
          equipments eq,
          program_equipments peq,
          purposes pur,
          program_purposes ppu
      WHERE
          c.name LIKE "%{word}%"
        AND 
          p.coach_id = (SELECT id FROM coaches WHERE name=c.name)      
        AND
          f.original_file_id = p.thumbnail_id
        AND
          (ex.id = pex.exercise_id AND p.id = pex.program_id)
        AND
          (eq.id = peq.equipment_id AND p.id = peq.program_id)
        AND
          (pur.id = ppu.purpose_id AND ppu.program_id = p.id)
    GROUP BY 
          p.id, ex.id, eq.id, pur.id
    ORDER BY 
          {sort_standard} DESC"""

  query_exercise = f"""
    SELECT
          p.id AS program_id,
          p.created_at,
          p.title,
          ex.title AS exercise,
          eq.name AS equipments,
          pur.title AS purposes,
          (SELECT pathname FROM files WHERE id = p.thumbnail_id) AS thumbnail,
          JSON_ARRAYAGG(JSON_OBJECT('pathname', f.pathname)) AS thumbnails,
          (SELECT COUNT(*) FROM program_lectures WHERE program_id = p.id) AS num_lectures
      FROM
          programs p,
          files f,
          exercises ex,
          program_exercises pex,
          equipments eq,
          program_equipments peq,
          purposes pur,
          program_purposes ppu
      WHERE
          ex.title LIKE "%{word}%"
        AND
          pex.exercise_id = (SELECT id FROM exercises WHERE title = ex.title)
        AND
          f.original_file_id = p.thumbnail_id
        AND
          (ex.id = pex.exercise_id AND p.id = pex.program_id)
        AND
          (eq.id = peq.equipment_id AND p.id = peq.program_id)
        AND
          (pur.id = ppu.purpose_id AND ppu.program_id = p.id)
    GROUP BY 
          p.id, ex.id, eq.id, pur.id
    ORDER BY 
          {sort_standard} DESC"""

  query_equipment = f"""
    SELECT
          p.id AS program_id,
          p.created_at,
          p.title,
          ex.title AS exercise,
          eq.name AS equipments,
          pur.title AS purposes,
          (SELECT pathname FROM files WHERE id = p.thumbnail_id) AS thumbnail,
          JSON_ARRAYAGG(JSON_OBJECT('pathname', f.pathname)) AS thumbnails,
          (SELECT COUNT(*) FROM program_lectures WHERE program_id = p.id) AS num_lectures
      FROM
          programs p,
          files f,
          exercises ex,
          program_exercises pex,
          equipments eq,
          program_equipments peq,
          purposes pur,
          program_purposes ppu
      WHERE
          eq.name LIKE "%{word}%"
        AND
          peq.equipment_id = (SELECT id FROM equipments WHERE name = eq.name)
        AND
          f.original_file_id = p.thumbnail_id
        AND
          (ex.id = pex.exercise_id AND p.id = pex.program_id)
        AND
          (eq.id = peq.equipment_id AND p.id = peq.program_id)
        AND
          (pur.id = ppu.purpose_id AND ppu.program_id = p.id)
    GROUP BY 
          p.id, ex.id, eq.id, pur.id
    ORDER BY 
          {sort_standard} DESC"""
  return query_program, query_coach, query_exercise, query_equipment


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
    thumbnails_list = []
    for image in thumbnails:
      thumbnails_list.append(json.loads(image))

    result = {
      "id": each_id,
      "title": title,
      "thumbnail": thumbnail,
      "thumbnails": thumbnails_list,
      "num_lectures": num_lectures
    }
    result_list.append(result)

  return result_list


def make_query_to_find_related_terms(word: str):
  query_program = f"""
    SELECT
          prog.id,
          prog.title
      FROM
          programs prog
      WHERE 
          prog.title LIKE "%피%"
  ORDER BY CHAR_LENGTH(prog.title)"""

  query_coach = f"""
    SELECT
          c.id,
          c.name
      FROM
          coaches c
      WHERE 
          c.name LIKE "%{word}%"
  ORDER BY CHAR_LENGTH(c.name)"""

  query_exercise = f"""
    SELECT
        ex.id,
        ex.title
    FROM
        exercises ex
    WHERE 
        ex.title LIKE "%{word}%"
  ORDER BY CHAR_LENGTH(ex.title)"""

  query_equipment = f"""
    SELECT
          eq.id,
          eq.name
      FROM
          equipments eq
      WHERE 
          eq.name LIKE "%{word}%"
    ORDER BY CHAR_LENGTH(eq.name)"""

  return query_program, query_coach, query_exercise, query_equipment


def program_progress(user_id):
  pass