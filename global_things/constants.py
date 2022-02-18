APP_ROOT = "/home/ubuntu/circlinMembersApi_python/circlinMembersApi_flask"
API_ROOT = "web-api-python.circlin.co.kr"

# region bodylab
AMAZON_URL = "https://circlin-plus.s3.ap-northeast-2.amazonaws.com"
IMAGE_ANALYSYS_SERVER = "3.35.12.179"
BUCKET_NAME = "circlin-plus"
BUCKET_BODY_IMAGE_INPUT_PATH = "bodylab/body/input"
BUCKET_BODY_IMAGE_OUTPUT_PATH = "bodylab/body/output"
BUCKET_ATFLEE_IMAGE_PATH = "bodylab/atflee/input"

BODY_IMAGE_INPUT_PATH = f"/home/ubuntu/circlinMembersApi_python/circlinMembersApi_flask/{BUCKET_BODY_IMAGE_INPUT_PATH}"
ATFLEE_IMAGE_INPUT_PATH = f"/home/ubuntu/circlinMembersApi_python/circlinMembersApi_flask/{BUCKET_ATFLEE_IMAGE_PATH}"
#endregion

# region Slack error notification
SLACK_NOTIFICATION_WEBHOOK = "https://hooks.slack.com/services/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?"
# endregion

# region Import payment API Keys
IMPORT_REST_API_KEY = "8960715711085849"
IMPORT_REST_API_SECRET = "aa8f4f6206e82213fc1665f0cd6f8967a59def6fd2be1321a34a48af8c87b39bd39850c45b54824b"
# endregion

# region bodylab criteria data
ATTRACTIVENESS_SCORE_CRITERIA = {
    "M": {
        # 유연규님
        'weight': 66,
        'height': 170,
        "bmi": 22.83,
        "muscle_mass": 33,
        "fat_mass": 8,
    },
    "W": {
        # 임희정님
        'weight': 50,
        'height': 159,
        "bmi": 19.302487059715,
        "muscle_mass": 21,
        "fat_mass": 8,
    }
}

BODY_IMAGE_ANALYSIS_CRITERIA = {
    # https://github.com/circlin-dev/circlin5.0/blob/39c2acd2b02d8cdba3d2e606e16d0ad6ab1d4302/circlin/src/screens/user/UserAnalysisScreen.js
    # line 330 ~ 351
    "M": {
        "name": "Ho Jung Jeong",
        "height": 175,
        "head_width": 92.03,
        "shoulder_width": 164.6,
        "shoulder_ratio": 1.55,
        "hip_width": 105.88973999023438,
        "hip_ratio": 1.15,
        "nose_to_shoulder_center": 81.9,
        "shoulder_center_to_hip_center": 242.83541870117188,
        "hip_center_to_ankle_center": 372.2978515625,
        "shoulder_center_to_ankle_center": 615.13327026367188,
        "whole_body_length": 721.02301025390626
    },
    "W": {
        "name": "Si Young Lee",
        "height": 169,
        "head_width": 125.29998779296875,
        "shoulder_width": 227.68,
        "shoulder_ratio": 1.8,
        "hip_width": 139.67,
        "hip_ratio": 1.11,
        "nose_to_shoulder_center": 113.8,
        "shoulder_center_to_hip_center": 341.46636962890625,
        "hip_center_to_ankle_center": 555.2415771484375,
        "shoulder_center_to_ankle_center": 896.70794677734375,
        "whole_body_length": 1022.0079345703125
    }
}
# endregion

















