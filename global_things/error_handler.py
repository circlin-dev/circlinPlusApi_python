from flask import request
from global_things.functions.slack import slack_error_notification
import json


class HandleException(Exception):
    def __init__(self,
                 user_ip: str = '',
                 user_id: int = 0,
                 api: str = '',
                 error_message: str = '',
                 query: str = '',
                 method: str = '',
                 status_code: int = 0,
                 payload=None,
                 result: bool = False):
        super().__init__()
        self.user_ip = user_ip
        self.user_id = user_id
        self.api = api
        self.error_message = error_message
        self.query = query
        self.method = method
        self.status_code = status_code
        self.payload = payload
        self.result = result

    def to_dict(self):
        error = dict()
        error['user_ip'] = self.user_ip
        error['user_id'] = self.user_id
        error['api'] = self.api
        error['error_message'] = self.error_message
        error['query'] = self.query
        error['method'] = self.method
        error['status_code'] = self.status_code
        error['payload'] = self.payload
        error['result'] = self.result
        slack_error_notification(user_ip=self.user_ip,
                                 user_id=self.user_id,
                                 api=self.api,
                                 method=self.method,
                                 status_code=self.status_code,
                                 query=self.query,
                                 error_message=self.error_message)
        return error
