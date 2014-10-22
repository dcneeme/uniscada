#!/usr/bin/python3

"""
Test URLs (default port, user=sdmarianne)

GOOD
    http://receiver.itvilla.com:8888/api/v1/hostgroups
    http://receiver.itvilla.com:8888/api/v1/hostgroups/
    http://receiver.itvilla.com:8888/api/v1/hostgroups/saared
    http://receiver.itvilla.com:8888/api/v1/servicegroups
    http://receiver.itvilla.com:8888/api/v1/servicegroups/
    http://receiver.itvilla.com:8888/api/v1/servicegroups/service_pumplad_ee
    http://receiver.itvilla.com:8888/api/v1/servicegroups/service_pumplad4_ee
    http://receiver.itvilla.com:8888/api/v1/services/00204AB80D57
    http://receiver.itvilla.com:8888/api/v1/services/00204AB80BF9
    http://receiver.itvilla.com:8888/api/v1/services/00204AA95C56

    https://receiver.itvilla.com:4433/api/v1/hostgroups
    https://receiver.itvilla.com:4433/api/v1/hostgroups/
    https://receiver.itvilla.com:4433/api/v1/hostgroups/saared
    https://receiver.itvilla.com:4433/api/v1/servicegroups
    https://receiver.itvilla.com:4433/api/v1/servicegroups/
    https://receiver.itvilla.com:4433/api/v1/servicegroups/service_pumplad_ee
    https://receiver.itvilla.com:4433/api/v1/servicegroups/service_pumplad4_ee
    https://receiver.itvilla.com:4433/api/v1/services/00204AB80D57
    https://receiver.itvilla.com:4433/api/v1/services/00204AB80BF9
    https://receiver.itvilla.com:4433/api/v1/services/00204AA95C56

BAD
    http://receiver.itvilla.com:8888/
    http://receiver.itvilla.com:8888/api/v1/
    http://receiver.itvilla.com:8888/api/v1/hostgroups/x
    http://receiver.itvilla.com:8888/api/v1/hostgroups/itvilla
    http://receiver.itvilla.com:8888/api/v1/servicegroups/x
    http://receiver.itvilla.com:8888/api/v1/servicegroups/hvvmon_ee
    http://receiver.itvilla.com:8888/api/v1/services/x
    http://receiver.itvilla.com:8888/api/v1/services/0008E101A8E9

    https://receiver.itvilla.com:4433/
    https://receiver.itvilla.com:4433/api/v1/
    https://receiver.itvilla.com:4433/api/v1/hostgroups/x
    https://receiver.itvilla.com:4433/api/v1/hostgroups/itvilla
    https://receiver.itvilla.com:4433/api/v1/servicegroups/x
    https://receiver.itvilla.com:4433/api/v1/servicegroups/hvvmon_ee
    https://receiver.itvilla.com:4433/api/v1/services/x
    https://receiver.itvilla.com:4433/api/v1/services/0008E101A8E9

"""

# Too old distro (Red Hat Enterprise Linux Server release 6.2 (Santiago) / 6 December 2011)
import sys
sys.path.append('/root/tornado-3.2/')
sys.path.append('/root/backports.ssl_match_hostname-3.4.0.2/src')

from monpanel import *

import tornado.web
import tornado.gen
import tornado.websocket

from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps

EXECUTOR = ThreadPoolExecutor(max_workers=50)

def unblock(f):
    @tornado.web.asynchronous
    @wraps(f)

    def wrapper(*args, **kwargs):
        self = args[0]

        def callback(future):
            result = future.result()

            if 'status' in result:
                self.set_status(result['status'])

            self.set_header("Content-Type", "application/json; charset=utf-8")
            self.set_header("Access-Control-Allow-Origin", "*")
            if 'headers' in result:
                for header in result['headers']:
                    for key in header:
                        self.set_header(key, header[key])

            self.write(json.dumps(result['bodydata'], indent=4, sort_keys=True, cls=JSONBinEncoder))
            self.finish()

        EXECUTOR.submit(
            partial(f, *args, **kwargs)
        ).add_done_callback(
            lambda future: tornado.ioloop.IOLoop.instance().add_callback(
                partial(callback, future)))

    return wrapper


class JSONBinEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) == type(bytes()):
            return obj.decode(encoding='UTF-8')
        return json.JSONEncoder.default(self, obj)


class UnknownHandler(tornado.web.RequestHandler):
    def initialize(self):
        pass

    def get(self, *args, **kwargs):
        self.set_status(404)
        base_url = self.request.protocol + '://' + self.request.host
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({
            'message': 'Not Found',
            'api_url': base_url + '/api/v1/'
        }, indent = 4, sort_keys = True))
        self.finish()


class RootHandler(tornado.web.RequestHandler):
    def initialize(self):
        pass

    def get(self, *args, **kwargs):
        base_url = self.request.protocol + '://' + self.request.host
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({
            'hostgroup_url': base_url + '/api/v1/hostgroups{/name}',
            'servicegroup_url': base_url + '/api/v1/servicegroups{/name}',
            'service_url': base_url + '/api/v1/services/name'
        }, indent = 4, sort_keys = True))
        self.finish()


class RestHandler(tornado.web.RequestHandler):
    def initialize(self):
        pass

    def get_current_user(self):
        cookeiauth = self.get_cookie('itvilla_com', None)
        if cookeiauth == None:
            return None
        return cookeiauth.split(':')[0]

    def get_login_url(self):
        # cookieauth does not support quoted cookies
        # self.set_cookie('CookieAuth_Redirect', self.request.protocol + '://' + self.request.host + self.request.uri, domain='.itvilla.com')
        self.set_header('Set-Cookie', 'CookieAuth_Redirect=' + self.request.protocol + '://' + self.request.host + self.request.uri + '; Domain=.itvilla.com; Path=/')
        return "https://login.itvilla.com/login"

    @tornado.web.authenticated
    @unblock
    def get(self, *args, **kwargs):

        if len(args) != 3:
            return({'message' : 'missing arguments'})

        self.session = Session(self.get_current_user())

        filter = None
        if args[2] != '':
            filter = args[2]

        try:
            body = self.session.sql2json(args[0], filter)

            headers = [
                    { 'X-Username': self.get_current_user() }
            ]
            return({ 'status': 200, 'headers': headers, 'bodydata': body })
        except SessionAuthenticationError as e:
            return({ 'status': 401, 'bodydata': {'message' : str(e)} })
        except SessionException as e:
            return({ 'status': 500, 'bodydata': {'message' : str(e)} })
        except Exception as e:
            return({ 'status': 501, 'bodydata': {'message' : str(e)} })


if __name__ == '__main__':
    from tornado.options import define, options, parse_command_line

    tornado.options.define("http_port", default = "8888", help = "HTTP port (0 to disable)", type = int)
    tornado.options.define("https_port", default = "4433", help = "HTTPS port (0 to disable)", type = int)

    args = sys.argv
    args.append("--logging=debug")
    tornado.options.parse_command_line(args)

    app_settings = {
        "debug": True
    }

    app = tornado.web.Application([
        (r'/api/v1/(servicegroups|hostgroups|services)(/(.*))?', RestHandler),
        (r'/api/v1/', RootHandler),
        (r'/.*', UnknownHandler)
    ], **app_settings)

    if options.https_port != 0:
        print("HTTPS server listening on port " + str(options.https_port))
        import tornado.httpserver
        httpsserver = tornado.httpserver.HTTPServer(app, ssl_options = {
                "certfile": "receiver.itvilla.com.crt",
                "keyfile": "receiver.itvilla.com.key"
            })
        httpsserver.listen(options.https_port)
        print("OK")

    if options.http_port != 0:
        print("HTTP server listening on port " + str(options.http_port))
        app.listen(options.http_port)
        print("OK")

    import tornado.ioloop
    tornado.ioloop.IOLoop.instance().start()