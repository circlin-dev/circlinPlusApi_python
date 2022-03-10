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
    result = error.to_dict()
    return json.dumps(result, ensure_ascii=False), result['status_code']


@app.route('/testing')
def hello_world():
    ip = request.headers["X-Forwarded-For"]

    query_parameter_dict = request.args.to_dict()
    values = ''
    for key in query_parameter_dict.keys():
        values += request.args[key]
    return f'Hello, {ip} ! || {values}'


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=True)  # 0.0.0.0 for production or 127.0.0.1 for local development
    except Exception as e:
        error = str(e)
        slack_error_notification(error_message=error)
