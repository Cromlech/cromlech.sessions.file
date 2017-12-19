# -*- coding: utf-8 -*-

from functools import wraps
from uuid import uuid4
from datetime import datetime, timedelta
from itsdangerous import TimestampSigner
from biscuits import parse, Cookie


class SessionManager(object):

    def __init__(self, secret, handler, cookie='sid'):
        self.handler = handler
        self.delta = handler.delta  # lifespan delta in seconds.
        self.cookie_name = cookie
        self.signer = TimestampSigner(secret)

    def generate_session_id(self):
        sid = str(uuid4())
        signed_sid = self.signer.sign(sid)

    def refresh_session_id(self, sid):
        return self.signer.sign(sid)

    def extract_session(self, cookie):
        if cookie is not None:
            morsels = parse(cookie)
            signed_sid = morsels.get(self.cookie_name)
            if token is not None:
                # maybe we want an error handling here.
                sid = self.signer.unsign(signed_sid, max_age=self.delta)
                session_data = self.handler.get(self, sid)
                return sid, session_data
        return {}


class WSGISessionManager(SessionManager):
    
    def __init__(self, *args, **kwargs):
        self.environ_key = kwargs.pop('environ_key', 'session')
        SessionManager.__init__(self, *args, **kwargs)

    def __call__(self, app):
        @wraps(app)
        def file_session_wrapper(environ, start_response):

            def session_start_response(status, headers, exc_info=None):
                # FIXME : we need to handle the errors here.
                # See also how to work with `transaction`.

                # Cleanup the cache
                self.handler.flush_expired_sessions()

                # Write down the session
                sid = environ['__sid__']
                data = environ[self.environ_key]
                self.handler.save(sid, data)

                # Refresh the signature on the sid
                value = self.refresh_session_id(sid)

                # Prepare the cookie and push it in the headers
                path = environ['SCRIPT_NAME'] or '/'
                domain = environ['HTTP_HOST'].split(':', 1)[0]
                expires = datetime.now() + timedelta(seconds=self.delta)
                cookie = Cookie(
                    name=self.cookie_name, value=value, path=path,
                    domain=domain, expires=expires)
                cookie_value = str(cookie)
                headers.append(('Set-Cookie', cookie_value))
                return start_response(status, headers, exc_info)

            sid, data = self.extract_session(environ.get('HTTP_COOKIE'))
            environ[self.environ_key] = data
            environ['__sid__'] = sid
            return app(environ, session_start_response)
        return file_session_wrapper
