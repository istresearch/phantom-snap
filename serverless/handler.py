from phantom_snap.settings import PHANTOMJS
from phantom_snap.phantom import PhantomJSRenderer
from phantom_snap.imagetools import save_image
import base64
import ujson

# TODO: ENV VARS OR POST ARGS
# # use when phantomjs is installed raw on the machine
# PHANTOMJS_EXE = '/opt/phantomjs/default/bin/phantomjs'
# # use via grunner in a container
# #PHANTOMJS_EXE = '/usr/bin/phantomjs'
# PHANTOMJS_ARGS = [
#     '--disk-cache=false',
#     '--load-images=true',
#     '--ignore-ssl-errors=true',
#     '--ssl-protocol=any'
# ]
# PHANTOMJS_TIME_ZONE = 'UTC'
# PHANTOMJS_DEFAULT_USERAGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
# PHANTOMJS_TIMEOUT_INITIAL = 15 # 15 Seconds, PhantomJS takes longer on the first render after startup
# PHANTONJS_TIMEOUT_PAGE_LOAD = 5 # Max time given for PhantomJS to load the page before 'stop' and render
# PHANTOMJS_TIMEOUT_RENDER_RESPONSE = 5 # Additional time after page load for PhantomJS to formulate and return response
# PHANTOMJS_TIMEOUT_STARTUP = 10  # Max time for PhantomJS process to start before giving up
# PHANTOMJS_LIFETIME_IDLE_SHUTDOWN_SEC = 300,  # Shutdown PhantomJS if it's been idle this long
# PHANTOMJS_LIFETIME_MAX_LIFETIME_SEC = 1800  # Restart PhantomJS every N seconds


def render(event, context):
    request_data = ujson.loads(event['body'])
    html = base64.b64decode(request_data['html'])
    url = request_data['url']

    renderer = PhantomJSRenderer({
            u'executable': './bin/phantomjs-2.1.1',
            u'args': [
                '--disk-cache=false',
                '--load-images=true',
                '--ignore-ssl-errors=true',
                '--ssl-protocol=any'
            ],
            u'env': {u'TZ': 'UTC'},
            u'timeouts': {
                u'initial_page_load': 15,
                u'page_load': 5,
                u'render_response': 5,
                u'process_startup': 10
            },
        })

    page = renderer.render(url=url, html=html, img_format='PNG')

    return {
        'isBase64Encoded': False,
        'statusCode': 200,
        'body': ujson.dumps(page),
        'headers': {'Content-Type': 'application/json'}
    }
