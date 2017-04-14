# coding: utf-8
import os
from functools import partial, wraps
from contextlib import contextmanager

from fabric.api import sudo, run, path, puts, quiet
from fabric.contrib.files import upload_template

from .git import get_active_branch_name


def su(user):
    return partial(sudo, user=user)


def requires_branch(cls):
    """
    Enforce function callers to provide a branch name
    unless the current working directory holds a git repository with a branch checked in.

    An exception is raised if failed to obtain branch name.

    The decorator may be optionally passed a required branch name
    limiting the function execution scope to the specified branch only.
    """
    def decorator(arg, *required_branches):

        def wrapper(branch=None, *args, **kwargs):
            force_branch = kwargs.pop('force_branch', False)
            if not isinstance(branch, cls):
                ci_branch = os.environ.get('BUILD_BRANCH')
                branch_name = branch if branch else (ci_branch or get_active_branch_name())
                if not branch_name:
                    raise ValueError('Not in a git repository. Provide a branch name')
                branch = cls(branch_name)
            # check if the function is allowed to run with this particular branch
            if not force_branch and required_branches and branch.name not in required_branches:
                puts('{} does not match the required branches {}'.format(branch.name, required_branches))
                return
            return arg(branch, *args, **kwargs)

        if callable(arg):
            return wraps(arg)(wrapper)
        else:
            def inner_dec(func):
                return decorator(func, arg)
            return inner_dec
    return decorator


def requires_user(func):
    """
    Require a function caller to supply user as an argument.
    The decorated function is passed the provided value (or None)
    and a call function (fabric.api.run if user is None).
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = kwargs.pop('user', None)
        call_func = su(user) if user else run
        return func(user=user, call=call_func, *args, **kwargs)
    return wrapper


@requires_user
def managepy(command, user, call):
    return call('python manage.py {}'.format(command))


@contextmanager
def pyenv(python_path):
    with path(python_path, 'prepend'):
        yield


@contextmanager
def virtualenv(virtualenv_path):
    with path(virtualenv_path, 'prepend'):
        yield


@contextmanager
def checksum(filename, *paths):
    paths = ' '.join(paths)
    # check whether the files have changed (or the checksum file does not exist at all)
    with quiet():
        if not sudo('tar cf - {} | shasum -c {}'.format(paths, filename)).failed:
            modified = False
        else:
            modified = True
    yield modified
    # compute checksum for specified paths
    if modified:
        sudo('tar cf - {} | shasum > {}'.format(paths, filename))


template = partial(upload_template, use_jinja=True, backup=False)
