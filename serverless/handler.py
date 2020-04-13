from phantom_snap.phantom import PhantomJSRenderer
from phantom_snap.lambda_schema import SCHEMA
import base64
import ujson
import os
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import traceback
import logging
import copy
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger('PhantomJSRenderer')
logger.setLevel(logging.DEBUG)


def render(event, context):
    request_data = ujson.loads(event['body'])
    logger.info("Received request {}".format(request_data))

    schema_version = os.getenv('SCHEMA_VERSION', '1.0')
    schema_key = os.getenv('SCHEMA_KEY', 'render')

    try:
        validate(request_data,
                 SCHEMA[schema_version][schema_key])
    except ValidationError as e:
        logger.warning("Failed schema validation {}".format(traceback.format_exc()))
        return {
            'isBase64Encoded': False,
            'statusCode': 400,
            'body': ujson.dumps({
                'message': 'Failed Schema Validation',
                'ex': traceback.format_exc(),
             }),
            'headers': {'Content-Type': 'application/json'}
        }

    # load data from schema with defaults
    url = request_data['url']
    html = request_data.get('html', None)
    img_format = request_data.get('img_format', 'PNG')
    width = request_data.get('width', 1280)
    height = request_data.get('height', 1024)
    page_load_timeout = request_data.get('page_load_timeout', None)
    user_agent = request_data.get('user_agent', None)
    headers = request_data.get('headers', None)
    cookies = request_data.get('cookies', None)
    html_encoding = request_data.get('html_encoding', 'utf-8')

    if html is not None:
        html = base64.b64decode(html)

    # render page
    try:
        renderer = PhantomJSRenderer({
            u'executable': './bin/phantomjs-2.1.1',
            u'args': [
                '--disk-cache=true',
                '--max-disk-cache-size=50000',
                '--disk-cache-path=/tmp/',
                '--load-images=true',
                '--ignore-ssl-errors=true',
                '--ssl-protocol=any',
            ],
            u'env': {u'TZ': os.getenv('PHANTOMJS_TIME_ZONE', 'UTC')},
            u'timeouts': {
                u'initial_page_load': int(os.getenv('PHANTOMJS_TIMEOUT_INITIAL', 20)),
                u'page_load': int(os.getenv('PHANTONJS_TIMEOUT_PAGE_LOAD', 15)),
                u'render_response': int(os.getenv('PHANTOMJS_TIMEOUT_RENDER_RESPONSE', 15)),
                u'process_startup': int(os.getenv('PHANTOMJS_TIMEOUT_STARTUP', 20)),
                u'resource_wait_ms': int(os.getenv('PHANTOMJS_RESOURCE_WAIT_MS', 300)),
            },
        })
        page = renderer.render(url=url,
                               html=html,
                               img_format=img_format,
                               width=width,
                               height=height,
                               page_load_timeout=page_load_timeout,
                               user_agent=user_agent,
                               headers=headers,
                               cookies=cookies,
                               html_encoding=html_encoding)
        renderer.shutdown()
        del renderer
    except Exception as e:
        logger.error("Uncaught exception {}".format(traceback.format_exc()))
        return {
            'isBase64Encoded': False,
            'statusCode': 500,
            'body': ujson.dumps({
                'message': 'Uncaught Exception',
                'ex': traceback.format_exc(),
             }),
            'headers': {'Content-Type': 'application/json'}
        }

    log_page = copy.deepcopy(page)
    if log_page['base64'] is not None:
        log_page['base64'] = '<omitted>'
    logger.info("Render response {}".format(log_page))

    if page['status'] == 'fail':
        logger.warning("Failed to render page")
        return {
            'isBase64Encoded': False,
            'statusCode': 500,
            'body': ujson.dumps(page),
            'headers': {'Content-Type': 'application/json'}
        }
    else:
        logger.debug("Successful render")
        return {
            'isBase64Encoded': False,
            'statusCode': 200,
            'body': ujson.dumps(page),
            'headers': {'Content-Type': 'application/json'}
        }
