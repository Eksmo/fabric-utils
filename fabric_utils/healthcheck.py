from time import sleep
from typing import Tuple, Callable, Any, Dict, Optional

from fabric.api import puts, settings, hide
from fabric.operations import run
from fabric.tasks import execute
from fabric.utils import error

from .helpers import is_parallel_supported


def check_uwsgi_is_200_ok(url, uwsgi_port=None, uwsgi_sock=None, status='200 OK'):
    with settings(hide('stdout')):
        addr = f'127.0.0.1:{uwsgi_port}' if uwsgi_port else uwsgi_sock
        command = f'uwsgi_curl {addr} {url} | head -n 1 | grep "{status}"'
        result = run(command, warn_only=True, shell=False)
        return result


def check_http_is_200_ok(healthcheck_url, http_host=None, unix_sock=None, status='200 OK'):
    with settings(hide('stdout')):
        command = 'curl'
        if unix_sock:
            command = f'{command} --unix-socket {unix_sock}'
        if http_host:
            command = f'{command} -H "Host: {http_host}"'
        command = f'{command} -sSL -D - "{healthcheck_url}" -o /dev/null | head -n 1 | grep "{status}"'
        result = run(command, warn_only=True, shell=False)
        return result


def check_role_is_up(task: Callable, *task_args: Any, **task_kwargs: Any) -> Tuple[dict, str]:
    with settings(parallel=is_parallel_supported()):
        is_role_up_results = execute(task, *task_args, **task_kwargs)
    per_hosts_success = {
        host: res.succeeded
        for host, res in is_role_up_results.items() if res
    }
    joint_stderr = '\n'.join(r.stdout for r in is_role_up_results.values() if r)
    return per_hosts_success, joint_stderr


def wait_until_role_is_up(task: Callable, poll_interval: int = 3, max_wait: int = 20, check=all,
                          task_args: Optional[Tuple[Any]] = None, task_kwargs: Optional[Dict[str, Any]] = None) -> bool:
    waiting_seconds = 0
    stderr = '-'
    task_args = task_args or ()
    task_kwargs = task_kwargs or {}

    puts(f'waiting for role/host to be up for as long as {max_wait} seconds')
    while waiting_seconds < max_wait:
        # skip waiting on the first iteration, app may already be up
        up_hosts, stderr = check_role_is_up(task, *task_args, **task_kwargs)
        if check(up_hosts.values()):
            puts(f'role/host is up after {waiting_seconds} seconds')
            return True
        else:
            failed_hosts = ', '.join([host for host, status in up_hosts.items() if not status])
            puts(f'role/host is not up after {waiting_seconds} seconds: failed hosts: {failed_hosts}')

        sleep(poll_interval)
        waiting_seconds += poll_interval

    with settings(warn_only=False):
        error(f'waited for {waiting_seconds} seconds, role/host is not up. Aborting \n {stderr}')

    return False
