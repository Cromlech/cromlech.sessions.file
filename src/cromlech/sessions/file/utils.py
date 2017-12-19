# -*- coding: utf-8 -*-

import os
import json
import stat


def assert_sessions_folder(path, create=False, pedantic=False):
    real_path = os.path.abspath(path)
    if not os.path.exists(real_path):
        if create:
            os.makedirs(real_path, stat.S_IRWXU)
            return real_path
        else:
            raise IOError('Sessions folder %s does not exist' % real_path)
    elif not os.path.isdir(real_path):
        raise IOError('%s is not a valid folder' % real_path)
    else:
        if pedantic:
            # We check the ownership and the rights.
            # Let's be pedantic and thorough.
            fstats = os.stat(real_path)
            if os.getuid() != fstats.st_uid:
                raise IOError(
                    'Current user does not own %s.' % real_path)
            if not bool(fstats.st_mode & stat.S_IRWXU):
                raise IOError(
                    'Folder `%s` rights are incorrect.' % real_path)
        else:
            # Only check read/write/execute
            if not os.access(real_path, os.R_OK or os.W_OK or os.X_OK):
                raise IOError(
                    '%s is not accessible for the current user' % real_path)
    return real_path
