import json

# def explore_query(search_filter, word):
#   if search_filter == 'program':
#     query = f"""
#       SELECT
#             p.id AS program_id,
#             p.title,
#             (SELECT pathname FROM files WHERE id = p.thumbnail_id) AS thumbnail,
#             f.pathname AS thumbnails,
#             (SELECT COUNT(*) FROM program_lectures WHERE program_id = p.id) AS num_lectures
#         FROM
#             programs p,
#             files f
#         WHERE
#             p.title LIKE "%{word}%"
#         AND
#             f.original_file_id = p.thumbnail_id"""
#
#     return query
#   elif search_filter == 'exercise':
#     pass
#   elif search_filter == 'coach':
#     pass
#   elif search_filter == 'equipment':
#     pass
#   elif search_filter == 'purpose':
#     pass
#   else:
#     pass


def explore_query(word: str = "", sort_by: str = "latest"):
  """
  WHERE == FILTER!
    (1) p.title LIKE "%피%"
    (2) ex.title LIKE "%피%"
    (3) eq.name LIKE "%피%"
    (4) pur.title LIKE "%피%"
  :param search_filter:
  :param word:
  :param sort_by:
  :return:
  """

  if sort_by == "rating":
    sort_standard = "average_rating"
  elif sort_by == "frequency":
    sort_standard = "frequency_week"
  else:
    sort_standard = "p.created_at"

  query = f"""
    SELECT
          p.id AS program_id,
          p.created_at,
          p.title,
          ex.title AS exercise,
          JSON_ARRAYAGG(JSON_OBJECT('equipments', eq.name)) AS equipments,
          JSON_ARRAYAGG(JSON_OBJECT('purposes', pur.title)) AS purposes,
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
          p.id
    ORDER BY 
          {sort_standard} DESC"""
  return query

  # elif search_filter == 'exercise':
  #   pass
  # elif search_filter == 'coach':
  #   pass
  # elif search_filter == 'equipment':
  #   pass
  # elif search_filter == 'purpose':
  #   pass
  # else:
  #   pass
