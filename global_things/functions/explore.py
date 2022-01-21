def explore_query(search_filter, word):
  if search_filter == 'program':
    query = f"""
      SELECT
            p.id AS program_id,
            p.title,
            (SELECT pathname FROM files WHERE id = p.thumbnail_id) AS thumbnail,
            f.pathname AS thumbnails,            
            (SELECT COUNT(*) FROM program_lectures WHERE program_id = p.id) AS num_lectures
        FROM
            programs p,
            files f
        WHERE 
            p.title LIKE "%{word}%"
        AND
            f.original_file_id = p.thumbnail_id"""

    return query
  elif search_filter == 'exercise':
    pass
  elif search_filter == 'coach':
    pass
  elif search_filter == 'equipment':
    pass
  elif search_filter == 'purpose':
    pass
  else:
    pass