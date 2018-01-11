# -*- coding: utf-8 -*-

import os
import time
from datetime import datetime
from cromlech.session import Store
from cromlech.marshallers import PickleMarshaller
from .utils import assert_sessions_folder


class FileStore(Store):
    """ Files based HTTP session.
    """

    def __init__(self, root, delta, marshaller=PickleMarshaller):
        self.delta = delta  # timedelta in seconds.
        self.root = assert_sessions_folder(root, create=True)
        self.marshaller = marshaller

    def get_session_path(self, sid):
        """Override to add a prefix or a namespace, if needed.
        """
        return os.path.join(self.root, sid)

    def __iter__(self):
        """Override to add a prefix or a namespace, if needed.
        """
        for filepath in os.listdir(self.root):
            yield filepath

    def get_session_file(self, sid, epoch=None):
        """Override to customize the behavior, add events or other
        kind of decorum.
        """
        path = self.get_session_path(sid)
        if os.path.exists(path):
            if epoch is None:
                epoch = time.time()
            fmod = os.path.getmtime(path)
            if (fmod + self.delta) < epoch:
                os.remove(path)  # File expired, we remove
                return None
            return path
        return None

    def get(self, sid):
        session_path = self.get_session_file(sid)
        if session_path is None:
            return self.new()
        session = self.marshaller.load_from(session_path)
        return session

    def set(self, sid, data):
        assert isinstance(data, dict)
        session_path = self.get_session_path(sid)  # it might not exist
        self.marshaller.dump_to(data, session_path)

    def clear(self, sid):
        session_path = self.get_session_path(sid)
        if session_path is not None:
            os.remove(session_path)

    delete = clear

    def flush_expired_sessions(self):
        """This method should be used in an asynchroneous task.
        Running this during an HTTP request/response cycle, synchroneously
        can result in low performances.
        """
        now = time.time()
        for sid in iter(self):
            path = self.get_session_file(sid, epoch=now)
            if path is None:
                # Added debug logging.
                continue
