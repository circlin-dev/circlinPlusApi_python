def convert_index_to_sports(answer_array: list, list_type: str):
  # list_type == 'purpose', 'sports', 'equipment'는 응답값 index가 1부터 시작되므로 유의한다(DB에서 각 항목을 1번부터 관리하기 때문).
  if list_type == 'purpose' and len(answer_array) > 0:
    new_list = []
    for answer in answer_array:
      if answer == 1: new_list.append("체력강화/건강유지")
      elif answer == 2: new_list.append("다이어트")
      elif answer == 3: new_list.append("바른체형/신체정렬")
      elif answer == 4: new_list.append("근력향상")
      elif answer == 5: new_list.append("산전/산후관리")
      elif answer == 6: new_list.append("중증 통증관리")
    return new_list
  elif list_type == 'sports' and len(answer_array) > 0:
    new_list = []
    for answer in answer_array:
      if answer == 1: new_list.append("무관")
      elif answer == 2: new_list.append("요가")
      elif answer == 3: new_list.append("필라테스")
      elif answer == 4: new_list.append("웨이트")
      elif answer == 5: new_list.append("유산소")
      elif answer == 6: new_list.append("무산소")
    return new_list
  elif list_type == 'disease' and len(answer_array) > 0:
    new_list = []
    for answer in answer_array:
      if answer == 0: new_list.append("허리디스크")
      elif answer == 1: new_list.append("목디스크")
      elif answer == 2: new_list.append("고혈압")
      elif answer == 3: new_list.append("저혈압")
      elif answer == 4: new_list.append("천식")
      elif answer == 5: new_list.append("당뇨")
      elif answer == 6: new_list.append("기타(수술이력, 사고이력)")
    return new_list
  elif list_type == 'age_group' and len(answer_array) > 0:
    new_list = []
    for answer in answer_array:
      if answer == 0: new_list.append("10대")
      elif answer == 1: new_list.append("20대")
      elif answer == 2: new_list.append("30대")
      elif answer == 3: new_list.append("40대")
      elif answer == 4: new_list.append("50대")
      elif answer == 5: new_list.append("60대")
      elif answer == 6: new_list.append("70대+")
    return new_list
  elif list_type == 'experience_group' and len(answer_array) > 0:
    new_list = []
    for answer in answer_array:
      if answer == 0: new_list.append("처음")
      elif answer == 1: new_list.append("~1개월 이내")
      elif answer == 2: new_list.append("~3개월 이내")
      elif answer == 3: new_list.append("~6개월 이내")
      elif answer == 4: new_list.append("~1년 이내")
      elif answer == 5: new_list.append("~3년 이내")
      elif answer == 6: new_list.append("~5년 이내")
      elif answer == 7: new_list.append("5년 이상")
    return new_list

