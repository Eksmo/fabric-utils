import os
from functools import wraps

from fabric.api import settings, warn


def teamcity(message_name, *params, **kwargs):
    force = kwargs.get('force') or False
    messages = {
        'testSuiteStarted': "testSuiteStarted name='%s'",
        'testSuiteFinished': "testSuiteFinished name='%s'",
        'buildStatus': "buildStatus text='%s'",
        'testStarted': "testStarted name='%s'",
        'testFailed': "testFailed name='%s' message='%s'",
        'testFinished': "testFinished name='%s'",
        'setParameter': "setParameter name='%s' value='%s'",
    }

    is_teamcity_mode = os.environ.get('TEAMCITY_VERSION') or force
    if not is_teamcity_mode:
        return

    message_tpl = messages.get(message_name)
    if not message_tpl:
        warn(f'teamcity message {message_name} not supported')
        return

    message = message_tpl % params
    print(f"##teamcity[{message}]")  # noqa


def with_teamcity(task):
    @wraps(task)
    def wrapper(*args, **kwargs):
        teamcity('testStarted', task.__name__)
        try:
            with settings(abort_exception=Exception):
                return task(*args, **kwargs)
        except Exception as exc:
            teamcity('testFailed', task.__name__, f'Exception: {type(exc).__name__}')
            raise
        finally:
            teamcity('testFinished', task.__name__)
    return wrapper
