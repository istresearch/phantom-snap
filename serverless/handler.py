from phantom_snap.phantom import PhantomJSRenderer
from phantom_snap.lambda_schema import SCHEMA
import base64
import ujson
import os
from flex.core import validate
from flex.exceptions import ValidationError
import traceback


def render(event, context):
    request_data = ujson.loads(event['body'])

    try:
        validate(SCHEMA, request_data)
    except ValidationError as e:
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
    img_format = request_data.get('image_format', 'PNG')
    width = request_data.get('width', 1280)
    height = request_data.get('height', 1024)
    page_load_timeout = request_data.get('page_load_timeout', None)
    user_agent = request_data.get('user_agent', None)
    headers = request_data.get('headers', None)
    cookies = request_data.get('cookies', None)
    html_encoding = request_data.get('html_encoding', None)

    # boot renderer up
    try:
        renderer = PhantomJSRenderer({
                u'executable': './bin/phantomjs-2.1.1',
                u'args': [
                    '--disk-cache=false',
                    '--load-images=true',
                    '--ignore-ssl-errors=true',
                    '--ssl-protocol=any'
                ],
                u'env': {u'TZ': os.getenv('PHANTOMJS_TIME_ZONE', 'UTC')},
                u'timeouts': {
                    u'initial_page_load': int(os.getenv('PHANTOMJS_TIMEOUT_INITIAL', 15)),
                    u'page_load': int(os.getenv('PHANTONJS_TIMEOUT_PAGE_LOAD', 5)),
                    u'render_response': int(os.getenv('PHANTOMJS_TIMEOUT_RENDER_RESPONSE', 5)),
                    u'process_startup': int(os.getenv('PHANTOMJS_TIMEOUT_STARTUP', 10)),
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
    except Exception as e:
        return {
            'isBase64Encoded': False,
            'statusCode': 500,
            'body': ujson.dumps({
                'message': 'Uncaught Exception',
                'ex': traceback.format_exc(),
             }),
            'headers': {'Content-Type': 'application/json'}
        }

    if page['status'] == 'fail':
        return {
            'isBase64Encoded': False,
            'statusCode': 500,
            'body': ujson.dumps(page),
            'headers': {'Content-Type': 'application/json'}
        }
    else:
        return {
            'isBase64Encoded': False,
            'statusCode': 200,
            'body': ujson.dumps(page),
            'headers': {'Content-Type': 'application/json'}
        }

if __name__ == "__main__":
    data_to_send = {
        'url': 'www.aol.com'
    }
    print(render({'body': ujson.dumps(data_to_send)}, {}))
