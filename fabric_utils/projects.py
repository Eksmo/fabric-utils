import os
from contextlib import contextmanager

from fabric.api import cd, sudo, settings

from .helpers import virtualenv


class PythonProject:
    python_bin = 'python'
    src = None
    env = None
    user = None

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
        with self.cd(path), self.su():
            with virtualenv(self.env_bin):
                yield

    @contextmanager
    def su(self):
        """Run underlying sudo commands with specified user"""
        with settings(sudo_user=self.user):
            yield


class DjangoProject(PythonProject):

    def managepy(self, command):
        with self.activate(), self.su():
            return sudo(f'python manage.py {command}')
