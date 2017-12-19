# -*- coding: utf-8 -*-

from functools import wraps
from uuid import uuid4
from datetime import datetime, timedelta
from itsdangerous import TimestampSigner
from biscuits import parse, Cookie
from collections import UserDict
from .session import SessionDict


class SessionManager(object):

    def __init__(self, secret, handler, cookie='sid'):
        self.handler = handler
        self.delta = handler.delta  # lifespan delta in seconds.
        self.cookie_name = cookie
        self.signer = TimestampSigner(secret)

    def generate_session_id(self):
        return str(uuid4())

    def refresh_session_id(self, sid):
        return self.signer.sign(sid)

    def get_session_id(self, cookie):
        if cookie is not None:
            morsels = parse(cookie)
            signed_sid = morsels.get(self.cookie_name)
            if signed_sid is not None:
                # maybe we want an error handling here.
                sid = self.signer.unsign(signed_sid, max_age=self.delta)
                return sid, signed_sid
        return self.generate_session_id()

    def get_session_dict(self, cookie):
        sid = self.get_session_id(cookie)
        session_dict = SessionDict(sid, self.handler)
        return session_dict


class WSGISessionManager(SessionManager):
    
    def __init__(self, *args, **kwargs):
        self.environ_key = kwargs.pop('environ_key', 'session')
        SessionManager.__init__(self, *args, **kwargs)

    def __call__(self, app):
        @wraps(app)
        def file_session_wrapper(environ, start_response):

            def session_start_response(status, headers, exc_info=None):

                # Write down the session
                # This relies on the good use of the `save` method.
                session_dict = environ[self.environ_key]
                session_dict.persist()

                # Refresh the signature on the sid
                ssid = self.refresh_session_id(session_dict.sid)

                # Prepare the cookie and push it in the headers
                path = environ['SCRIPT_NAME'] or '/'
                domain = environ['HTTP_HOST'].split(':', 1)[0]
                expires = datetime.now() + timedelta(seconds=self.delta)
                cookie = Cookie(
                    name=self.cookie_name, value=ssid, path=path,
                    domain=domain, expires=expires)
                cookie_value = str(cookie)
                headers.append(('Set-Cookie', cookie_value))
                return start_response(status, headers, exc_info)

            session_dict = self.get_session_dict(environ.get('HTTP_COOKIE'))
            environ[self.environ_key] = session_dict
            return app(environ, session_start_response)
        return file_session_wrapper
