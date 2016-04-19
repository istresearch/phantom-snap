
phantom-snap
====

Render HTML to an image using PhantomJS with this library designed to scale for high volume continuous operation.

Features
--------

-  Provides full timing control around the rendering process.
-  Maintains a live PhantomJS process (instead of a new one per request which many wrappers do, which is slow).
-  [Coming soon] Manages rendering under specified timezones or proxies per request.

Examples
--------

The example assumes you have PhantomJS installed and on on your path.

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

