from global_things.constants import SLACK_NOTIFICATION_WEBHOOK, AMAZON_URL, IMAGE_ANALYSYS_SERVER, BUCKET_IMAGE_PATH_BODY_INPUT, BUCKET_IMAGE_PATH_BODY_OUTPUT, BUCKET_IMAGE_PATH_ATFLEE_INPUT
from global_things.functions.slack import slack_error_notification
from datetime import datetime
import boto3
import cv2
import json
import mimetypes
import os
import requests


# region bodylab.py
def standard_healthiness_value(age_group: str, gender: str, weight: float, height: float, bmi: float):
    # 남녀 평균 BMI(ideal_bmi) 근거: https://www.kjfp.or.kr/journal/download_pdf.php?doi=10.21215/kjfp.2021.11.1.81 연구자료 82p 결과.2.비만도에 따른 성별별 분포
    if age_group is None or gender is None or weight is None or height is None or bmi is None:
        return 'Missing data'

    if gender == 'W':
        if age_group == "10대":
            percent = (19.7 + ((19.7 + 21.5) / 2)) / 2
        elif age_group == "20대":
            percent = (22.1 + 22.7) / 2
        elif age_group == "30대":
            percent = (((23.4 + 25.1) / 2) + ((24.0 + 25.7) / 2)) / 2
        elif age_group == "40대":
            percent = (((24.6 + 26.3) / 2) + 26.9) / 2
        elif age_group == "50대":
            percent = (27.6 + (28.2 + 29.8) / 2) / 2
        else:
            percent = (28.2 + 29.8) / 2
        ideal_fat_mass = (weight * percent) / 100
        # if age < 18:
        #     percent = 19.7
        # elif age < 21:
        #     percent = (19.7 + 21.5) / 2
        # elif age < 26:
        #     percent = 22.1
        # elif age < 31:
        #     percent = 22.7
        # elif age < 36:
        #     percent = (23.4 + 25.1) / 2
        # elif age < 41:
        #     percent = (24.0 + 25.7) / 2
        # elif age < 46:
        #     percent = (24.6 + 26.3) / 2
        # elif age < 51:
        #     percent = 26.9
        # elif age < 56:
        #     percent = 27.6
        # else:
        #     percent = (28.2 + 29.8) / 2

        ideal_muscle_mass = weight * 0.34
        ideal_bmi = 22.52
    else:
        if age_group == "10대":
            percent = (9.4 + 10.5) / 2
        elif age_group == "20대":
            percent = (11.6 + (12.7 + 14.6) / 2) / 2
        elif age_group == "30대":
            percent = (((13.7 + 15.7) / 2) + 16.8) / 2
        elif age_group == "40대":
            percent = (17.8 + ((18.9 + 20.7) / 2)) / 2
        elif age_group == "50대":
            percent = (((20.0 + 21.8) / 2) + 22.8) / 2
        else:
            percent = 22.8
        ideal_fat_mass = (weight * percent) / 100

        # if age < 18:
        #     percent = 9.4
        # elif age < 21:
        #     percent = 10.5
        # elif age < 26:
        #     percent = 11.6
        # elif age < 31:
        #     percent = (12.7 + 14.6) / 2
        # elif age < 36:
        #     percent = (13.7 + 15.7) / 2
        # elif age < 41:
        #     percent = 16.8
        # elif age < 46:
        #     percent = 17.8
        # elif age < 51:
        #     percent = (18.9 + 20.7) / 2
        # elif age < 56:
        #     percent = (20.0 + 21.8) / 2
        # else:
        #     percent = 22.8
        ideal_muscle_mass = weight * 0.4
        ideal_bmi = 25.05

    if 0 <= bmi <= 18.5:
        bmi_status = "저체중"
    elif 18.5 < bmi <= 23:
        bmi_status = "정상"
    elif 23 < bmi <= 25:
        bmi_status = "경도비만"
    else:
        bmi_status = "중등도비만"

    return ideal_fat_mass, ideal_muscle_mass, bmi_status, ideal_bmi


def analyze_body_images(user_id, url):
    response = requests.post(
        f"http://{IMAGE_ANALYSYS_SERVER}/analysis",
        json={
            "user_id": user_id,
            "url": url
        })

    if response.status_code == 200:
        return json.dumps({'result': response.json(), 'status_code': 200}, ensure_ascii=False)
    elif response.status_code == 400:
        slack_error_notification(api='/api/bodylab', error_log=response.json()['message'])
        return json.dumps({'error': response.json()['message'], 'status_code': 400}, ensure_ascii=False)
    elif response.status_code == 500:
        slack_error_notification(api='/api/bodylab', error_log=response.json()['message'])
        return json.dumps({'error': response.json()['message'], 'status_code': 500}, ensure_ascii=False)


def analyze_atflee_images(user_id, url):
    return ''


# def get_date_range_from_week(year: str, week_number: str):
#     """
#     Reference: http://mvsourcecode.com/python-how-to-get-date-range-from-week-number-mvsourcecode/
#
#     getDateRangeFromWeek(2022, 2) ==> input<'week'> 기준 (2022, 1) (1.3 ~ 1.9)
#     getDateRangeFromWeek(2022, 53) ==> input<'week'> 기준 (2022, 52) (12.26 ~ 1.1)
#
#     getDateRangeFromWeek(2023, 2) ==> input<'week'> 기준 (2023, 1) (1.2 ~ 1.8)
#     getDateRangeFromWeek(2023, 53) ==> input<'week'> 기준 (2023, 52) (12.25 ~ 12.31)
#
#     getDateRangeFromWeek(2024, 2) ==> input<'week'> 기준 (2024, 1) (1.1 ~ 1.7)       *** getDateRangeFromWeek(2024, 1) == getDateRangeFromWeek(2024, 2)
#     getDateRangeFromWeek(2024, 53) ==> input<'week'> 기준 (2024, 52) (12.23 ~ 12.29)
#     ################################################################################### 이상 input_week + 1 == selected week
#     getDateRangeFromWeek(2025, 1) ==> input<'week'> 기준 (2025, 1) (12.30 ~ 1.5)
#     getDateRangeFromWeek(2025, 52) ==> input<'week'> 기준 (2025, 52) (12.22 ~ 12.28)
#
#     getDateRangeFromWeek(2026, 1) ==> input<'week'> 기준 (2026, 1) (12.29 ~ 1.4)
#     getDateRangeFromWeek(2026, 53) ==> input<'week'> 기준 (2026, 53) (12.28 ~ 1.3)
#     ################################################################################### 이상 input_week == selected week
#     getDateRangeFromWeek(2027, 2) ==> input<'week'> 기준 (2027, 1) (1.4 ~ 1.10)
#     getDateRangeFromWeek(2027, 53) ==> input<'week'> 기준 (2027, 52) (12.27 ~ 1.2)
#
#     getDateRangeFromWeek(2028, 2) ==> input<'week'> 기준 (2028, 1) (1.3 ~ 1.9)
#     getDateRangeFromWeek(2028, 53) ==> input<'week'> 기준 (2028, 52) (12.25 ~ 12.31)
#
#     getDateRangeFromWeek(2029, 2) ==> input<'week'> 기준 (2029, 1) (1.1 ~ 1.7)       *** getDateRangeFromWeek(2029, 1) == getDateRangeFromWeek(2029, 2)
#     getDateRangeFromWeek(2029, 53) ==> input<'week'> 기준 (2029, 52) (12.24 ~ 12.30)
#     ################################################################################### input_week + 1 == selected week
#     getDateRangeFromWeek(2030, 1) ==> input<'week'> 기준 (2030, 1) (12.31 ~ 1.6)
#     getDateRangeFromWeek(2030, 52) ==> input<'week'> 기준 (2030, 52) (12.23 ~ 12.29)
#
#     getDateRangeFromWeek(2031, 1) ==> input<'week'> 기준 (2031, 1) (12.30 ~ 1.5)
#     getDateRangeFromWeek(2031, 52) ==> input<'week'> 기준 (2031, 52) (12.22 ~ 12.28)
#
#     getDateRangeFromWeek(2032, 1) ==> input<'week'> 기준 (2032, 1) (12.29 ~ 1.4)
#     getDateRangeFromWeek(2032, 53) ==> input<'week'> 기준 (2032, 53) (12.27 ~ 1.2)
#     ################################################################################### 이상 input_week == selected week
#     getDateRangeFromWeek(2033, 2) ==> input<'week'> 기준 (2033, 1) (1.3 ~ 1.9)
#     getDateRangeFromWeek(2033, 53) ==> input<'week'> 기준 (2033, 52) (12.26 ~ 1.1)
#
#     getDateRangeFromWeek(2034, 2) ==> input<'week'> 기준 (2034, 1) (1.2 ~ 1.8)
#     getDateRangeFromWeek(2034, 53) ==> input<'week'> 기준 (2034, 52) (12.25 ~ 12.31)
#
#     getDateRangeFromWeek(2035, 2) ==> input<'week'> 기준 (2035, 1) (1.1 ~ 1.7)      *** getDateRangeFromWeek(2035, 1) == getDateRangeFromWeek(2035, 2)
#     getDateRangeFromWeek(2035, 53) ==> input<'week'> 기준 (2035, 52) (12.24 ~ 12.30)
#     ################################################################################### input_week + 1 == selected week
#     getDateRangeFromWeek(2036, 1) ==> input<'week'> 기준 (2036, 1) (12.31 ~ 1.6)
#     getDateRangeFromWeek(2036, 52) ==> input<'week'> 기준 (2036, 52) (12.22 ~ 12.28)
#
#     :param year: year(YYYY)
#     :param week_number: month(mm)
#     # Either (String, String) or (int, int) is OK.
#     # But month format is 'ww', so if value 01~09 and
#     # you want to set parameter type as int, you must convert string 'ww' to int 'w'.
#     :return:
#     """
#     if year in ['2022', '2023', '2024', '2027', '2028', '2029', '2033', '2034', '2035']:
#         corrected_week_number = int(week_number) + 1  # int("01" ~ "09) => 1 ~ 9
#
#         firstdate_of_week = datetime.datetime.strptime(f'{year}-W{int(corrected_week_number)-1}-1', "%Y-W%W-%w").date()
#         lastdate_of_week = firstdate_of_week + datetime.timedelta(days=6.9)
#         return str(firstdate_of_week), str(lastdate_of_week)
#     elif year in ['2025', '2026', '2030', '2031', '2032', '2036']:
#         firstdate_of_week = datetime.datetime.strptime(f'{year}-W{int(week_number)-1}-1', "%Y-W%W-%w").date()
#         lastdate_of_week = firstdate_of_week + datetime.timedelta(days=6.9)
#         return str(firstdate_of_week), str(lastdate_of_week)
# endregion

def generate_resized_image(local_save_path, user_id, category, now, extension, original_image_path):
    # file_name = user_id + now + extension
    # local_image_path = BODY_IMAGE_INPUT_PATH, user_id, file_name
    # 새롭게 생성되는 resized file들은 file_name = user_id + now + {width}w + extension
    original_image = cv2.imread(original_image_path, cv2.IMREAD_COLOR)
    height, width, channel = original_image.shape
    new_widths = [1080, 750, 640, 480, 320, 240, 150]
    resized_image_list = []
    for new_width in new_widths:
        new_height = int(new_width * height / width)

        if new_width > width:  # 확대
            resized_image = cv2.resize(original_image,
                                       dsize=(new_width, new_height),
                                       interpolation=cv2.INTER_LINEAR)
        else:                  # 축소(<) or 유지(=)
            resized_image = cv2.resize(original_image,
                                       dsize=(new_width, new_height),
                                       interpolation=cv2.INTER_AREA)

        original_name = f'bodylab_{category}_input_{user_id}_{now}.{extension}'
        file_name = f'bodylab_{category}_input_{user_id}_{now}_{new_width}w.{extension}'
        resized_image_path = f'{local_save_path}/{user_id}/{file_name}'

        if category == 'body':
            object_name = f'{BUCKET_IMAGE_PATH_BODY_INPUT}/{user_id}/{file_name}'
        else:
            object_name = f'{BUCKET_IMAGE_PATH_ATFLEE_INPUT}/{user_id}/{file_name}'
        cv2.imwrite(resized_image_path, resized_image)
        image_dict = {
            # For DB when INSERT
            'pathname': f'{AMAZON_URL}/{object_name}',
            'original_name': original_name,
            'mime_type': get_image_information(resized_image_path)['mime_type'],
            'size': get_image_information(resized_image_path)['size'],
            'width': new_width,
            'height': new_height,
            # For Server
            'file_name': file_name,
            'local_path': resized_image_path,
            'object_name': object_name,
        }
        resized_image_list.append(image_dict)
    return resized_image_list


def get_image_information(path):
    result = {
        'mime_type': mimetypes.guess_type(path)[0],
        'size': int(os.path.getsize(path))
    }
    return result


def upload_image_to_s3(file_name, bucket_name, object_name):
    s3_client = boto3.client('s3')

    try:
        s3_client.upload_file(file_name, bucket_name, object_name)
    except Exception as e:
        return str(e)

    return True


def healthiness_score(recommended, mine):
    score = (1 - (abs(recommended - mine) / mine)) * 100
    return score


def attractiveness_score(best_person, mine):
    score = (1 - (abs(best_person - mine) / mine)) * 100
    return score
