def replace_number_to_schedule(schedule_list: list):
    replaced_date = []
    schedule_dict = {
        0: {"order": 0, "day": "월 06-09"},
        1: {"order": 6, "day": "화 06-09"},
        2: {"order": 12, "day": "수 06-09"},
        3: {"order": 18, "day": "목 06-09"},
        4: {"order": 24, "day": "금 06-09"},
        5: {"order": 30, "day": "토 06-09"},
        6: {"order": 36, "day": "일 06-09"},

        7: {"order": 1, "day": "월 09-12"},
        8: {"order": 7, "day": "화 09-12"},
        9: {"order": 13, "day": "수 09-12"},
        10: {"order": 19, "day": "목 09-12"},
        11: {"order": 25, "day": "금 09-12"},
        12: {"order": 31, "day": "토 09-12"},
        13: {"order": 37, "day": "일 09-12"},

        14: {"order": 2, "day": "월 12-15"},
        15: {"order": 8, "day": "화 12-15"},
        16: {"order": 14, "day": "수 12-15"},
        17: {"order": 20, "day": "목 12-15"},
        18: {"order": 26, "day": "금 12-15"},
        19: {"order": 32, "day": "토 12-15"},
        20: {"order": 38, "day": "일 12-15"},

        21: {"order": 3, "day": "월 15-18"},
        22: {"order": 9, "day": "화 15-18"},
        23: {"order": 15, "day": "수 15-18"},
        24: {"order": 21, "day": "목 15-18"},
        25: {"order": 27, "day": "금 15-18"},
        26: {"order": 33, "day": "토 15-18"},
        27: {"order": 39, "day": "일 15-18"},

        28: {"order": 4, "day": "월 18-21"},
        29: {"order": 10, "day": "화 18-21"},
        30: {"order": 16, "day": "수 18-21"},
        31: {"order": 22, "day": "목 18-21"},
        32: {"order": 28, "day": "금 18-21"},
        33: {"order": 34, "day": "토 18-21"},
        34: {"order": 40, "day": "일 18-21"},

        35: {"order": 5, "day": "월 21-24"},
        36: {"order": 11, "day": "화 21-24"},
        37: {"order": 17, "day": "수 21-24"},
        38: {"order": 23, "day": "목 21-24"},
        39: {"order": 29, "day": "금 21-24"},
        40: {"order": 35, "day": "토 21-24"},
        41: {"order": 41, "day": "일 21-24"}
    }
    if len(schedule_list) == 0:
        return replaced_date

    for grid_number in schedule_list:
        replaced_date.append(schedule_dict[grid_number])  # 리스트에 요소 추가하는 파이썬 문법...

    replaced_date = sorted(replaced_date, key=lambda x: x['order'])  # 리스트 정렬하는 파이썬 문법......
    replaced_date = [date['day'] for date in replaced_date]

    return replaced_date
