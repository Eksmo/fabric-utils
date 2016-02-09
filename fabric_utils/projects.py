# coding: utf-8
import os
from contextlib import contextmanager

from fabric.api import cd

from .helpers import virtualenv


class PythonProject(object):
    python_bin = 'python'
    src = None
    env = None

    def __init__(self, *args, **kwargs):
        pass

    @property
    def env_bin(self):
        if not self.env:
            raise ValueError('invalid env')
        return os.path.join(self.env, 'bin')

    @property
    def python(self):
        return os.path.join(self.env_bin, self.python_bin)

    @contextmanager
    def cd(self, path=None):
        path = path or self.src

        if not path:
            raise ValueError('invalid path')

        with cd(path):
            yield

    @contextmanager
    def activate(self, path=None):
        with self.cd(path):
            with virtualenv(self.env_bin):
                yield
