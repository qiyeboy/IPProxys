#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<17175297.hk@gmail.com>
#         http://binux.me
# Created on 2012-12-15 16:11:13

import logging
import tornado.web
from base64 import b64decode, b64encode
from config import POWER_CONFIG as options
from db.DataStore import sqlhelper
import os
import re
import json
import urllib
import random
import socket
import hashlib
try:
    from urlparse import urlparse, urlsplit
except ImportError:
    from urllib.parse import urlparse, urlsplit
from tornado import gen
from tornado.web import HTTPError
from tornado.ioloop import IOLoop
import tornado.iostream
import tornado.httputil
import tornado.tcpclient
import tornado.httpclient
try:
    import pycurl
    tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
except ImportError:
    pycurl = None


def utf8(string):
    if isinstance(string, unicode):
        return string.encode('utf8')
    return string


def link(a, b):
    """
    link stream a to stream b
    """
    a.read_until_close(lambda x: not b.closed() and b.write(b'', callback=b.close),
                       streaming_callback=lambda x: not b.closed() and b.write(x))
    b.set_close_callback(lambda: not a.closed() and a.write(b'', callback=a.close))


class ProxyHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'HEAD', 'CONNECT', 'PUT', 'OPTIONS']
    set_cookie_re = re.compile(";?\s*(domain|path)\s*=\s*[^,;]+", re.I)

    def options(self):
        cors = self.get_argument('cors', None)
        if not cors:
            return self.get()

        self.set_header('Access-Control-Allow-Credentials', 'true')
        self.set_header('Access-Control-Max-Age', 86400)
        if 'Access-Control-Request-Headers' in self.request.headers:
            self.set_header('Access-Control-Allow-Headers',
                            self.request.headers.get('Access-Control-Request-Headers'))
        if 'Access-Control-Request-Method' in self.request.headers:
            self.set_header('Access-Control-Allow-Methods',
                            self.request.headers.get('Access-Control-Request-Method'))
        self.set_status(204)
        self.finish()

    def get(self):
        method = self.request.method
        url = self.request.uri
        headers = tornado.httputil.HTTPHeaders(self.request.headers)
        body = self.request.body

        if self.request.uri.startswith('http'):
            return self.proxy(method, url, headers, body, http_proxy=True)

        method = self.get_argument('method', method)
        url = self.get_argument('url', self.get_argument('rl', url))
        callback = self.get_argument('callback', None)

        try:
            request = json.loads(self.get_argument('request', self.request.body))
        except:
            request = {}
        url = request.get('url', url)
        method = request.get('method', method)
        if 'headers' in request:
            for key, value in request['headers'].items():
                headers[key] = value
        body = request.get('body', body)
        callback = request.get('callback', callback)

        for key, values in self.request.arguments.items():
            key = key.lower()
            if key.startswith('h-'):
                headers[key[2:]] = values[0].strip()
            elif key.startswith('d-'):
                if key[2:] in headers:
                    del headers[key[2:]]

        if 'del_headers' in request:
            for key in request['del_headers']:
                if key in headers:
                    del headers[key]

        for keyword in ('Host', 'Content-Type', 'Content-Length'):
            if keyword in headers:
                del headers[keyword]
        if body.startswith('base64,'):
            try:
                body = b64decode(body[7:])
            except:
                pass

        if self.request.path == '/sign' and self.auth(url):
            return self.finish(self.sign(url))

        if not url.startswith('http'):
            return self.finish('hello world!')

        self.request.method = method
        self.request.uri = url

        return self.proxy(method, url, headers, body, _callback=callback)

    put = get
    post = get
    head = get

    def sign(self, url):
        parsed = urlparse(url)
        return {
            'host_sign': hashlib.md5(
                ('%s:%s:%s' % (options.username, options.password, parsed.netloc)).encode('utf8')
            ).hexdigest()[5:11],
            'path_sign': hashlib.md5(
                ('%s:%s:%s:%s' % (options.username, options.password, parsed.netloc, parsed.path)).encode('utf8')
            ).hexdigest()[5:11],
            'url_sign': hashlib.md5(
                ('%s:%s:%s' % (options.username, options.password, url)).encode('utf8')
            ).hexdigest()[5:11],
            }

    @gen.coroutine
    def proxy(self, method, url, headers, body, **kwargs):
        if not self.auth(url):
            if kwargs.get('http_proxy'):
                self.set_header('Proxy-Authenticate', 'Basic realm="hello"')
                self.set_status(407)
                self.finish()
                raise gen.Return()
            else:
                raise HTTPError(403)

        req = tornado.httpclient.HTTPRequest(
                method = method,
                url = url,
                headers = headers,
                body = body or None,
                decompress_response = False,
                follow_redirects = False,
                allow_nonstandard_methods = True)

        if self.application.forward_proxies:
            self.via_proxy = proxy = self.application.get_proxy()
            try:
                remote = yield gen.with_timeout(IOLoop.current().time()+10, tornado.tcpclient.TCPClient().connect(
                    proxy.hostname, int(proxy.port), ssl_options={} if proxy.scheme == 'https' else None))
            except gen.TimeoutError:
                self.application.remove_proxy(proxy)
                raise HTTPError(504)

            parsed = urlparse(req.url)
            userpass = None
            netloc = parsed.netloc
            if '@' in parsed.netloc:
                userpass, _, netloc = netloc.rpartition("@")
            headers = tornado.httputil.HTTPHeaders(headers)

            if parsed.scheme == 'https':
                remote.write(utf8('CONNECT %s:%s HTTP/1.1\r\n' % (parsed.hostname, parsed.port or 443)))
                remote.write(utf8('Host: %s\r\n' % netloc))
                if proxy.username:
                    remote.write(utf8('Proxy-Authorization: Basic %s\r\n' %
                                 b64encode('%s:%s' % (proxy.username, proxy.password))))
                remote.write('\r\n')
                yield remote.read_until('\r\n\r\n')

                channel_a, channel_b = socket.socketpair()
                if not hasattr(channel_a, '_sock'):
                    channel_a, channel_b = socket._socketobject(_sock=channel_a), socket._socketobject(_sock=channel_b)
                channel_a, channel_b = tornado.iostream.IOStream(channel_a), tornado.iostream.IOStream(channel_b)

                link(channel_a, remote)
                link(remote, channel_a)

                remote = yield channel_b.start_tls(False, {}, netloc)

                request_path = parsed.path
                if parsed.query:
                    request_path += '?%s' % parsed.query
                remote.write(utf8('%s %s HTTP/1.1\r\n' % (req.method.upper(), urllib.quote(request_path))))
            else:
                remote.write(utf8('%s %s HTTP/1.1\r\n' % (req.method.upper(), req.url)))
                if proxy.username:
                    headers['Proxy-Authorization'] = 'Basic %s' % b64encode('%s:%s' % (proxy.username, proxy.password))

            if 'Host' not in headers:
                headers['Host'] = netloc
            # force disable connection
            if not kwargs.get('http_proxy'):
                headers['Connection'] = b'close'
            if userpass:
                headers['Authorization'] = utf8('basic %s' % b64encode(userpass))
            if req.body:
                headers['Content-Length'] = str(len(utf8(req.body)))
            for key, value in headers.get_all():
                remote.write(utf8('%s: %s\r\n' % (key, value)))
            remote.write('\r\n')
            if req.body:
                remote.write(utf8(body))
            yield remote.write(b'')

            self._auto_finish = False
            client = self.request.connection.detach()
            # not forward any further message to remote, as current request had finished
            if kwargs.get('http_proxy'):
                link(client, remote)
            link(remote, client)

            self._log()
            return

        if kwargs.get('http_proxy'):
            # streaming in http proxy mode
            self._auto_finish = False

            stream = self.request.connection.detach()
            req.header_callback = lambda line, stream=stream: not stream.closed() and stream.write(line) if not line.startswith('Transfer-Encoding') else None
            req.streaming_callback = lambda chunk, stream=stream: not stream.closed() and stream.write(chunk)

            client = tornado.httpclient.AsyncHTTPClient()
            try:
                result = yield client.fetch(req)
            except tornado.httpclient.HTTPError as e:
                pass
            finally:
                stream.close()
            self._log()
            return

        client = tornado.httpclient.AsyncHTTPClient()
        try:
            result = yield client.fetch(req)
        except tornado.httpclient.HTTPError as e:
            if e.response:
                result = e.response
            else:
                self.set_status(502)
                self.write('Bad Gateway error:\n' + str(e))
                self.finish()
                raise gen.Return()

        self.set_status(result.code, result.reason)
        if result.headers.get('Transfer-Encoding') == 'chunked':
            del result.headers['Transfer-Encoding']
        if 'set-cookie' in result.headers:
            set_cookie = result.headers.get_list('set-cookie')
            del result.headers['set-cookie']
            for each in set_cookie:
                result.headers.add('set-cookie', self.set_cookie_re.sub('', each))

        if kwargs.get('_callback'):
            self.set_header('Content-Type', 'application/javascript')
            self.finish('%s(%s)' % (kwargs['_callback'], json.dumps(result.body)))
        else:
            cors = self.get_argument('cors', None)
            if cors:
                result.headers["Access-Control-Allow-Origin"] = "*"
            self._headers = result.headers
            if result.code == 304:
                self.finish()
            else:
                self.finish(result.body)

    def auth(self, url):
        if not options.username:
            return True

        username, password = None, None

        if not (username and password) and 'Proxy-Authorization' in self.request.headers:
            try:
                method, b64 = self.request.headers['Proxy-Authorization'].strip().split(' ', 1)
                username, password = b64decode(b64.split(',', 1)[0]).decode('utf8').split(':', 1)
            except:
                raise
                pass
            del self.request.headers['Proxy-Authorization']

        if not (username and password) and 'Authorization' in self.request.headers:
            try:
                method, b64 = self.request.headers['Authorization'].split(' ', 1)
                username, password = b64decode(b64).decode('utf8').split(':', 1)
            except:
                pass

        if not (username and password):
            username = self.get_argument('username', username)
            password = self.get_argument('password', password)

        request = {}
        if not (username and password):
            try:
                request = json.loads(self.get_argument('request'))
            except:
                pass
            username = request.get('username', username)
            password = request.get('username', password)

        if options.username == username and options.password == password:
            return True

        # auth by sign
        sign = self.sign(url)
        for key, value in sign.items():
            if request.get(key, self.get_argument(key, None)) == value:
                return True

        return False

    @gen.coroutine
    def connect(self):
        url = self.request.uri
        if not self.auth(url):
            self.set_header('Proxy-Authenticate', 'Basic realm="hello"')
            self.set_status(407)
            self.finish()
            raise gen.Return()

        self._auto_finish = False
        client = self.request.connection.detach()

        if self.application.forward_proxies:
            self.via_proxy = proxy = self.application.get_proxy()
            try:
                remote = yield gen.with_timeout(IOLoop.current().time()+10, tornado.tcpclient.TCPClient().connect(
                    proxy.hostname, int(proxy.port), ssl_options={} if proxy.scheme == 'https' else None))
                remote.write(utf8('CONNECT %s HTTP/1.1\r\n' % self.request.uri))
                remote.write(utf8('Host: %s\r\n' % self.request.uri))
                if proxy.username:
                    remote.write(utf8('Proxy-Authorization: Basic %s\r\n' %
                                 b64encode('%s:%s' % (proxy.username, proxy.password))))
                remote.write('\r\n')
            except gen.TimeoutError:
                self.application.remove_proxy(proxy)
                raise HTTPError(504)
        else:
            try:
                host, port = self.request.uri.split(':')
                remote = yield gen.with_timeout(IOLoop.current().time()+10,
                                                tornado.tcpclient.TCPClient().connect(host, int(port)))
            except gen.TimeoutError:
                raise HTTPError(504)
            yield client.write(b'HTTP/1.0 200 Connection established\r\n\r\n')

        link(client, remote)
        link(remote, client)

        yield [
            gen.Task(client.set_close_callback),
            gen.Task(remote.set_close_callback),
        ]
        self._log()

    def _request_summary(self):
        if getattr(self, 'via_proxy', None):
            return "%s %s via %s (%s)" % (self.request.method, self.request.uri,
                                          self.via_proxy.hostname, self.request.remote_ip)
        else:
            return "%s %s (%s)" % (self.request.method, self.request.uri,
                                   self.request.remote_ip)


class Application(tornado.web.Application):
    def __init__(self):
        self.forward_proxies = []
        self.refresh_proxies()

        settings = dict(
            debug=options.debug,
        )
        super(Application, self).__init__([(".*", ProxyHandler), ], **settings)

    def refresh_proxies(self):
        self.forward_proxies = sqlhelper.select(50)

    def get_proxy(self):
        if len(self.forward_proxies) == 0:
            self.refresh_proxies()
        _proxy = random.choice(self.forward_proxies)
        class Proxy(object):
            hostname = _proxy['ip']
            port = _proxy['port']
            scheme = _proxy['protocol']
        return Proxy

    def remove_proxy(self, proxy):
        return sqlhelper.delete(conditions={
            'ip': proxy.hostname,
            'port': proxy.port,
            'protocol': proxy.scheme
        })


def main():
    from tornado.ioloop import IOLoop
    from tornado.httpserver import HTTPServer
    http_server = HTTPServer(Application(), xheaders=True)
    http_server.bind(options.port, options.bind)
    http_server.start()
    logging.info("http server started on %s:%s" % (options.bind, options.port))
    IOLoop.instance().start()

if __name__ == "__main__":
    main()
