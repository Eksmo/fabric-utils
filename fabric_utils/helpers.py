import os
import re
from typing import Any
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
                puts(f'{branch.name} does not match the required branches {", ".join(required_branches)}')
                return
            return arg(branch, *args, **kwargs)

        if callable(arg):
            return wraps(arg)(wrapper)
        else:
            def inner_dec(func):
                return decorator(func, arg, *required_branches)
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
    return call(f'python manage.py {command}')


@contextmanager
def pyenv(python_path):
    with path(python_path, 'prepend'):
        yield


@contextmanager
def virtualenv(virtualenv_path):
    with path(virtualenv_path, 'prepend'):
        yield


@contextmanager
def checksum(filename, *files_or_dirs):
    paths = ' '.join(files_or_dirs)
    # check whether the files have changed (or the checksum file does not exist at all)
    with quiet():
        if not sudo(f'find {paths} -type f -print0 | sort -z | xargs -0 tar cf - | shasum -c {filename}').failed:
            modified = False
        else:
            modified = True
    yield modified
    # compute checksum for specified paths
    if modified:
        sudo(f'find {paths} -type f -print0 | sort -z | xargs -0 tar cf - | shasum > {filename}')


def get_checksum(*files_or_dirs):
    """
    Calculate sha checksum for list of given files or directories.
    """
    paths = ' '.join(files_or_dirs)
    # what this command does is:
    shasum = sudo(f'find {paths} -type f -print0 | sort -z | xargs -0 tar cf - | tar xOf - | shasum')

    if shasum.failed:
        raise Exception('failed to get shasum for specified files')

    return str(shasum).split(' ', 1)[0]


def readlink(path):
    with quiet():
        result = sudo(f'readlink {path}')
    if not result.failed:
        return str(result)


def slugify_version(version):
    # Python 2.7.15 -> python_2_7_15
    return re.sub(r'[^\d\w]+', '_', version).lower()


def slugify_command_version(command, user=None):
    command_output = str(sudo(command, user=user))
    return slugify_version(command_output)


def to_bool(value: Any) -> bool:
    """Convert a command line choice to a boolean value"""
    true_values = ('yes', 'y', 'true', 't', '1')

    if isinstance(value, (bool, int)):
        return bool(value)

    if isinstance(value, str) and value.lower() in true_values:
        return True

    return False


template = partial(upload_template, use_jinja=True, backup=False)
