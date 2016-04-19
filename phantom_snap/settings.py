
import os


PHANTOMJS = {
    'executable': 'phantomjs',
    'args': [],
    'env': {},
    'script': os.path.join(os.path.dirname(__file__), 'render-ipc.js'),
    'timeouts': {
        'initial_render_response': 15,  # 15 Seconds, PhantomJS takes longer on the first render after startup
        'page_load': 5,  # Max time given for PhantomJS to load the page before 'stop' and render
        'render_response': 5,  # Additional time after page load for PhantomJS to formulate and return response
        'process_startup': 10  # Max time for PhantomJS process to start before giving up
    }
}