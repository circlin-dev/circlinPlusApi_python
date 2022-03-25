from datetime import datetime, timedelta
from pypika import MySQLQuery as Query, Table, Order
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


def send_aligo_free_trial(phone, nickname, manager_nickname):
    send_aligo = requests.post(
        # "https://nodejs.circlinplus.co.kr:444/aligo/message",
        "https://api.circlinplus.co.kr/api/aligo/message",
        json={
            "phone": phone,
            "message": f"*써클인플러스 무료체험 시작 알림*\n\n{nickname}님, 환영합니다! \n{nickname}님이 작성해주신 사전 설문에 따라 {nickname}님의 전담 매니저로 '{manager_nickname}'가 배정되었어요!\n지금 써클인플러스 앱을 다운받고, 매니저 채팅창을 확인해 보세요!\n\n앱 다운로드: https://www.circlinplus.co.kr/landing"
            # "message": f"*써클인플러스 무료체험 시작 알림*\n\n{nickname}님, 환영합니다! \n조금 전에 작성해 주신 사전 설문 내용을 꼼꼼히 읽어보고, {nickname}님께 꼭 맞는 운동의 체험 강의를 보내드렸어요!\n\n아래 링크에서 '써클인플러스' App을 다운받고, {nickname}님을 위해 준비된 맞춤 강의와 함께 즐겁게 운동을 시작해 보세요!\n\n앱 다운로드: https://www.circlinplus.co.kr/landing \n\n* 무료체험 기간은 현재 시각부터 1주일 이후 일시로 자동 적용됩니다.\n제공해드린 무료체험 운동 강의는 써클인 플러스 앱을 통해서만 시청 가능하니 앱스토어/구글 플레이스토어에서 꼭! 앱을 다운받아 주세요 :)"
            # "rdate": 'YYYYMMDD',  # 예약발송 일자(ex. 20220303)
            # "rtime": 'HHmm'   # 예약발송 시간(ex. 1707)
        }
    ).json()

    return send_aligo['result']


def manager_by_gender(gender):
    if gender == 'M':
        manager_id = 28  # 28 = 매니저 JHONE, 18 = 매니저 HJ
    else:
        manager_id = 18
    return manager_id


def build_chat_message(user_nickname, manager_nickname):
    # index 0: 신청 당일

    now = datetime.now()
    now_2m = (now + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:00")
    now_1h = (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:00")

    d1_0802 = (now + timedelta(days=1)).strftime("%Y-%m-%d 08:02:00")
    d1_1145 = (now + timedelta(days=1)).strftime("%Y-%m-%d 11:45:00")
    d1_1522 = (now + timedelta(days=1)).strftime("%Y-%m-%d 15:22:00")
    d1_1820 = (now + timedelta(days=1)).strftime("%Y-%m-%d 18:20:00")
    d1_2112 = (now + timedelta(days=1)).strftime("%Y-%m-%d 21:12:00")

    d2_0730 = (now + timedelta(days=2)).strftime("%Y-%m-%d 07:30:00")
    d2_1005 = (now + timedelta(days=2)).strftime("%Y-%m-%d 10:05:00")
    d2_1221 = (now + timedelta(days=2)).strftime("%Y-%m-%d 12:21:00")
    d2_1430 = (now + timedelta(days=2)).strftime("%Y-%m-%d 14:30:00")
    d2_1603 = (now + timedelta(days=2)).strftime("%Y-%m-%d 16:03:00")
    d2_1810 = (now + timedelta(days=2)).strftime("%Y-%m-%d 18:10:00")
    d2_2019 = (now + timedelta(days=2)).strftime("%Y-%m-%d 20:19:00")
    d2_2200 = (now + timedelta(days=2)).strftime("%Y-%m-%d 22:00:00")

    d3_0749 = (now + timedelta(days=3)).strftime("%Y-%m-%d 07:49:00")
    d3_1132 = (now + timedelta(days=3)).strftime("%Y-%m-%d 11:32:00")
    d3_1552 = (now + timedelta(days=3)).strftime("%Y-%m-%d 15:52:00")
    d3_1902 = (now + timedelta(days=3)).strftime("%Y-%m-%d 19:02:00")
    d3_2139 = (now + timedelta(days=3)).strftime("%Y-%m-%d 21:39:00")

    d4_0850 = (now + timedelta(days=4)).strftime("%Y-%m-%d 08:50:00")
    d4_1100 = (now + timedelta(days=4)).strftime("%Y-%m-%d 11:00:00")
    d4_1407 = (now + timedelta(days=4)).strftime("%Y-%m-%d 14:07:00")
    d4_1830 = (now + timedelta(days=4)).strftime("%Y-%m-%d 18:30:00")
    d4_2042 = (now + timedelta(days=4)).strftime("%Y-%m-%d 20:42:00")

    d5_0830 = (now + timedelta(days=5)).strftime("%Y-%m-%d 08:30:00")
    d5_1121 = (now + timedelta(days=5)).strftime("%Y-%m-%d 11:21:00")
    d5_1720 = (now + timedelta(days=5)).strftime("%Y-%m-%d 17:20:00")
    d5_2045 = (now + timedelta(days=5)).strftime("%Y-%m-%d 20:45:00")

    d6_0841 = (now + timedelta(days=6)).strftime("%Y-%m-%d 08:41:00")
    d6_1103 = (now + timedelta(days=6)).strftime("%Y-%m-%d 11:03:00")
    d6_1844 = (now + timedelta(days=6)).strftime("%Y-%m-%d 18:44:00")
    d6_2209 = (now + timedelta(days=6)).strftime("%Y-%m-%d 22:09:00")

    # Test time scheduling.
    # now_2m = (now + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
    # now_1h = (now + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")
    #
    # d1_0802 = (now + timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S")
    # d1_1145 = (now + timedelta(minutes=4)).strftime("%Y-%m-%d %H:%M:%S")
    # d1_1522 = (now + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    # d1_1820 = (now + timedelta(minutes=6)).strftime("%Y-%m-%d %H:%M:%S")
    # d1_2112 = (now + timedelta(minutes=7)).strftime("%Y-%m-%d %H:%M:%S")
    #
    # d2_0730 = (now + timedelta(minutes=8)).strftime("%Y-%m-%d %H:%M:%S")
    # d2_1005 = (now + timedelta(minutes=9)).strftime("%Y-%m-%d %H:%M:%S")
    # d2_1221 = (now + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    # d2_1430 = (now + timedelta(minutes=11)).strftime("%Y-%m-%d %H:%M:%S")
    # d2_1603 = (now + timedelta(minutes=12)).strftime("%Y-%m-%d %H:%M:%S")
    # d2_1810 = (now + timedelta(minutes=13)).strftime("%Y-%m-%d %H:%M:%S")
    # d2_2019 = (now + timedelta(minutes=14)).strftime("%Y-%m-%d %H:%M:%S")
    # d2_2200 = (now + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    #
    # d3_0749 = (now + timedelta(minutes=16)).strftime("%Y-%m-%d %H:%M:%S")
    # d3_1132 = (now + timedelta(minutes=17)).strftime("%Y-%m-%d %H:%M:%S")
    # d3_1552 = (now + timedelta(minutes=18)).strftime("%Y-%m-%d %H:%M:%S")
    # d3_1902 = (now + timedelta(minutes=19)).strftime("%Y-%m-%d %H:%M:%S")
    # d3_2139 = (now + timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S")
    #
    # d4_0850 = (now + timedelta(minutes=21)).strftime("%Y-%m-%d %H:%M:%S")
    # d4_1100 = (now + timedelta(minutes=22)).strftime("%Y-%m-%d %H:%M:%S")
    # d4_1407 = (now + timedelta(minutes=23)).strftime("%Y-%m-%d %H:%M:%S")
    # d4_1830 = (now + timedelta(minutes=24)).strftime("%Y-%m-%d %H:%M:%S")
    # d4_2042 = (now + timedelta(minutes=25)).strftime("%Y-%m-%d %H:%M:%S")
    #
    # d5_0830 = (now + timedelta(minutes=26)).strftime("%Y-%m-%d %H:%M:%S")
    # d5_1121 = (now + timedelta(minutes=27)).strftime("%Y-%m-%d %H:%M:%S")
    # d5_1720 = (now + timedelta(minutes=28)).strftime("%Y-%m-%d %H:%M:%S")
    # d5_2045 = (now + timedelta(minutes=29)).strftime("%Y-%m-%d %H:%M:%S")
    #
    # d6_0841 = (now + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    # d6_1103 = (now + timedelta(minutes=31)).strftime("%Y-%m-%d %H:%M:%S")
    # d6_1844 = (now + timedelta(minutes=32)).strftime("%Y-%m-%d %H:%M:%S")
    # d6_2209 = (now + timedelta(minutes=33)).strftime("%Y-%m-%d %H:%M:%S")

    daily_messages = {
        0: [
            {"order": 0,
             "time": now_2m,
             "message": f"안녕하세요, {user_nickname}님! 🥳\n저는 {user_nickname}님의 무료체험 매니저로 배정된 {manager_nickname}입니다 :)"
             },
            {"order": 1,
             "time": now_2m,
             "message": "비록 지금은 무료체험 기간이라\n제가 메시지를 발송하는 것만 가능하지만!"
             },
            {"order": 2,
             "time": now_2m,
             "message": "체험 후에 이용권을 결제하시면,\n저와 실시간으로 메시지를 주고 받을 수 있답니다!"
             },
            {"order": 3,
             "time": now_2m,
             "message": f"우선 사전 설문지에 작성해주신 내용을 참고해서\n{user_nickname}님이 관심있어하실만한 프로그램으로"
             },
            {"order": 4,
             "time": now_2m,
             "message": "무료 체험 강의를 일정에 맞춰 세팅해두었어요!\n마이페이지에서 확인해보세요~! :)"
             },
            {"order": 5,
             "time": now_2m,
             "message": f"그리고 내일부터 제가\n{user_nickname}님이 더 건강한 하루를 보내실 수 있도록"
             },
            {"order": 6,
             "time": now_2m,
             "message": "매일매일 다른 미션을 드리려고해요! 😉\n제가 쪼끔 귀찮게 메시지를 보내더라도"
             },
            {"order": 7,
             "time": now_2m,
             "message": "한 주동안 미션을 잘 따라오시면\n이전보다 훨씬 더 건강한 한주를 보내실 수 있을거예요 ㅎㅎ"
             },

            {"order": 0,
             "time": now_1h,
             "message": "아참참! 그리고 제가 써클인플러스\n2만원 할인 쿠폰 코드를 알려드릴건데요 😎"
             },
            {"order": 1,
             "time": now_1h,
             "message": "매일 제가 드리는 메시지 잘 읽으시도록\n메시지들 사이에 한글자씩 숨겨서 알려드릴게요 😏"
             },
            {"order": 2,
             "time": now_1h,
             "message": "그럼 우선 첫 글자!\n[ 쿠폰코드 : C______ ]"
             }
        ],
        1: [
            {"order": 0,
             "time": d1_0802,
             "message": f"{user_nickname}님~! 좋은 아침이예요! :)"
             },
            {"order": 1,
             "time": d1_0802,
             "message": "오늘의 미션은 가볍게 \"30분 걷기\" 입니다! \n딱 30분만 시간 내어서 바깥에서 걸어보는 거예요!\n어려운 미션이 아니니 분명 달성하실 수 있으시겠죠?! ㅎㅎ"
             },
            {"order": 2,
             "time": d1_0802,
             "message": f"{user_nickname}님과 대화 할 수 있다면\n오늘 몇 시쯤 걸으실 수 있는지 여쭤보고\n제가 {user_nickname}님과 딱!! 약속 시간을 정해서\n그 시간에 맞춰서 걷고 계신지 채팅 드렸을텐데, 아쉬워요 ㅠ.ㅠ!"
             },
            {"order": 3,
             "time": d1_0802,
             "message": f"{user_nickname}님과 대화할 수 있는 날을 기대해 볼게요ㅎㅎ"
             },

            {"order": 0,
             "time": d1_1145,
             "message": f"{user_nickname}님!\n점심식사 하실 때가 된 것 같아서 메시지 드려요 ㅎㅎ"
             },
            {"order": 1,
             "time": d1_1145,
             "message": "오늘은 어떤 메뉴를 드시려나요?!\n벌써 이른 점심을 드셨으려나요? ㅎㅎ"
             },
            {"order": 2,
             "time": d1_1145,
             "message": "운동도 운동이지만,\n진짜 건강하게 먹는 습관이 중요하더라구요!"
             },
            {"order": 3,
             "time": d1_1145,
             "message": "아직 식사 전이시라면,\n오늘 메뉴는 쪼끔 더 건강한 메뉴로! :)"
             },
            {"order": 4,
             "time": d1_1145,
             "message": "그럼 오늘 남은 하루도 파잇팅입니다!"
             },

            {"order": 0,
             "time": d1_1522,
             "message": f"{user_nickname}님!\n저는 지금 딱 자리에서 일어나서\n스트레칭을 쭈욱쭈욱 해줬어요! :)"
             },
            {"order": 1,
             "time": d1_1522,
             "message": "이런 작은 습관 하나하나가 쌓여서\n하루의 피로도를 확 낮춰주거든요!"
             },
            {"order": 2,
             "time": d1_1522,
             "message": f"{user_nickname}님도 지금 한번 자리에서 일어나서\n온몸을 쭉쭉 스트레칭 한번 하셔요😁"
             },
            {"order": 3,
             "time": d1_1522,
             "message": "오늘의 미션 \"30분 걷기\"도 잊지 않으셨죠?!"
             },

            {"order": 0,
             "time": d1_1820,
             "message": f"{user_nickname}님 퇴근하셨나요~?ㅎㅎ\n앗, 직장인이 아니실 수도 있겠네요!"
             },
            {"order": 1,
             "time": d1_1820,
             "message": "제가 관리하고 있는 회원님들께는\n평소 생활 패턴이 어떠신지 많이 여쭙고"
             },
            {"order": 2,
             "time": d1_1820,
             "message": f"개별 생활 패턴에 알맞게끔 관리를 해드리고 있는데\n{user_nickname}님의 평소 생활 패턴도 어떠실지 궁금하네요! :)"
             },
            {"order": 3,
             "time": d1_1820,
             "message": "오늘 제가 드린 미션 \"30분 걷기\"는 하셨나요?ㅎㅎ\n아니면 곧 하러 가시려나요?!"
             },
            {"order": 4,
             "time": d1_1820,
             "message": "아직 전이라면, 걸을 때는 배에 딱 힘주고!\n파워워킹!ㅎㅎ 아시죠?!"
             },

            {"order": 0,
             "time": d1_2112,
             "message": "앗, 벌써 9시가 넘었네요! ㅎㅎ\n오늘은 어제보다 조금 더 건강한 하루를 보내셨나요?!"
             },
            {"order": 1,
             "time": d1_2112,
             "message": "아직 \"30분 걷기\" 전이라면, 지금도 늦지 않았어요!\n오늘을 건강하게 마무리해보세요! :)"
             },
            {"order": 2,
             "time": d1_2112,
             "message": "아참 할인 쿠폰 코드의 두번째 글자를 알려드릴게요!\n[ 쿠폰코드 : CI_____ ]"
             },
            {"order": 3,
             "time": d1_2112,
             "message": "벌써 감 잡으셨나요?ㅎㅎ\n아직 나머지 글자를 알려드리지 않았으니 속단은 금물이예요! :)"
             },
            {"order": 4,
             "time": d1_2112,
             "message": "내일도 가벼운 미션을 드릴테니,\n오늘 푹 주무시고 내일도 우리 팟팅해보아요! ㅎㅎ"
             },
        ],
        2: [
            {"order": 0,
             "time": d2_0730,
             "message": f"{user_nickname}님, 굳모닝입니다~!ㅎㅎ\n오늘의 데일리 미션, \"물 2L 마시기\"입니다!"
             },
            {"order": 1,
             "time": d2_0730,
             "message": "물만 잘 마셔도 우리 몸에서 칼로리를 더 많이\n소모한다는 사실 알고 계셨나요?!"
             },
            {"order": 2,
             "time": d2_0730,
             "message": "뇌에서는 갈증을 허기로 착각해서\n물을 많이 안마시면 식욕이 더 늘기도 해요! 🐷"
             },
            {"order": 3,
             "time": d2_0730,
             "message": "오늘은 제가 메시지를 드릴 때 마다\n의식적으로 물을 한컵씩 마셔보는 거예요!!"
             },
            {"order": 4,
             "time": d2_0730,
             "message": "그럼 일단 제 메시지를 보신 지금!ㅎㅎ\n물 한 컵 원샷해 보실까요?! :)"
             },

            {"order": 0,
             "time": d2_1005,
             "message": f"{user_nickname}님, 물 한컵 마실 시간이예요~!ㅎㅎ\n오늘은 \"물 2L 마시기\"를 위해서\n조금 더 자주자주 메시지를 드려보려구요!"
             },
            {"order": 1,
             "time": d2_1005,
             "message": "평소 소화기관이 약한 편이시라면\n물은 찬 물 보단 따뜻하거나 미지근한 물이 좋아요!"
             },
            {"order": 2,
             "time": d2_1005,
             "message": "저는 원래 완전 찬물파였는데,\n며칠 미지근한 물을 먹어버릇 했더니\n금방 익숙해지더라구요! ㅎㅎ"
             },
            {"order": 3,
             "time": d2_1005,
             "message": "생수를 마시는 걸 어려워하시는 편이라면\n차를 우려 드셔보세요!"
             },
            {"order": 4,
             "time": d2_1005,
             "message": "자주 붓는 편이라면 호박티도 좋아요~!"
             },

            {"order": 0,
             "time": d2_1221,
             "message": f"{user_nickname}님~! 점심 드셨나요?ㅎㅎ\n물 한컵 챙겨 드세요! :)"
             },
            {"order": 1,
             "time": d2_1221,
             "message": "혹시 \"물 2L 마시기\"에 커피를 포함하진 않으셨죠?!"
             },
            {"order": 2,
             "time": d2_1221,
             "message": "커피나 녹차는 이뇨작용을 하기 때문에\n커피는 포함시키면 안됩니다~! ㅎㅎ"
             },

            {"order": 0,
             "time": d2_1430,
             "message": f"{user_nickname}님! 저 또 왔어요~! 🙌\n물 챙겨드시라고 메시지 보내요!"
             },
            {"order": 1,
             "time": d2_1430,
             "message": "시간이 두 시가 넘어서 점심 이미 드셨을 거 같은데,\n오늘도 건강한 점심식사 하셨나요?!ㅎㅎ"
             },
            {"order": 2,
             "time": d2_1430,
             "message": "식사 전에 물 한컵을 딱 원샷하면\n식사량을 줄일 수 있어요 :)"
             },
            {"order": 3,
             "time": d2_1430,
             "message": "평소 배가 적당히 부를 때에 수저를 딱 놓지 못하고\n과식하는 편이시라면 식사 전에 물 한컵 드셔보세요!"
             },

            {"order": 0,
             "time": d2_1603,
             "message": f"{user_nickname}님~! 물 드세요 물~!ㅎㅎ\n물 많이 마시니 화장실 엄청 자주 들락날락 하게되죠? :)"
             },
            {"order": 1,
             "time": d2_1603,
             "message": "화장실 가실 때 마다 기지개도 한번씩\n쫙쫙 펴주시고요! ㅎㅎ"
             },
            {"order": 2,
             "time": d2_1603,
             "message": "이따 저녁때쯤 오늘의 할인 쿠폰 코드 글자도 알려드릴게요!"
             },
            {"order": 3,
             "time": d2_1603,
             "message": "그럼 오늘 남은 하루도 팟팅입니다~!\n한 두시간 뒤에 또 물 알림 메시지 드릴게요 ㅎㅎ"
             },

            {"order": 0,
             "time": d2_1810,
             "message": f"{user_nickname}님, 또 물 한컵 원샷해주세요~! :)"
             },
            {"order": 1,
             "time": d2_1810,
             "message": "벌써 저녁이 되었네요ㅎㅎ\n오늘 평소보다 화장실 진짜 많이 가셨을 거 같은데,\n어떠신가요?ㅎㅎ"
             },
            {"order": 2,
             "time": d2_1810,
             "message": "오늘 하루만 딱 해보는거지만,\n가능하시다면 내일도 모레도 제가 메시지 드릴 때마다\n물 한컵씩 챙겨 마셔주시면 금방 습관 되실 거에요!"
             },

            {"order": 0,
             "time": d2_2019,
             "message": f"{user_nickname}님! 물 한컵 또 챙겨드시구요ㅎㅎ\n이따 10시쯤 마지막 물 한컵! 메시지 드릴게요~!"
             },
            {"order": 1,
             "time": d2_2019,
             "message": f"{user_nickname}님이 몇시에 주무시는지 알면\n마지막 물 알림을 수면 2시간 전 쯤으로 드릴텐데..!\n{user_nickname}님의 답변을 듣고싶네요ㅎ_ㅎ"
             },
            {"order": 2,
             "time": d2_2019,
             "message": f"아참, 오늘의 쿠폰 코드! 세번째 글자 알려드립니다~!\n[ 쿠폰코드 : CIR____ ]"
             },

            {"order": 0,
             "time": d2_2200,
             "message": f"{user_nickname}님 마지막 물 한컵~!ㅎㅎ\n오늘의 미션 \"물 2L 마시기\"는 성공하셨나요?"
             },
            {"order": 1,
             "time": d2_2200,
             "message": f"답장을 못 받으니 {user_nickname}님 오늘 어떠셨는지\n잘 따라오고 계시는건지 궁금하네요😣"
             },
            {"order": 2,
             "time": d2_2200,
             "message": f"{user_nickname}님께 짜 드리고 싶은 운동 플랜과\n{user_nickname}님에게 딱! 추천드리고 싶은 기구들도 많은데\n무료 체험 기간에는 제한적이라 너무 아쉬워요😢"
             },
            {"order": 3,
             "time": d2_2200,
             "message": f"체험 기간이 끝나면 꼭 2만원 할인 쿠폰 쓰셔서\n{user_nickname}님 맞춤 운동 플랜과 기구들을 받아보세요!"
             },
            {"order": 4,
             "time": d2_2200,
             "message": f"그럼 오늘 하루도 고생 많으셨습니다~!🙌"
             },
        ],
        3: [
            {"order": 0,
             "time": d3_0749,
             "message": f"좋은 아침이예요, {user_nickname}님! :)\n오늘의 미션은 \"단백질 챙겨먹기\"예요! ㅎㅎ"
             },
            {"order": 1,
             "time": d3_0749,
             "message": "저는 매일 섭취 칼로리를 계산하고 기록하는데요!"
             },
            {"order": 2,
             "time": d3_0749,
             "message": "다른 회원님들 식사하시는 것도 한번 기록해보니깐\n단백질은 의식적으로 더 챙겨먹지 않으면\n매번 하루 권장량을 다들 못 채우시더라구요ㅠ_ㅠ"
             },
            {"order": 3,
             "time": d3_0749,
             "message": f"{user_nickname}님도 오늘 하루만큼은 의식해서 단백질 더 챙겨드셔보는거예요!"
             },
            {"order": 4,
             "time": d3_0749,
             "message": "이따 식사하실 때 단백질이 좀 부족하다면\n편의점에서 파는 단백질 식품을 챙겨드셔도 좋습니다 :)"
             },
            {"order": 5,
             "time": d3_0749,
             "message": "그럼 오늘 하루도 건강하게!! 팟팅이에요! ㅎㅎ"
             },

            {"order": 0,
             "time": d3_1132,
             "message": f"{user_nickname}님, 점심드실 때가 다 된 거 같아서\n오늘 \"단백질 챙겨먹기\" 잊어버리셨을까봐\n한번 더 알려드려요 ㅎㅎ"
             },
            {"order": 1,
             "time": d3_1132,
             "message": "오늘 점심 메뉴는 단백질 많은 메뉴로 선택! 아시죠?!😉"
             },

            {"order": 0,
             "time": d3_1552,
             "message": f"{user_nickname}님! 오늘 하루도 건강하게 잘 보내고 계신가요 ㅎㅎ\n기지개 한번 쭉 펴주세요!"
             },
            {"order": 1,
             "time": d3_1552,
             "message": "아참, 오늘 간식으로 삶은 계란 드시는 것도 좋아요!\n계란 하나에는 약 6g의 단백질이 들었거든요 :)"
             },

            {"order": 0,
             "time": d3_1902,
             "message": f"{user_nickname}님 저녁 식사는 하셨나요? :)"
             },
            {"order": 1,
             "time": d3_1902,
             "message": "오늘 미션은 평소 단백질을 크게 신경쓰고 계시지 않았다면\n어떤 걸 먹어야 할지, 얼마나 먹어야 할지도\n참 어려우셨을 것 같아요 ㅠ_ㅠ!"
             },
            {"order": 2,
             "time": d3_1902,
             "message": f"대화가 가능하다면, 제가 바로바로 메뉴 추천도 해드리고\n{user_nickname}님 질문에 답변도 드릴 수 있을텐데\n오늘도 아쉽네용 ㅠㅠ..!"
             },
            {"order": 3,
             "time": d3_1902,
             "message": "그런 의미에서(?)! 할인 쿠폰 네번째 글자를 알려드릴게요!\n[ 쿠폰코드 : CIRC___ ]"
             },
            {"order": 4,
             "time": d3_1902,
             "message": "나머지 글자가 뭔지 이제 눈에 보이는 것 같죠?ㅎㅎㅎㅎㅎ\n뭔지 눈치채셨다면, 지금도 바로 사용해보세요! :)"
             },

            {"order": 0,
             "time": d3_2139,
             "message": f"{user_nickname}님 오늘도 수고하셨습니다 :)"
             },
            {"order": 1,
             "time": d3_2139,
             "message": "저랑 함께 하신지 4일이 되셨는데,\n이전보다 건강한 4일을 보내셨을지 궁금하네요~!"
             },
            {"order": 2,
             "time": d3_2139,
             "message": f"오늘도 {user_nickname}님의 답변은 못 듣지만ㅎㅎ\n잘 따라와주시고 있을 거란 믿음을 가지고 있어요! :)\n그렇죠?! ㅎㅎ"
             },
            {"order": 3,
             "time": d3_2139,
             "message": "그럼 오늘도 푹 주무시고,\n내일 아침에 새로운 미션으로 메시지 드릴게요!"
             },
            {"order": 4,
             "time": d3_2139,
             "message": "굳나잇 되세요~!"
             }
        ],
        4: [
            {"order": 0,
             "time": d4_0850,
             "message": f"{user_nickname}님, 푹 주무셨나요? :)\n오늘의 미션은 \"까치발 100번하기\"예요!"
             },
            {"order": 1,
             "time": d4_0850,
             "message": "종아리는 제 2의 심장이라고 불리기도 해요!\n심장에서 나온 피를 다시 거꾸로 올려주는 근육인데요~!"
             },
            {"order": 2,
             "time": d4_0850,
             "message": "평소에 우리는 종아리 근육을 쓸 일이 거의 없어서\n이렇게 의식적으로 써주지 않으면\n혈액순환이 원활하지 못해 하체부종의 원인이 되어요😫"
             },
            {"order": 3,
             "time": d4_0850,
             "message": "제가 오늘은 다섯 타임으로 메시지를 드릴건데요!\n제 메시지를 받을 때 마다\n앉아서 또는 일어나서 까치발을 2초씩 20번 해주세요!"
             },
            {"order": 4,
             "time": d4_0850,
             "message": "종아리에 힘이 꽉 들어오도록이요💪\n이 정도로 종아리가 굵어지진 않으니 걱정마시구요! ㅎㅎ\n그럼 일단 지금 20번! 한번 해 볼까요?!"
             },

            {"order": 0,
             "time": d4_1100,
             "message": f"{user_nickname}님, 지금 앉아계시나요 일어서 계시나요?ㅎㅎ"
             },
            {"order": 1,
             "time": d4_1100,
             "message": "2초씩 지그시 까치발로 힘줬다 풀었다를\n스무번 반복해보세요!"
             },
            {"order": 2,
             "time": d4_1100,
             "message": "쥐가 나시는 분들도 종종 계신데\n쥐가 나신다면 힘을 과도하게 주지 않으셔도 괜찮아요 :)"
             },

            {"order": 0,
             "time": d4_1407,
             "message": f"{user_nickname}님, 한번 더 2초씩 20번 진행해보실까요?ㅎㅎ\n일어서 계시다면 벽을 잡고 진행하셔도 좋아요!"
             },
            {"order": 1,
             "time": d4_1407,
             "message": "까치발을 내릴 때 더 깊숙히 내릴 수 있도록\n계단 위나 문턱 위에 발 앞쪽만 대고 진행해주시면\n훨씬 효과적이에요 :)"
             },

            {"order": 0,
             "time": d4_1830,
             "message": f"{user_nickname}님~! 까치발 네번째 타임이에요ㅎㅎ\n피트니스에서는 이 운동을 \"카프레이즈\"라고 해요! "
             },
            {"order": 1,
             "time": d4_1830,
             "message": "카프레이즈라고 인터넷에 검색해보시면,\n무거운 덤벨을 들고 하는 사람들도 볼 수 있으실텐데요!"
             },
            {"order": 2,
             "time": d4_1830,
             "message": "종아리 근육은 대부분 선천적인 요소로 크기가 결정되기 때문에\n이 운동을 아무리 열심히 해도 종아리가 쉬이 굵어지진 않아요ㅎㅎ"
             },
            {"order": 3,
             "time": d4_1830,
             "message": "대신 안 쓰던 근육을 써서 뭉칠 수 있으니까\n오늘 자기 전에 좀 주물러 주시구요! :)"
             },

            {"order": 0,
             "time": d4_2042,
             "message": "오늘의 마지막 까치발 타임 :)"
             },
            {"order": 1,
             "time": d4_2042,
             "message": "혹시 놓친 타임이 있다면 \n마지막 타임에 횟수를 더해서 진행해 주세요!"
             },
            {"order": 2,
             "time": d4_2042,
             "message": "오늘 주무시기 전에 종아리 주물주물해 주시고요 :)"
             },
            {"order": 3,
             "time": d4_2042,
             "message": "그리고 오늘의 할인 쿠폰 코드 글자!\n[ 쿠폰코드 : CIRCL__ ]\n아직도 눈치 못채신 건 아니겠죠?ㅎㅎ"
             },
            {"order": 4,
             "time": d4_2042,
             "message": "쿠폰은 이용권 결제 시에 결제 페이지에서 입력하면\n바로 할인이 적용됩니다 :)"
             },
        ],
        5: [
            {"order": 0,
             "time": d5_0830,
             "message": f"좋은 아침이에요, {user_nickname}님~! ㅎㅎ"
             },
            {"order": 1,
             "time": d5_0830,
             "message": "종아리는 괜찮으신가요? :)\n평소 잘 안쓰는 근육이라 알이 배기셨을 수도 있어요!"
             },
            {"order": 2,
             "time": d5_0830,
             "message": "오늘의 미션은 \"식사 직후 15분 걷기\"에요!\n점심시간이 짧으시다면, 저녁 식사 후에만 걸으셔도 괜찮아요 :)"
             },
            {"order": 3,
             "time": d5_0830,
             "message": "식사 후에는 우리 몸의 혈당 수치가 높아지는데\n이때 우리 몸에 지방이 축적되기가 아주 쉽거든요ㅠ_ㅠ"
             },
            {"order": 4,
             "time": d5_0830,
             "message": "식사 후에 바로 앉거나 눕지 말고\n신체를 움직여 주세요!"
             },

            {"order": 0,
             "time": d5_1121,
             "message": f"{user_nickname}님, 오늘 식사 후에 15분 걷기! 기억하시죠?ㅎㅎ"
             },
            {"order": 1,
             "time": d5_1121,
             "message": "살 안찌는 사람들을 살펴보면\n이런 작은 습관들 덕분에 살이 잘 안 찌더라구요!"
             },

            {"order": 0,
             "time": d5_1720,
             "message": f"{user_nickname}님!\n저녁 식사 후에 15분 걷기!"
             },
            {"order": 1,
             "time": d5_1720,
             "message": "곧 저녁 드실 거 같아서 잊지 마시라고\n메시지 드려요 ㅎㅎ"
             },
            {"order": 2,
             "time": d5_1720,
             "message": "점심때 못 걸으셨다면 저녁 식사 후에 조금 더 걸어주세요!"
             },

            {"order": 0,
             "time": d5_2045,
             "message": f"{user_nickname}님! 6일차 쿠폰 코드 글자 알려드리겠습니다 :)\n[ 쿠폰코드 : CIRCLI_ ]"
             },
            {"order": 1,
             "time": d5_2045,
             "message": "마지막 글자가 무엇일지 짐작하셨다면!\n지금 바로 사용해도 좋아요ㅎㅎ"
             },
            {"order": 2,
             "time": d5_2045,
             "message": "아참 그리고 이 할인 쿠폰은 무료 체험 기간이 끝나고\n일주일 뒤 까지만 유효하다니까 참고해 주세요ㅠ_ㅠ"
             },
            {"order": 3,
             "time": d5_2045,
             "message": "그럼 오늘도 푹 쉬시고요!\n내일 더 건강하게 만나요~!"
             },
        ],
        6: [
            {"order": 0,
             "time": d6_0841,
             "message": f"{user_nickname}님 오늘 마지막 날이네요 :)"
             },
            {"order": 1,
             "time": d6_0841,
             "message": "마지막 쿠폰 코드 글자는..!\n[ 쿠폰코드 : CIRCLIN ]\n이미 짐작하셨다고요?! ㅎㅎ\n그러실 줄 알았어요😌"
             },
            {"order": 2,
             "time": d6_0841,
             "message": "유효기간은 무료 체험 종료일 기준 일주일입니다!"
             },
            {"order": 3,
             "time": d6_0841,
             "message": f"그리고 대망의 마지막 미션은 \"전신 사진 찍기\"입니다!\n거울 앞에서 전신 사진을 찍어주세요 :)\n이 사진은 {user_nickname}님의 BEFORE 사진이 될 거예요ㅎㅎ "
             },
            {"order": 4,
             "time": d6_0841,
             "message": "무료 체험 기간은 끝이 났지만\n오늘을 시작으로 앞으로 매주 1회 전신 사진을 찍어\n나의 신체 변화를 기록하는거에요!"
             },
            {"order": 5,
             "time": d6_0841,
             "message": "꾸준하게 기록해온 눈바디 사진들은\n후에 나에게 강력한 동기부여가 되기도 하거든요!ㅎㅎ"
             },
            {"order": 6,
             "time": d6_0841,
             "message": "시작이 반이니까 꼭! 오늘 딱 30초만 시간 내서\n나의 전신을 사진으로 기록해보세요!"
             },

            {"order": 0,
             "time": d6_1103,
             "message": f"{user_nickname}님, 마지막 날 점심 식사도 건강하게! :)"
             },
            {"order": 1,
             "time": d6_1103,
             "message": "식사 후엔 15분 걷기!\n물도 중간중간 한컵씩 마셔주시고\n카프레이즈 했던 거도 기억나시죠?"
             },
            {"order": 2,
             "time": d6_1103,
             "message": f"{user_nickname}님이 이 중에서 어떤 것들이 어려우셨는지\n어떤 게 제일 좋았는지 듣고싶네요 ㅎㅎ\n"
             },
            {"order": 3,
             "time": d6_1103,
             "message": f"제가 준비한 일주일 미션들이\n{user_nickname}님의 일주일을 조금이나마 건강하게 만들었기를 바래요!"
             },

            {"order": 0,
             "time": d6_1844,
             "message": f"{user_nickname}님, 아침에 미션으로 드렸던\nBEFORE 전신 사진 찍어두셨나요?! ㅎㅎ"
             },
            {"order": 1,
             "time": d6_1844,
             "message": f"앞으로 {user_nickname}님의 마음에 쏙 드는 AFTER를 \n만드실 수 있기를 제가 기도할게요 :)"
             },
            {"order": 2,
             "time": d6_1844,
             "message": "알려드렸던 2만원 할인 쿠폰 코드 기억하시죠?!\n[ 쿠폰코드 : CIRCLIN ]\n이거 유효기간은 체험기간 종료 후 딱 일주일이라는거!\n기억해주시고요 ㅎㅎ"
             },
            {"order": 3,
             "time": d6_1844,
             "message": f"한 주 동안 잘 따라오셨을 거라고 믿고\n다시 만날 날을 기약하며!"
             },
            {"order": 4,
             "time": d6_1844,
             "message": "추가로 \"첫 기구 무료 배송\" 쿠폰을 드릴게요!\n[ 쿠폰코드 : DIDA04 ]"
             },
            {"order": 5,
             "time": d6_1844,
             "message": "무료배송 쿠폰은 이용권 결제 이후에 기구 신청할 때에\n사용하실 수 있습니다 :)"
             },

            {"order": 0,
             "time": d6_2209,
             "message": f"{user_nickname}님~! 마지막 날 주무시기 전에!\n아직 BEFORE 전신 사진 안 찍으셨으면\n꼭 찍어두시라고 메시지 보내요 ㅎㅎ"
             },
            {"order": 1,
             "time": d6_2209,
             "message": f"이 사진이 앞으로 {user_nickname}님의 일상을 확 바꿔\n멋진 AFTER 를 만드시길 바랍니다🎉"
             },
            {"order": 2,
             "time": d6_2209,
             "message": f"그럼 이전보다 더 건강한 일주일 보내셨길 바라면서\n저는 이제 작별 인사를 드릴게요🙌\n{user_nickname}님의 무료체험 {manager_nickname}였습니다!"
             },
        ]
    }

    return daily_messages
