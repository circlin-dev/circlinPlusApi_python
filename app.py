from api import api
from global_things.constants import APP_ROOT, BODY_IMAGE_INPUT_PATH, ATFLEE_IMAGE_INPUT_PATH
from global_things.error_handler import InvalidAPIUsage
from global_things.functions.slack import slack_error_notification
from flask import abort, Flask, jsonify, render_template, request
from flask_cors import CORS
import json
import logging
from werkzeug.exceptions import HTTPException


app = Flask(__name__)
CORS(app, supports_credentials=True)

#   For nginx log
logging.basicConfig(filename=f'{APP_ROOT}/execution_log.log', filemode='a+',
                    format=' [%(filename)s:%(lineno)s:%(funcName)s()]- %(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

# For Blueprint api activation.
app.register_blueprint(api, url_prefix="/api")


@app.route('/testing')
def hello_world():
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    query_parameter_dict = request.args.to_dict()
    values = ''
    for key in query_parameter_dict.keys():
        values += request.args[key]
    return f'Hello, {ip} ! || {values}'


@app.route('/bodylab_form')
def bodylab_form():
    return render_template('bodylab_form.html')


@app.errorhandler(InvalidAPIUsage)
def invalid_api_usage(e):
    return jsonify(e.to_dict())


@app.errorhandler(400)
def handle_400_error(e):
    result_dict = {'result': False, 'error': str(e)}
    slack_error_notification(error_log=str(e))
    # return jsonify(error=str(e)), 400
    return json.dumps(result_dict, ensure_ascii=False), 400


@app.errorhandler(405)
def handle_400_error(e):
    result_dict = {'result': False, 'error': str(e)}
    slack_error_notification(error_log=str(e))
    return json.dumps(result_dict, ensure_ascii=False), 405


# @app.errorhandler(Exception)
# def handle_exception(e):
#     # pass through HTTP errors
#     if isinstance(e, HTTPException):
#         slack_error_notification(error_log=str(e))
#         return str(e), 500
#
#     # now you're handling non-HTTP exceptions only
#     slack_error_notification(error_log=str(e))
#     return str(e), 500


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=True)  # 0.0.0.0 for production or 127.0.0.1 for local development
    except Exception as e:
        error = str(e)
        slack_error_notification(error_log=error)
