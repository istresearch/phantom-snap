
phantom-snap
====

Render HTML to an image using PhantomJS with this library designed to scale for high volume continuous operation.

Features
--------

-  Provides full timing control around the rendering process.
-  Maintains a live PhantomJS process (instead of a new one per request which many wrappers do, which is slow).

Roadmap
-------
-  Decorators to manage rendering under specified timezones or proxies per request.

Examples
--------

The example assumes you have http://phantomjs.org/ installed.

::

    from phantom_snap.settings import PHANTOMJS
    from phantom_snap.phantom import PhantomJSRenderer
    
    config = {
        'executable': '/usr/local/bin/phantomjs',
        'args': PHANTOMJS['args'] + ['--disk-cache=false', '--load-images=true'],
        'env': {'TZ': 'America/Los_Angeles'}
    }
    r = PhantomJSRenderer(config)

    urls = ['http://whatismytimezone.com/',
            'http://www.drudgereport.com',
            'http://www.google.com']

    try:
        for url in urls:
            page = r.render(url)
            if page is not None:
                if page['error'] is None:
                    print ''.join([page['url'], ' ', str(page['status']), ' ', str(page['load_time'])])
                else:
                    print ''.join([page['url'], ' ', str(page['status']), ' ', page['error']])
    finally:
        r.shutdown(15)

A sample response from the ``render(url)`` method looks like this:

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
        'idle_shutdown_sec': 1800,  # 30 minutes, Shutdown PhantomJS if it's been idle this long
        'max_lifetime_sec': 86400  # 24 hours, Restart PhantomJS every 24 hours
    }

    r = Lifetime(PhantomJSRenderer(config))

You can view the default configuration values in ``phantom_snap.settings.py``.
