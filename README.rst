
phantom-snap
====

Render HTML to an image using PhantomJS with this library designed to scale for high volume continuous operation.

Features
--------

-  Provides full timing control around the rendering process.
-  Maintains a live PhantomJS process (instead of a new one per request which many wrappers do, which is slow).
-  Render content from a URL, or provide the HTML content directly to the renderer

Roadmap
-------
-  Decorator to manage rendering under specified timezones
-  Decorator to manage rendering under specified proxies.

Examples
--------

The example assumes you have http://phantomjs.org/ installed.


This first example demonstrates rendering a URL and saving the resulting image to a file at /tmp/google-render.jpg.
::

    from phantom_snap.settings import PHANTOMJS
    from phantom_snap.phantom import PhantomJSRenderer
    from phantom_snap.imagetools import save_image
    
    config = {
        'executable': '/usr/local/bin/phantomjs',
        'args': PHANTOMJS['args'] + ['--disk-cache=false', '--load-images=true'],
        'env': {'TZ': 'America/Los_Angeles'}
        'timeouts': {
            'page_load': 3
        }
    }
    r = PhantomJSRenderer(config)

    url = 'http://www.google.com'

    try:
        page = r.render(url, img_format='JPEG')
        save_image('/tmp/google-render', page)
    finally:
        r.shutdown(15)

A sample response from ``r.render(url)`` looks like this:

::

    {
        "status": "success",
        "format": "PNG",
        "url": "http://www.google.com",
        "paint_time": 141,
        "base64": "iVBORw0KGgo  <SNIP>  RK5CYII=",
        "error": null,
        "load_time": 342
    }

This example shows how to provide HTML content directly to the rendering process, instead of requesting it.
::

    from phantom_snap.settings import PHANTOMJS
    from phantom_snap.phantom import PhantomJSRenderer
    from phantom_snap.imagetools import save_image

    config = {
        'executable': '/usr/local/bin/phantomjs',
        'args': PHANTOMJS['args'] + ['--disk-cache=false', '--load-images=true']
    }
    r = PhantomJSRenderer(config)

    url = 'http://www.a-url.com'
    html = '<html><body>Boo ya!</body></html>'

    try:
        page = r.render(url=url, html=html, img_format='PNG')
        save_image('/tmp/html-render', page)
    finally:
        r.shutdown(15)


Decorators
----------

**Lifetime**

If you plan on running a ``PhantomJSRenderer`` instance for an extended period of time with high volume, it's recommended that you wrap the instance with a ``Lifetime`` decorator as shown below. 

The ``Lifetime`` decorator will transparently shutdown the underlying PhantomJS process if the renderer is idle or after a maximum lifetime to release any accumulated resources. This is important if PhantomJS is configured to use a memory-based browser cache to prevent the cache from growing too large. After the ``Lifetime`` decorator shuts down the Renderer (due to idle time or maximum time) the next render request will automatically create a new PhantomJS process.

::

    from phantom_snap.settings import PHANTOMJS
    from phantom_snap.phantom import PhantomJSRenderer
    from phantom_snap.decorators import Lifetime

    config = {
        'executable': '/usr/local/bin/phantomjs',
        'args': PHANTOMJS['args'] + ['--disk-cache=false', '--load-images=true'],
        'env': {'TZ': 'America/Los_Angeles'},

        # Properties for the Lifetime decorator
        'idle_shutdown_sec': 900,  # 15 minutes, Shutdown PhantomJS if it's been idle this long
        'max_lifetime_sec': 43200  # 12 hours, Restart PhantomJS every 12 hours
    }

    r = Lifetime(PhantomJSRenderer(config))

    try:
        urls = [] # Some endless source of URL targets

        for url in urls:
            page = r.render(url=url, img_format='JPEG')

            # Store the image somewhere

    finally:
        r.shutdown()


You can view the default configuration values in ``phantom_snap.settings.py``.
