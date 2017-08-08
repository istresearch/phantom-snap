
import os
from copy import deepcopy

# Defaults for the PhantomJS Renderer
PHANTOMJS = {
    'executable': 'phantomjs',
    'args': [],
    'env': {},
    'script': os.path.join(os.path.dirname(__file__), 'render-ipc.js'),
    'timeouts': {
        'initial_page_load': 15,  # 15 Seconds, PhantomJS takes longer on the first execution after startup
        'page_load': 5,  # Max time given for PhantomJS to load the page before 'stop' and render
        'render_response': 5,  # Additional time after page load for PhantomJS to formulate and return response
        'process_startup': 10  # Max time for PhantomJS process to start before giving up
    }
}

# Defaults for the Lifetime decorator
LIFETIME = {
    'idle_shutdown_sec': 1800,  # 30 minutes, Shutdown PhantomJS if it's been idle this long
    'max_lifetime_sec': 86400  # 24 hours, Restart PhantomJS every 24 hours
}


def merge(a, b, path=None):
    """
    Recursively merges b into a, overwriting existing a values.
    :param a: 
    :type a: dict
    :param b: 
    :type b: dict
    :param path: 
    :return: a
    """
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            else:
                a[key] = deepcopy(b[key])
        else:
            a[key] = deepcopy(b[key])
    return a
