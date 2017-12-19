# -*- coding: utf-8 -*-


class SessionDict(object):

    def __init__(self, sid, handler):
        self.sid = sid
        self.handler = handler
        self._session = None
        self._modified = False

    def __getitem__(self, key):
        return self.session[key]

    def __setitem__(self, key, value):
        self.session[key] = value

    def __delitem__(self, key):
        self.session.__delitem__(key)

    def __repr__(self):
        return self.session.__repr__()

    def __iter__(self):
        return iter(self.session)

    def __contains__(self, key):
        return key in self.session

    def has_key(self, key):
        return key in self.session

    def get(self, key, default=None):
        return self.session.get(key, default)

    @property
    def session(self):
        if self._session is None:
            self._session = self.handler.get(self.sid)
        return self._session

    @property
    def accessed(self):
        return self._session is not None

    @property
    def modified(self):
        return self._modified

    def save(self):
        """Mark as dirty to allow persistence.
        """
        self._modified = True

    def persist(self, force=False):
        if force or (not force and self._modified):
            self.handler.save(self.sid, self._session)
            self._modified = False
        elif self.accessed:
            # here update the modified time
            """
            st = os.stat(f)
            atime = st[ST_ATIME] #access time
            mtime = st[ST_MTIME] #modification time
            
            new_mtime = mtime + (4*3600) #new modification time
        
            #modify the file timestamp
            os.utime(f,(atime,new_mtime))
            """
