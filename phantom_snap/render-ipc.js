/**
 * PhantomJS process that uses STDIN and STDOUT for
 * interprocess communication (IPC). The protocol follows...
 *
 * Input is expected to be JSON:
 * {
 *   "url": String, [required]
 *   "html": String, [optional]
 *   "width": Integer, [optional]
 *   "height": Integer, [optional]
 *   "userAgent": String, [optional]
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
 * }\n
 *
 * Output will be JSON:
 * {
 *   "url": String,
 *   "status": "success", "stopped" or "fail",
 *   "loadTime": Long of amount of time required to load the page,
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

    if(request.hasOwnProperty('timeout')) {
        timeout = request.timeout;
    }

    page.settings.resourceTimeout  = timeout;

    var rendered = false;
    var time = Date.now();

    var render = function(status) {

        if(!rendered) {
            rendered = true;

            page.stop();

            time = Date.now() - time;

            var response = {
                url: request.url,
                loadTime: time,
                'status': status,
                'format': format
            };

            if(status === "success" || status === "stopped") {
                response.base64 = page.renderBase64(format);
            }

            page.close();

            system.stdout.writeLine(JSON.stringify(response));
            readInput();
        }
    };

    page.onLoadFinished = function(status) {
        render(status);
    };

    if(request.hasOwnProperty('html')) {
        page.setContent(request.html, request.url);
    }
    else {
        page.open(request.url);
    }

    setTimeout(function() {
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
