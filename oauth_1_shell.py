"""ipython -i oauth_1_shell.py"""

from __future__ import unicode_literals
import json
import sys
import urlparse
import webbrowser

from oauthlib.oauth1.rfc5849.utils import escape
import requests
from requests_oauthlib import OAuth1

def usage():
    print "Usage: ipython -i {0} <config>".format(sys.argv[0])

def request(method, url, *args, **kwargs):
    res = requests.request(method, url, *args, **kwargs)
    print '> {0} {1} HTTP/1.1'.format(res.request.method, res.request.url)
    print '\n'.join(
        [ '> {0}: {1}'.format(key, value)
          for (key, value) in res.request.headers.items() ])
    print '> '
    if res.request.body is not None:
        print res.request.body
        print
    print '< HTTP/{0} {1}'.format(res.raw.version / 10., res.status_code)
    print '\n'.join(
        [ '< {0}: {1}'.format(key, value)
          for (key, value) in res.headers.items() ])
    print
    print res.text
    return res

def get(url, *args, **kwargs):
    return request(method='GET', url=url, *args, **kwargs)

def post(url, *args, **kwargs):
    return request(method='POST', url=url, *args, **kwargs)

def put(url, *args, **kwargs):
    return request(method='PUT', url=url, *args, **kwargs)

def delete(url, *args, **kwargs):
    return request(method='DELETE', url=url, *args, **kwargs)

try:
    config = __import__(sys.argv[1])
except:
    usage()
    sys.exit(1)

print

try:
    token_credentials = config.token_credentials
    if not token_credentials['oauth_token'][0]:
        raise Exception()
    if not token_credentials['oauth_token_secret'][0]:
        raise Exception()
except:
    print "'config.token_credentials' doesn't look usable."
    print "Requesting new token credentials."
    print

    callback_uri='http://127.0.0.1:12345/'

    oauth_temp = OAuth1(
        config.client_credentials['oauth_token'][0],
        config.client_credentials['oauth_token_secret'][0],
        callback_uri=callback_uri,
        signature_type=config.web_redirection_flow_signature_type)
    r = post(url=config.temporary_credentials_url,
             headers={
                 'Content-Type': 'application/x-www-form-urlencoded', 'Accept':
                 'application/x-www-form-urlencoded'},
             auth=oauth_temp)
    temporary_credentials = urlparse.parse_qs(r.content)

    authorize_url = '{0}?oauth_token={1}&oauth_callback={2}'.format(
        config.user_authorization_url,
        temporary_credentials['oauth_token'][0],
        escape(callback_uri)
    )

    webbrowser.open(authorize_url)
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
    class AuthorizationHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200, 'OK')
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.server.path = self.path

    server_address = (urlparse.urlparse(callback_uri).hostname,
                      urlparse.urlparse(callback_uri).port)
    httpd = HTTPServer(server_address, AuthorizationHandler)
    httpd.handle_request()
    httpd.server_close()
    verifier_url = urlparse.urlparse(httpd.path)
    verifier_query = urlparse.parse_qs(verifier_url.query)

    oauth_token = OAuth1(
        config.client_credentials['oauth_token'][0],
        config.client_credentials['oauth_token_secret'][0],
        unicode(temporary_credentials['oauth_token'][0]),
        unicode(temporary_credentials['oauth_token_secret'][0]),
        callback_uri=callback_uri,
        signature_type=config.web_redirection_flow_signature_type,
        verifier=unicode(verifier_query['oauth_verifier'][0]))

    r = post(url=config.token_credentials_url,
             headers={
                 'Content-Type': 'application/x-www-form-urlencoded',
                 'Accept': 'application/x-www-form-urlencoded'},
             auth=oauth_token)
    token_credentials = urlparse.parse_qs(r.content)
else:
    print "Using existing 'config.token_credentials'."
    print
    print "To request new token credentials, delete token_credentials from "
    print "{0}.py and re-run.".format(sys.argv[1])
    print

print "Display your token_credentials with:"
print
print "    >>> token_credentials"
print
print ("Copy token_credentials to {0}.py to reuse them for future "
       "sessions.".format(sys.argv[1]))
print

oauth_resource = OAuth1(config.client_credentials['oauth_token'][0],
                        config.client_credentials['oauth_token_secret'][0],
                        unicode(token_credentials['oauth_token'][0]),
                        unicode(token_credentials['oauth_token_secret'][0]),
                        signature_type=config.resource_signature_type)
oauth = oauth_resource

print "Ready to make requests and display responses like:"
print
print "    >>> res = request(method='GET', url='http://example.com/some/resource', auth=oauth)"
print
print "or"
print
print "    >>> res = requests.get('http://example.com/some/resource', auth=oauth)"
print "    >>> res.json()"
print "    >>> print json.dumps(res.json(), indent=2)"
