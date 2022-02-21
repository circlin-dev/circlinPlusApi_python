from global_things.constants import SLACK_NOTIFICATION_WEBHOOK, AMAZON_URL, IMAGE_ANALYSYS_SERVER, BUCKET_IMAGE_PATH_BODY_INPUT, BUCKET_IMAGE_PATH_BODY_OUTPUT, BUCKET_IMAGE_PATH_ATFLEE_INPUT
from global_things.functions.slack import slack_error_notification
import base64
import boto3
import cv2
import json
import math
import mimetypes
import os
from PIL import Image
import pyheif
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
        slack_error_notification(api='/api/bodylab', error_message=response.json()['message'])
        return json.dumps({'error': response.json()['message'], 'status_code': 400}, ensure_ascii=False)
    elif response.status_code == 500:
        slack_error_notification(api='/api/bodylab', error_message=response.json()['message'])
        return json.dumps({'error': response.json()['message'], 'status_code': 500}, ensure_ascii=False)


def analyze_atflee_images(path):
    try:
        response = requests.post(
            "https://vision.googleapis.com/v1/images:annotate?key=AIzaSyC55mGMIcRGYMFvK2y0m1GYXXlSiDpmpNE",
            json={
                "requests": [
                    {
                        "image": {
                            "content": base64.b64encode(cv2.imencode('.jpg', cv2.imread(path, cv2.IMREAD_COLOR))[1]).decode('utf-8')
                        },
                        "features": [
                            {
                                "type": "DOCUMENT_TEXT_DETECTION",
                                "maxResults": 30
                            }
                        ]
                    }
                ]
            }).json()
        # return response
        annotations = response['responses'][0]['textAnnotations'][0]
        locale = annotations['locale']
    except Exception as e:
        result = {
            'result': False,
            'status_code': 400,
            'error': f'OCR server failed to process request image: {str(e)}'
        }
        return result

    try:
        if locale == 'ko':
            text_list = annotations['description'].split('\n')

            weight_index = text_list.index('체중')
            bmi_index = text_list.index('BMI')
            fat_index = text_list.index('체지방량')
            muscle_index = text_list.index('근육량(클릭필수)')

            weight = float(text_list[weight_index + 1].split('kg')[0].strip())
            bmi = float(text_list[bmi_index+1])
            fat = float(text_list[fat_index+1].split('kg')[0].strip())
            muscle = float(text_list[muscle_index+1].split('kg')[0].strip())
            height = round(math.sqrt((weight / bmi)), 2) * 100  # 키 => 소수점 첫 번째 자리까지 나오도록 반올림
        else:
            text_list = annotations['description'].split('\n')

            weight_index = text_list.index('Weight')
            bmi_index = text_list.index('BMI')
            fat_index = text_list.index('Body Fat')
            muscle_index = text_list.index('Muscle mass')

            weight = float(text_list[weight_index + 1].split('kg')[0].strip())
            bmi = float(text_list[bmi_index+1])
            fat = round(weight * float(text_list[fat_index+1].split('%')[0].strip()) / 100, 2)
            muscle = float(text_list[muscle_index+1].split('kg')[0].strip())
            height = round(math.sqrt(weight / bmi), 2) * 100  # 키 => 소수점 첫 번째 자리까지 나오도록 반올림

        result_dict = {
            'result': True,
            'weight': weight,
            'height': height,
            'bmi': bmi,
            'fat': fat,
            'muscle': muscle
        }
        return result_dict
    except Exception as e:
        result = {
            'result': False,
            'status_code': 400,
            'error': f'Cannot recognize necessary values from request file: {str(e)}'
        }
        return result


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


def heic_to_jpg(path):
    # heif_file = pyheif.read(path)
    # new_image = Image.frombytes(
    #     heif_file.mode,
    #     heif_file.size,
    #     heif_file.data,
    #     "raw",
    #     heif_file.mode,
    #     heif_file.stride,
    # )
    #
    # new_path = f"{path.split('.')[0]}.jpg"
    # new_image.save(new_path, "JPEG")
    #
    # return new_path
    return ''


def upload_image_to_s3(file_name, bucket_name, object_name):
    s3_client = boto3.client('s3')

    try:
        s3_client.upload_file(file_name, bucket_name, object_name)
    except Exception as e:
        return str(e)

    return True


def healthiness_score(recommended, mine):
    score = (1 - (abs(recommended - mine) / mine)) * 100
    if score < 0:
        score = 0
    return score


def attractiveness_score(best_person, mine):
    score = (1 - (abs(best_person - mine) / mine)) * 100
    if score < 0:
        score = 0
    return score


def return_dict_when_nothing_to_return():
    result_dict = {
        "result": False,
        "id": None,
        "created_at": None,
        "user_week_id": None,
        "bmi": {
            "user": None,
            "ideal": None,
            "healthiness_score": None,
            "attractiveness_score": None,
            "bmi_status": None,
        },
        "muscle": {
            "user": None,
            "ideal": None,
            "healthiness_score": None,
            "attractiveness_score": None,
        },
        "fat": {
            "user": None,
            "ideal": None,
            "healthiness_score": None,
            "attractiveness_score": None,
        },
        "body_image_analysis": {
            "body_input_url": None,
            "body_input_url_resized": None,
            "body_output_url": None,
            "body_output_url_resized": None,
            "user": {
                "height": None,
                "weight": None,
                "shoulder_width": None,
                "shoulder_ratio": None,
                "hip_width": None,
                "hip_ratio": None,
                "nose_to_shoulder_center": None,
                "shoulder_center_to_hip_center": None,
                "hip_center_to_ankle_center": None,
                "shoulder_center_to_ankle_center": None,
                "whole_body_length": None,
            },
            "compare": None
        }
    }
    return result_dict
