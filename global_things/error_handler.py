from flask import request
from global_things.functions.slack import slack_error_notification
import json

class InvalidAPIUsage(Exception):
    status_code = 400

    def __init__(self,
                 user_ip: str = '',
                 user_id: int = 0,
                 nickname: str = '',
                 api: str = '',
                 error_message: str = '',
                 query: str = '',
                 method: str = '',
                 status_code=None, payload=None,
                 result=False):
        super().__init__()
        self.user_ip = user_ip
        self.user_id = user_id
        self.nickname = nickname
        self.api = api
        self.error_message = error_message
        self.query = query
        self.method = method
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
        self.result = result

    def to_dict(self):
        error = dict()
        error['user_ip'] = self.user_ip
        error['user_id'] = self.user_id
        error['nickname'] = self.nickname
        error['api'] = self.api
        error['error_message'] = self.error_message
        error['query'] = self.query
        error['method'] = self.method
        error['status_code'] = self.status_code
        error['payload'] = self.payload
        error['result'] = self.result
        slack_error_notification(self.user_ip, self.user_id, self.nickname, self.api, self.error_message, self.query, self.method)
        return error


result_dict = {
    "id": record[0],
    "created_at": record[1].strftime('%Y-%m-%d %H:%M:%S'),
    "user_week_id": record[2],
    "bmi": {
        "user": record[7],
        "ideal": record[8],
        "healthiness_score": record[9],
        "attractiveness_score": record[10],
        "bmi_status": record[11]
    },
    "muscle": {
        "user": record[12],
        "ideal": record[13],
        "healthiness_score": record[14],
        "attractiveness_score": record[15]
    },
    "fat": {
        "user": record[16],
        "ideal": record[17],
        "healthiness_score": record[18],
        "attractiveness_score": record[19]
    },
    "body_image_analysis": {
        "body_input_url": record[3],
        "body_input_url_resized": json.loads(record[4]),
        "body_output_url": record[20],
        "body_output_url_resized": record[21],
        "user": {
            "height": record[5],
            "weight": record[6],
            "shoulder_width": record[22],
            "shoulder_ratio": record[23],
            "hip_width": record[24],
            "hip_ratio": record[25],
            "nose_to_shoulder_center": record[26],
            "shoulder_center_to_hip_center": record[27],
            "hip_center_to_ankle_center": record[28],
            "shoulder_center_to_ankle_center": record[29],
            "whole_body_length": record[30]
        },
        "compare": BODY_IMAGE_ANALYSIS_CRITERIA[gender]
    }
}