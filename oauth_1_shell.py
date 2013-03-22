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

    oauth = OAuth1(config.client_credentials['oauth_token'][0],
                   config.client_credentials['oauth_token_secret'][0],
                   callback_uri=callback_uri,
                   signature_type=config.web_redirection_flow_signature_type)
    r = requests.post(url=config.temporary_credentials_url,
                      headers={
                          'Content-Type': 'application/x-www-form-urlencoded', 'Accept':
                          'application/x-www-form-urlencoded'},
                      auth=oauth)
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

    oauth = OAuth1(config.client_credentials['oauth_token'][0],
                   config.client_credentials['oauth_token_secret'][0],
                   unicode(temporary_credentials['oauth_token'][0]),
                   unicode(temporary_credentials['oauth_token_secret'][0]),
                   callback_uri=callback_uri,
                   signature_type=config.web_redirection_flow_signature_type,
                   verifier=unicode(verifier_query['oauth_verifier'][0]))

    r = requests.post(url=config.token_credentials_url,
                      headers={
                          'Content-Type': 'application/x-www-form-urlencoded',
                          'Accept': 'application/x-www-form-urlencoded'},
                      auth=oauth)
    token_credentials = urlparse.parse_qs(r.content)
else:
    print "Using existing 'config.token_credentials'."
    print
    print "To request new token credentials, delete token_credentials from "
    print "config.py and re-run."
    print

print "Display your token_credentials with:"
print ">>> token_credentials"
print
print ("Copy token_credentials to {0}.py to reuse them for future "
       "sessions.".format(sys.argv[1]))
print

oauth = OAuth1(config.client_credentials['oauth_token'][0],
               config.client_credentials['oauth_token_secret'][0],
               unicode(token_credentials['oauth_token'][0]),
               unicode(token_credentials['oauth_token_secret'][0]),
               signature_type=config.resource_signature_type)

print "Ready to make requests and display responses like:"
print ">>> res = requests.get('http://example.com/some/resource', auth=oauth)"
print ">>> res.json()"
print ">>> print json.dumps(res.json(), indent=2)"
