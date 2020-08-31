from typing import Callable

from fabric.api import puts, task


@task
def set_redis_lock(call: Callable, *, host: str, port: int, lock: str, user: str) -> bool:
    result = call(f'redis-cli -h {host} -p {port} msetnx {lock} {user}')
    is_locked = '(integer) 0' in result.stdout
    if is_locked:
        locked_due = call(f'redis-cli -h {host} -p {port} get {lock}')
        puts(f'lock is set for {locked_due}')
        return False
    return True


@task
def delete_redis_lock(call: Callable, host: str, port: int, lock: str) -> None:
    call(f'redis-cli -h {host} -p {port} del {lock}')
