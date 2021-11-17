/**
 * PhantomJS process that uses STDIN and STDOUT for
 * interprocess communication (IPC). The protocol follows...
 *
 * Input is expected to be JSON:
 * {
 *   "url": String, [required]
 *   "html": String, [optional]
 *   "html64": Base64 encoded HTML String, [optional]
 *   "width": Integer, [optional]
 *   "height": Integer, [optional]
 *   "userAgent": String, [optional]
 *   "httpProxy": String, [optional]
 *   "headers": Map<String, String>, [optional]
 *   "cookies": List<{
 *       'name'     : String, [required]
 *       'value'    : String, [required]
 *       'domain'   : String, [optional]
 *       'path'     : String, [required]
 *       'httponly' : Boolean, [optional]
 *       'secure'   : Boolean, [optional]
 *       'expires'  : Long [optional]
 *     }>, [optional]
 *   "format": String, [optional]
 *   "timeout": Long [optional]
 *   "resourceWait": Integer [optional]
 * }\n
 *
 * Output will be JSON:
 * {
 *   "url": String,
 *   "status": "success", "stopped" or "fail",
 *   "loadTime": Long of amount of time required to load the page,
 *   "paintTime": Long of amount of time required to paint the page (render the image),
 *   "base64": String of base 64 encoded image,
 *   "format": String
 * }\n

 * In the event of an error, the output will be JSON:
 * {
 *   "error": String
 * }\n
 *
 * To exit the process send:
 * exit\n
 */

var system = require("system");
var webpage = require("webpage");

// Redirect console logging to stderr to protect the protocol on stdin/stdout
console.log = function(msg) {
    system.stderr.writeLine(msg);
};

// Redirect console logging to stderr to protect the protocol on stdin/stdout
console.error = function(msg) {
    system.stderr.writeLine(msg);
};

// From https://stackoverflow.com/a/41713002, https://jsfiddle.net/47zwb41o/
escape = function( s ){
    var chr, hex, i = 0, l = s.length, out = '';
    for( ; i < l; i ++ ){
        chr = s.charAt( i );
        if( chr.search( /[A-Za-z0-9\@\*\_\+\-\.\/]/ ) > -1 ){
            out += chr; continue; }
        hex = s.charCodeAt( i ).toString( 16 );
        out += '%' + ( hex.length % 2 != 0 ? '0' : '' ) + hex;
    }
    return out;
};

b64ToUtf8 = function(s){
	s = s.replace(/\s/g, '');
	return decodeURIComponent(escape(atob(s)));
};

renderHtml = function (request) {

    var page = webpage.create();

    page.viewportSize = {
        width: 1280,
        height: 1024
    };

    if (request.hasOwnProperty('width')) {
        page.viewportSize.width = request.width;
    }

    if (request.hasOwnProperty('height')) {
        page.viewportSize.height = request.height;
    }

    if (request.hasOwnProperty('userAgent')) {
        page.settings.userAgent = request.userAgent;
    }

    if (request.hasOwnProperty('headers')) {
        page.customHeaders = request.headers;
    }

    if (request.hasOwnProperty('httpProxy')) {

        // Undocumented API for proxy:
        //
        // Global:
        // phantom.setProxy(host_or_IP, port, proxy_type, user_name, password);
        // host_or_IP only this argument is required others are optional
        // port is numeric value by default 80
        // proxy_type can be http (default) or socks5
        //
        // Per page:
        // page.setProxy("http://user:pass@proxy_ip_or_host:port/");

        page.setProxy(request.httpProxy);
    }

    phantom.clearCookies();

    if (request.hasOwnProperty('cookies')) {
        for (var i = 0; i < request.cookies.length; i++) {
            phantom.addCookie(request.cookies[i]);
        }
    }

    var format = 'PNG';

    if (request.hasOwnProperty('format')) {
        if(request.format === 'PNG' || request.format === 'JPEG') {
            format = request.format;
        }
        else {
            var error = {
                error: 'Request JSON specifies unsupported output format.'
            };
            system.stdout.writeLine(JSON.stringify(error));
            readInput();
        }
    }

    var timeout = 1000 * 180;
    var resourceWait  = 300;

    var count = 0;
    var renderTimeout;
    var stoppedRenderTimeout;

    if(request.hasOwnProperty('timeout')) {
        timeout = request.timeout;
    }

    if(request.hasOwnProperty('resourceWait')) {
        resourceWait = request.resourceWait;
    }

    page.settings.resourceTimeout  = timeout;

    var rendered = false;
    var time = Date.now();

    page.onConfirm = page.onPrompt = function noOp() {};

    var render = function(status) {

        if(!rendered) {
            rendered = true;
            clearTimeout(renderTimeout);
            clearTimeout(stoppedRenderTimeout);

            page.stop();

            time = Date.now() - time;

            // PhantomJS will use black background for transparency in JPEG if not specified.
            // https://github.com/ariya/phantomjs/issues/12724
            if(format === 'JPEG') {
                page.evaluate(function() {
                    document.body.style.backgroundColor = 'white';
                });
            }

            var response = {
                url: request.url,
                loadTime: time,
                'status': status,
                'format': format
            };

            if(status === "success" || status === "stopped") {
                time = Date.now();
                var base64 = page.renderBase64(format);

                if(base64) {
                    response.base64 = base64;
                    response.paintTime = Date.now() - time;
                }
                else {
                    response.status = 'fail';
                }
            }

            page.close();

            system.stdout.writeLine(JSON.stringify(response));
            readInput();
        }
    };

    // lazy load ajax to get a more clear page
    // https://gist.github.com/cjoudrey/1341747
    page.onResourceRequested = function (req) {
        count += 1;
        clearTimeout(renderTimeout);
    };

    page.onResourceReceived = function (res) {
        if (!res.stage || res.stage === 'end') {
            count -= 1;
            if (count === 0) {
                renderTimeout = setTimeout(function() {render('success')},
                                           resourceWait);
            }
        }
    };

    // render only if we have no more resources to load
    page.onLoadFinished = function(status) {
        if (count == 0) {
            render(status);
        }
    };

    if(request.hasOwnProperty('html')) {
        page.setContent(request.html, request.url);
    }
    else if(request.hasOwnProperty('html64')) {
        page.setContent(b64ToUtf8(request.html64), request.url);
    }
    else {
        page.open(request.url);
    }

    stoppedRenderTimeout = setTimeout(function() {
        render("stopped");
    }, timeout);
};

function readInput() {
    setTimeout(function(){
        var input = system.stdin.readLine();

        if(input !== "exit") {

            try {
                var request = JSON.parse(input);

                if(request.hasOwnProperty('url')) {
                    renderHtml(request);
                }
                else {
                    var error = {
                        error: 'Request JSON requires "url" field.'
                    };
                    system.stdout.writeLine(JSON.stringify(error));
                    readInput();
                }
            }
            catch(err) {
                var error = {
                    error: err
                };
                system.stdout.writeLine(JSON.stringify(error));
                readInput();
            }
        }
        else {
            phantom.exit();
        }
    }, 0);
};

readInput();
