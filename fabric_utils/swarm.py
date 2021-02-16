import random
from typing import Optional, Callable, Any
from functools import wraps

from fabric.api import quiet, puts, task, abort, run, settings
from fabric.colors import green as g, red as r, yellow as y

from fabric_utils.healthcheck import check_role_is_up


@task
def docker_swarm_ping_manager() -> Optional[str]:
    # a node may fail but this is perfectly fine
    # perhaps it's under a maintenance?
    with quiet(), settings(abort_exception=Exception, abort_on_prompts=True):
        try:
            return run('docker node ls')
        except Exception:
            return None


def docker_swarm_select_manager(role: str) -> Optional[str]:
    checked_hosts, stderr = check_role_is_up(docker_swarm_ping_manager, role=role)
    if any(checked_hosts.values()):
        good_hosts = [host for host, status in checked_hosts.items() if status]
        puts(g(f'swarm is healthy. {len(good_hosts)}/{len(checked_hosts)} available managers: {", ".join(good_hosts)}'))
        return random.choice(good_hosts)
    else:
        failed_hosts = ', '.join([host for host, status in checked_hosts.items() if not status])
        abort(r(f'swarm is not healthy. all managers failed: {failed_hosts}'))
        return None


@task
def docker_swarm_restart(label: str, value: str, stack: str,
                         no_serial: bool = False, no_wait: bool = False) -> None:
    """
    Restart swarm services by their deploy labels defined in the compose file.

    :param label: service label defined in the compose file (e.g. mybook.deploy.group)
    :param value: service label value (e.g. uwsgi)
    :param stack: name of the stack where the labeled service is defined
    :param no_serial: Execute the update command on all nodes at once ignoring the parallelism mode
    :param no_wait: Do not wait for currently services to exit gracefully
    """
    service_format = '{{.Name}}'
    service_names = run(f'docker stack services '
                        f'--format "{service_format}" --filter label={label}={value} '
                        f'{stack}')
    if 'Nothing found' in service_names:
        abort(r(f'no services found matching label "{label}={value}"'))
    else:
        command = 'docker service update --quiet --force --no-healthcheck'
        if no_serial:
            command = f'{command} --update-parallelism=0'
        if no_wait:
            command = f'{command} --stop-grace-period=1s'
        for service_name in service_names.splitlines():
            puts(y(f'restarting service {service_name}'))
            run(f'{command} {service_name}')


def with_swarm_node(role: str) -> Callable:
    """
    Pick a random swarm node and pass it as a keyword arg to the decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*task_args: Any, **task_kwargs: Any) -> Any:
            swarm_node = docker_swarm_select_manager(role)
            task_kwargs['node'] = swarm_node
            return func(*task_args, **task_kwargs)
        return wrapper
    return decorator
