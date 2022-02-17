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
    0: {
        "sex": "man",
        "preferred_by": "man",
        'weight': 0,
        'height': 0,
        "bmi": 00.00,
        "muscle_mass": 00.00,
        "fat_mass": 00.00,
    },
    1: {
        "sex": "man",
        "preferred_by": "woman",
        'weight': 0,
        'height': 0,
        "bmi": 00.00,
        "muscle_mass": 00.00,
        "fat_mass": 00.00,
    },
    2: {
        "sex": "woman",
        "preferred_by": "man",
        'weight': 0,
        'height': 0,
        "bmi": 00.00,
        "muscle_mass": 00.00,
        "fat_mass": 00.00,
    },
    3: {
        "sex": "woman",
        "preferred_by": "woman",
        'weight': 0,
        'height': 0,
        "bmi": 00.00,
        "muscle_mass": 00.00,
        "fat_mass": 00.00,
    }
}

BODY_IMAGE_ANALYSIS_CRITERIA = {
    "man": {
        "name": "Ho Jung Jeong",
        "height": 175,
        "shoulder_width": 164.6,
        "hip_width": 92.03,
        "head_height": 105.88973999023438,
        "upperbody_height": 242.83541870117188,
        "lowerbody_height": 372.2978515625
    },
    "woman": {
        "name": "Si Young Lee",
        "height": 169,
        "shoulder_width": 227.68,
        "hip_width": 139.67,
        "head_height": 125.29998779296875,
        "upperbody_height": 341.46636962890625,
        "lowerbody_height": 555.2415771484375
    }
}
# endregion





















