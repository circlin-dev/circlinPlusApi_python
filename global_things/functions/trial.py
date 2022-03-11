import requests

# 무료 프로그램 체험 CASE 1 ~ 19
TRIAL_DICTIONARY = {
    "피트니스": {
        # case 1, 2, 3(완료)
        "M": [
            {"day": 0, "lecture_id": 1, 'type': 'guide', "title": "기본기 - 하체 운동"},
            {"day": 0, "lecture_id": 97, 'type': 'drill', "title": "기본기 - 하체 운동 (실습)(체험)"},
            {"day": 1, "lecture_id": 41, 'type': 'guide', "title": "기본기 - 등/복근 운동"},
            {"day": 1, "lecture_id": 98, 'type': 'drill', "title": "기본기 - 등/복근 운동 (실습)(체험)"},
            {"day": 2, "lecture_id": 43, 'type': 'guide', "title": "기본기 - 힙 운동"},
            {"day": 2, "lecture_id": 99, 'type': 'drill', "title": "기본기 - 힙 운동 (실습)(체험)"},
            {"day": 3, "lecture_id": 45, 'type': 'guide', "title": "기본기 - 가슴/어깨 운동"},
            {"day": 3, "lecture_id": 100, 'type': 'drill', "title": "기본기 - 가슴/어깨 운동 (실습)(체험)"},
            {"day": 4, "lecture_id": 47, 'type': 'guide', "title": "기본 & 케틀벨 - 하체 운동"},
            {"day": 4, "lecture_id": 101, 'type': 'drill', "title": "기본 & 케틀벨 - 하체 운동 (실습)(체험)"},
            {"day": 5, "lecture_id": 49, 'type': 'guide', "title": "기본 & 케틀벨 - 등/복근 운동"},
            {"day": 5, "lecture_id": 102, 'type': 'drill', "title": "기본 & 케틀벨 - 등/복근 운동 (실습)(체험)"},
            {"day": 6, "lecture_id": 51, 'type': 'guide', "title": "기본 & 케틀벨 - 힙 운동"},
            {"day": 6, "lecture_id": 103, 'type': 'drill', "title": "기본 & 케틀벨 - 힙 운동 (실습)(체험)"},
        ],
        # case 4, 5, 6(완료)
        "W": [  # 1일차, 3일차, 5일차, 6일차
            {"day": 0, "lecture_id": 1, 'type': 'guide', "title": "기본기 - 하체 운동"},
            {"day": 0, "lecture_id": 97, 'type': 'drill', "title": "기본기 - 하체 운동 (실습)(체험)"},
            {"day": 1, "lecture_id": 41, 'type': 'guide', "title": "기본기 - 등/복근 운동"},
            {"day": 1, "lecture_id": 98, 'type': 'drill', "title": "기본기 - 등/복근 운동 (실습)(체험)"},
            {"day": 2, "lecture_id": 43, 'type': 'guide', "title": "기본기 - 힙 운동"},
            {"day": 2, "lecture_id": 99, 'type': 'drill', "title": "기본기 - 힙 운동 (실습)(체험)"},
            {"day": 3, "lecture_id": 45, 'type': 'guide', "title": "기본기 - 가슴/어깨 운동"},
            {"day": 3, "lecture_id": 100, 'type': 'drill', "title": "기본기 - 가슴/어깨 운동 (실습)(체험)"},
            {"day": 4, "lecture_id": 47, 'type': 'guide', "title": "기본 & 케틀벨 - 하체 운동"},
            {"day": 4, "lecture_id": 101, 'type': 'drill', "title": "기본 & 케틀벨 - 하체 운동 (실습)(체험)"},
            {"day": 5, "lecture_id": 49, 'type': 'guide', "title": "기본 & 케틀벨 - 등/복근 운동"},
            {"day": 5, "lecture_id": 102, 'type': 'drill', "title": "기본 & 케틀벨 - 등/복근 운동 (실습)(체험)"},
            {"day": 6, "lecture_id": 51, 'type': 'guide', "title": "기본 & 케틀벨 - 힙 운동"},
            {"day": 6, "lecture_id": 103, 'type': 'drill', "title": "기본 & 케틀벨 - 힙 운동 (실습)(체험)"},
        ]
    },
    "필라테스": {
        # case 7, 8, 9(W 완료)(M은 W의 것으로 배정되게 해 둔 상태이며, 주석한 부분이 원래 M용.
        "M": [
            {"day": 0, "lecture_id": 142, "type": "guide", "title":  "틀어진 골반 교정 운동 2"},
            {"day": 0, "lecture_id": 144, "type": "drill", "title":  "[실습] 틀어진 골반 교정 운동 2(체험)"},
            {"day": 1, "lecture_id": 80,  "type": "guide", "title":  "하체 스트레칭 1"},
            {"day": 1, "lecture_id": 92, "type": "drill",  "title":  "하체 스트레칭 1 (실습)(체험)"},
            {"day": 2, "lecture_id": 14,  "type": "guide", "title":  "before start 1"},
            {"day": 2, "lecture_id": 116, "type": "drill", "title":  "before start 1 (실습)(체험)"},
            {"day": 3, "lecture_id": 16,  "type": "guide", "title": "before start 2"},
            {"day": 3, "lecture_id": 117, "type": "drill", "title": "before start 2 (실습)(체험)"},
            {"day": 4, "lecture_id": 18,  "type": "guide", "title":  "before start 3"},
            {"day": 4, "lecture_id": 118, "type": "drill", "title":  "before start 3 (실습)(체험)"},
            {"day": 5, "lecture_id": 81,  "type": "guide", "title":  "하체 스트레칭 2"},
            {"day": 5, "lecture_id": 93, "type": "drill",  "title":  "하체 스트레칭 2 (실습)(체험)"},
            {"day": 6, "lecture_id": 104, "type": "guide",  "title": "Core Integration (코어통합) LEVEL 1"},
            {"day": 6, "lecture_id": 120, "type": "drill", "title": "Core Integration (코어통합) LEVEL 1 (실습)(체험)"}
            # {"day": 0, "lecture_id": 80, "title":  "하체 스트레칭 1"},
            # {"day": 0, "lecture_id": 92, "title":  "하체 스트레칭 1 (실습)(체험)"}
            # {"day": 1, "lecture_id": 81, "title":  "하체 스트레칭 2"}
            # {"day": 1, "lecture_id": 93, "title":  "하체 스트레칭 2 (실습)(체험)"}
            # {"day": 2, "lecture_id": 82, "title":  "하체 스트레칭 3"}
            # {"day": 2, "lecture_id": 94, "title":  "하체 스트레칭 3 (실습)(체험)"}
            # {"day": 3, "lecture_id": 83, "title": "상체 스트레칭 1"}
            # {"day": 3, "lecture_id": 95, "title": "상체 스트레칭 1 (실습)(체험)"}
            # {"day": 4, "lecture_id": 84, "title":  "상체 스트레칭 2"}
            # {"day": 4, "lecture_id": 96, "title":  "상체 스트레칭 2 (실습)(체험)"}
            # {"day": 5, "lecture_id": , "title": "필라테스 초급 동작 1"}, # 편집 미완성
            # {"day": 5, "lecture_id": , "title": "필라테스 초급 동작 1 (실습)(체험)"}, # 편집 미완성
            # {"day": 6, "lecture_id": , "title": "필라테스 초급 동작 2"}  # 편집 미완성
            # {"day": 6, "lecture_id": , "title": "필라테스 초급 동작 2 (실습)(체험)"}  # 편집 미완성
        ],
        # case 10, 11, 12(완료)
        "W": [
            {"day": 0, "lecture_id": 142, "type": "guide", "title":  "틀어진 골반 교정 운동 2"},
            {"day": 0, "lecture_id": 144, "type": "drill", "title":  "[실습] 틀어진 골반 교정 운동 2(체험)"},
            {"day": 1, "lecture_id": 80,  "type": "guide", "title":  "하체 스트레칭 1"},
            {"day": 1, "lecture_id": 92, "type": "drill",  "title":  "하체 스트레칭 1 (실습)(체험)"},
            {"day": 2, "lecture_id": 14,  "type": "guide", "title":  "before start 1"},
            {"day": 2, "lecture_id": 116, "type": "drill", "title":  "before start 1 (실습)(체험)"},
            {"day": 3, "lecture_id": 16,  "type": "guide", "title": "before start 2"},
            {"day": 3, "lecture_id": 117, "type": "drill", "title": "before start 2 (실습)(체험)"},
            {"day": 4, "lecture_id": 18,  "type": "guide", "title":  "before start 3"},
            {"day": 4, "lecture_id": 118, "type": "drill", "title":  "before start 3 (실습)(체험)"},
            {"day": 5, "lecture_id": 81,  "type": "guide", "title":  "하체 스트레칭 2"},
            {"day": 5, "lecture_id": 93, "type": "drill",  "title":  "하체 스트레칭 2 (실습)(체험)"},
            {"day": 6, "lecture_id": 104, "type": "guide",  "title": "Core Integration (코어통합) LEVEL 1"},
            {"day": 6, "lecture_id": 120, "type": "drill", "title": "Core Integration (코어통합) LEVEL 1 (실습)(체험)"}
        ]
    },
    "요가": {  # case 13(완료)
        "M": [
            {"day": 0, "lecture_id": 35, "type": "guide", "title": "웜업 요가 I"},
            {"day": 1, "lecture_id": 36, "type": "guide", "title": "웜업 요가 II"},
            {"day": 2, "lecture_id": 37, "type": "guide", "title": "빈야사 기초"},
            {"day": 3, "lecture_id": 38, "type": "guide", "title": "빈야사의 기초 자세 1"},
            {"day": 4, "lecture_id": 39, "type": "guide", "title": "빈야사의 기초 자세 2"},
            {"day": 5, "lecture_id": 90, "type": "guide", "title": "빈야사의 기초 자세 3"},
            {"day": 6, "lecture_id": 121, "type": "guide", "title": "베이직 빈야사 I"}
        ],
        "W": [
            {"day": 0, "lecture_id": 35, "type": "guide", "title": "웜업 요가 I"},
            {"day": 1, "lecture_id": 36, "type": "guide", "title": "웜업 요가 II"},
            {"day": 2, "lecture_id": 37, "type": "guide", "title": "빈야사 기초"},
            {"day": 3, "lecture_id": 38, "type": "guide", "title": "빈야사의 기초 자세 1"},
            {"day": 4, "lecture_id": 39, "type": "guide", "title": "빈야사의 기초 자세 2"},
            {"day": 5, "lecture_id": 90, "type": "guide", "title": "빈야사의 기초 자세 3"},
            {"day": 6, "lecture_id": 121, "type": "guide", "title": "베이직 빈야사 I"}
        ]
    },
    "댄스 카디오": {  # case 14, 15, 16(완료)
        "M": [
            {"day": 0, "lecture_id": 122, "type": "guide", "title": "BASIC 전신"},
            {"day": 0, "lecture_id": 146, "type": "drill2", "title": "[실습] BASIC 전신(체험)"},
            {"day": 1, "lecture_id": 124, "type": "guide", "title": "BASIC 상체"},
            {"day": 1, "lecture_id": 147, "type": "drill2", "title": "[실습] BASIC 상체(체험)"},
            {"day": 2, "lecture_id": 126, "type": "guide", "title": "BASIC 하체"},
            {"day": 2, "lecture_id": 148, "type": "drill2", "title": "[실습] BASIC 하체(체험)"},
            {"day": 3, "lecture_id": 128, "type": "guide", "title": "BASIC 근력"},
            {"day": 3, "lecture_id": 149, "type": "drill2", "title": "[실습] BASIC 근력(체험)"},
            {"day": 4, "lecture_id": 130, "type": "guide", "title": "BASIC 힙합"},
            {"day": 4, "lecture_id": 150, "type": "drill2", "title": "[실습] BASIC 힙합(체험)"},
            {"day": 5, "lecture_id": 132, "type": "guide", "title": "LEVEL UP 전신"},
            {"day": 5, "lecture_id": 151, "type": "drill2", "title": "[실습] LEVEL UP 전신(체험)"},
            {"day": 6, "lecture_id": 134, "type": "guide", "title": "LEVEL UP 상체"},
            {"day": 6, "lecture_id": 152, "type": "drill2", "title": "[실습] LEVEL UP 상체(체험)"}
        ],
        "W": [
            {"day": 0, "lecture_id": 122, "type": "guide", "title": "BASIC 전신"},
            {"day": 0, "lecture_id": 146, "type": "drill2", "title": "[실습] BASIC 전신(체험)"},
            {"day": 1, "lecture_id": 124, "type": "guide", "title": "BASIC 상체"},
            {"day": 1, "lecture_id": 147, "type": "drill2", "title": "[실습] BASIC 상체(체험)"},
            {"day": 2, "lecture_id": 126, "type": "guide", "title": "BASIC 하체"},
            {"day": 2, "lecture_id": 148, "type": "drill2", "title": "[실습] BASIC 하체(체험)"},
            {"day": 3, "lecture_id": 128, "type": "guide", "title": "BASIC 근력"},
            {"day": 3, "lecture_id": 149, "type": "drill2", "title": "[실습] BASIC 근력(체험)"},
            {"day": 4, "lecture_id": 130, "type": "guide", "title": "BASIC 힙합"},
            {"day": 4, "lecture_id": 150, "type": "drill2", "title": "[실습] BASIC 힙합(체험)"},
            {"day": 5, "lecture_id": 132, "type": "guide", "title": "LEVEL UP 전신"},
            {"day": 5, "lecture_id": 151, "type": "drill2", "title": "[실습] LEVEL UP 전신(체험)"},
            {"day": 6, "lecture_id": 134, "type": "guide", "title": "LEVEL UP 상체"},
            {"day": 6, "lecture_id": 152, "type": "drill2", "title": "[실습] LEVEL UP 상체(체험)"}
        ]
    },
    "서킷 트레이닝": {  # case 17, 18, 19(완성)  ==>  강의(guide) 없이 '실습(drill)'만 있음.
        "M": [
            {"day": 0, "lecture_id": 160, "type": "drill", "title": "왕초보 전신&팔 운동(체험)"},
            {"day": 1, "lecture_id": 161, "type": "drill", "title": "누워서 하는 복근&상체 운동(체험)"},
            {"day": 2, "lecture_id": 164, "type": "drill", "title": "허벅지 집중 운동(체험)"},
            {"day": 3, "lecture_id": 162, "type": "drill", "title": "코어 강화 운동(체험)"},
            {"day": 4, "lecture_id": 163, "type": "drill", "title": "엉덩이 자극 집중 운동(체험)"},
            {"day": 5, "lecture_id": 166, "type": "drill", "title": "운동량 up! 전신 유산소 운동(체험)"},
            {"day": 6, "lecture_id": 165, "type": "drill", "title": "왕초보 전신&하체 운동(체험)"}
        ],
        "W": [
            {"day": 0, "lecture_id": 160, "type": "drill", "title": "왕초보 전신&팔 운동(체험)"},
            {"day": 1, "lecture_id": 161, "type": "drill", "title": "누워서 하는 복근&상체 운동(체험)"},
            {"day": 2, "lecture_id": 164, "type": "drill", "title": "허벅지 집중 운동(체험)"},
            {"day": 3, "lecture_id": 162, "type": "drill", "title": "코어 강화 운동(체험)"},
            {"day": 4, "lecture_id": 163, "type": "drill", "title": "엉덩이 자극 집중 운동(체험)"},
            {"day": 5, "lecture_id": 166, "type": "drill", "title": "운동량 up! 전신 유산소 운동(체험)"},
            {"day": 6, "lecture_id": 165, "type": "drill", "title": "왕초보 전신&하체 운동(체험)"}
        ],
    },
    "복싱": {
        # 무료 체험 강의 편성에는 없는 종목이지만, 써킷 트레이닝으로 부여함(단, 서킷 트레이닝을 이미 선택한 유저의 경우 중복을 제거한다)(https://circlincoltd.slack.com/archives/C01BY52TMPZ/p1646665898210579)
        "M": [
            {"day": 0, "lecture_id": 160, "type": "drill", "title": "왕초보 전신&팔 운동(체험)"},
            {"day": 1, "lecture_id": 161, "type": "drill", "title": "누워서 하는 복근&상체 운동(체험)"},
            {"day": 2, "lecture_id": 164, "type": "drill", "title": "허벅지 집중 운동(체험)"},
            {"day": 3, "lecture_id": 162, "type": "drill", "title": "코어 강화 운동(체험)"},
            {"day": 4, "lecture_id": 163, "type": "drill", "title": "엉덩이 자극 집중 운동(체험)"},
            {"day": 5, "lecture_id": 166, "type": "drill", "title": "운동량 up! 전신 유산소 운동(체험)"},
            {"day": 6, "lecture_id": 165, "type": "drill", "title": "왕초보 전신&하체 운동(체험)"}
        ],
        "W": [
            {"day": 0, "lecture_id": 160, "type": "drill", "title": "왕초보 전신&팔 운동(체험)"},
            {"day": 1, "lecture_id": 161, "type": "drill", "title": "누워서 하는 복근&상체 운동(체험)"},
            {"day": 2, "lecture_id": 164, "type": "drill", "title": "허벅지 집중 운동(체험)"},
            {"day": 3, "lecture_id": 162, "type": "drill", "title": "코어 강화 운동(체험)"},
            {"day": 4, "lecture_id": 163, "type": "drill", "title": "엉덩이 자극 집중 운동(체험)"},
            {"day": 5, "lecture_id": 166, "type": "drill", "title": "운동량 up! 전신 유산소 운동(체험)"},
            {"day": 6, "lecture_id": 165, "type": "drill", "title": "왕초보 전신&하체 운동(체험)"}
        ],
    },
    "기타": {
        # 무료 체험 강의 편성에는 없는 종목이지만, 써킷 트레이닝으로 부여함(단, 서킷 트레이닝을 이미 선택한 유저의 경우 중복을 제거한다)(https://circlincoltd.slack.com/archives/C01BY52TMPZ/p1646665898210579)
        "M": [
            {"day": 0, "lecture_id": 160, "type": "drill", "title": "왕초보 전신&팔 운동(체험)"},
            {"day": 1, "lecture_id": 161, "type": "drill", "title": "누워서 하는 복근&상체 운동(체험)"},
            {"day": 2, "lecture_id": 164, "type": "drill", "title": "허벅지 집중 운동(체험)"},
            {"day": 3, "lecture_id": 162, "type": "drill", "title": "코어 강화 운동(체험)"},
            {"day": 4, "lecture_id": 163, "type": "drill", "title": "엉덩이 자극 집중 운동(체험)"},
            {"day": 5, "lecture_id": 166, "type": "drill", "title": "운동량 up! 전신 유산소 운동(체험)"},
            {"day": 6, "lecture_id": 165, "type": "drill", "title": "왕초보 전신&하체 운동(체험)"}
        ],
        "W": [
            {"day": 0, "lecture_id": 160, "type": "drill", "title": "왕초보 전신&팔 운동(체험)"},
            {"day": 1, "lecture_id": 161, "type": "drill", "title": "누워서 하는 복근&상체 운동(체험)"},
            {"day": 2, "lecture_id": 164, "type": "drill", "title": "허벅지 집중 운동(체험)"},
            {"day": 3, "lecture_id": 162, "type": "drill", "title": "코어 강화 운동(체험)"},
            {"day": 4, "lecture_id": 163, "type": "drill", "title": "엉덩이 자극 집중 운동(체험)"},
            {"day": 5, "lecture_id": 166, "type": "drill", "title": "운동량 up! 전신 유산소 운동(체험)"},
            {"day": 6, "lecture_id": 165, "type": "drill", "title": "왕초보 전신&하체 운동(체험)"}
        ],
    }
}


def replace_text_to_level(level_text: str):
    if level_text == '매우 약하게':
        level = -1
    elif level_text == '약하게':
        level = 0
    elif level_text == '보통':
        level = 1
    elif level_text == '강하게':
        level = 2
    else:
        level = 3  # '매우 강하게'
    return level


def send_aligo_free_trial(phone, nickname):
    send_aligo = requests.post(
        "https://api.circlinplus.co.kr/api/aligo/message",
        json={
            "phone": phone,
            "message": f"써클인플러스 무료체험 시작 알림 \
            \
            {nickname}님, 환영합니다! 조금 전에 작성해 주신 사전 설문 내용을 꼼꼼히 읽어보고, {nickname}님께 꼭 맞는 운동의 체험 강의를 보내드렸어요! \
            아래 링크에서 '써클인플러스' App을 다운받고, {nickname}을 위해 준비된 맞춤 강의와 함께 즐겁게 운동을 시작해 보세요! \
            \
            앱 다운로드: https://www.circlinplus.co.kr/landing \
            \
            * 무료체험 기간은 현재 시각부터 1주일로 자동 적용되며, 제공해드린 무료체험 운동 강의는 써클인 플러스 앱을 통해서만 시청 가능하니 앱스토어/구글 플레이스토어에서 꼭! 앱을 다운받아 주세요 :)"
            # "rdate": 'YYYYMMDD',  # 예약발송 일자(ex. 20220303)
            # "rtime": 'HHmm'   # 예약발송 시간(ex. 1707)
        }
    ).json()

    return send_aligo['result']
