from api import api
from global_things.constants import APP_ROOT
from global_things.functions.slack import slack_error_notification
from global_things.error_handler import HandleException
from flask import Flask, request
from flask_cors import CORS
from flask_request_validator.error_formatter import demo_error_formatter
from flask_request_validator.exceptions import InvalidRequestError, InvalidHeadersError, RuleError
import json
import logging
import traceback
from werkzeug.exceptions import HTTPException


app = Flask(__name__)
CORS(app, supports_credentials=True)

#   For nginx log
logging.basicConfig(filename=f'{APP_ROOT}/execution_log.log',
                    filemode='a+',
                    format=' [%(filename)s:%(lineno)s:%(funcName)s()]- %(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

# For Blueprint api activation.
app.register_blueprint(api, url_prefix="/api")


@app.errorhandler(HandleException)
def raise_exception(error):
    return json.dumps(error.to_dict(), ensure_ascii=False), error.to_dict()['status_code']


@app.route('/testing')
def hello_world():
    ip = request.headers["X-Forwarded-For"]

    query_parameter_dict = request.args.to_dict()
    values = ''
    for key in query_parameter_dict.keys():
        values += request.args[key]
    return f'Hello, {ip} ! || {values}'


# def error_handle(app):
#     """에러 핸들러
#
#     에러 처리하는 함수
#
#     Args:
#         app  : __init__.py에서 파라미터로 app을 전달 받은 값
#     Returns:
#         json : error_response() 함수로 에러 메시지를 전달해서 반환 받고 return
#     """
#
#     @app.errorhandler(Exception)
#     def handle_error(e):
#         traceback.print_exc()
#         return json.dumps({"error": f"{str(e)}: 서버 상에서 오류가 발생했습니다(Exception)"}, ensure_ascii=False), 500
#
#     @app.errorhandler(AttributeError)
#     def handle_error(e):
#         traceback.print_exc()
#         return json.dumps({"error": f"{str(e)}: 서버 상에서 오류가 발생했습니다(NoneType Error)"}, ensure_ascii=False), 500
#
#     @app.errorhandler(KeyError)
#     def handle_key_error(e):
#         traceback.print_exc()
#         return json.dumps({"error": f"{str(e)}: 데이터베이스에서 값을 가져오는데 문제가 발생하였습니다(Database Key Error)"}, ensure_ascii=False), 500
#
#     @app.errorhandler(TypeError)
#     def handle_type_error(e):
#         traceback.print_exc()
#         return json.dumps({"error": f"{str(e)}: 데이터의 값이 잘못 입력되었습니다(Data Type Error)"}, ensure_ascii=False), 500
#
#     @app.errorhandler(ValueError)
#     def handle_value_error(e):
#         traceback.print_exc()
#         return json.dumps({"error": f"{str(e)}: 데이터에 잘못된 값이 입력되었습니다(Data Value Error)"}, ensure_ascii=False), 500
#
#     # @app.errorhandler(err.OperationalError)
#     # def handle_operational_error(e):
#     #     traceback.print_exc()
#     #     return error_response(e, "에러")
#
#     @app.errorhandler(InvalidRequestError)
#     def data_error(e):
#         """validate_params 정규식 에러
#         validate_params rules에 위배될 경우 발생되는 에러 메시지를 처리하는 함수
#         """
#         traceback.print_exc()
#         dev_error_message = demo_error_formatter(
#             e)[0]['errors'], demo_error_formatter(e)[0]['message']
#         return json.dumps({"error": f"형식에 맞는 값을 입력해주세요({dev_error_message})"}, ensure_ascii=False), 400


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=True)  # 0.0.0.0 for production or 127.0.0.1 for local development
    except Exception as e:
        error = str(e)
        slack_error_notification(error_message=error)
