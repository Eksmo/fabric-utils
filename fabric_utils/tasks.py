# coding: utf-8
import re
from time import sleep

from fabric.api import puts, local, task, runs_once, lcd, settings, hide, env
from fabric.operations import sudo
from fabric.tasks import execute
from fabric.utils import error


@task
@runs_once
def register_opbeat_deployment(git_path='', org_id=None, app_id=None, token=None, revision=None, branch=None):
    """
    Register deployment with opbeat

    :param git_path: relative path to git repo, to cd into
    :param revision: release git full hash (detected automatically if not provided)
    :param branch: release git branch (detected automatically if not provided)
    :return: None
    """
    with lcd(git_path):
        revision = revision or local('git log -n 1 --pretty="format:%H"', capture=True)
        branch = branch or local('git rev-parse --abbrev-ref HEAD', capture=True)
        local('curl https://intake.opbeat.com/api/v1/organizations/{org_id}/apps/{app_id}/releases/'
              ' -H "Authorization: Bearer {token}"'
              ' -d rev={revision}'
              ' -d branch={branch}'
              ' -d status=completed'.format(
                org_id=org_id, app_id=app_id, token=token, revision=revision, branch=branch))


@task
def sqlmigrate(from_branch='origin/develop', to_branch='origin/master', prefix='export STAGE=dev'):
    """
    Display sql statements that will run when branch is deployed.
    Note, that this command might trigger checkout and also database connection for sqlmigrate.

    Examples:
        * fab local.sqlmigrate
        * fab local.sqlmigrate:origin/feature/inapp,origin/master

    :param from_branch: feature branch, containing new migrations
    :param to_branch: target branch, to witch first one will be merged
    :param prefix: prefix sqlmigrate with env var set or other command
    :return: None
    """
    with settings(warn_only=True), hide('warnings'):
        files = local('git diff --name-only %s %s | grep migrations' % (from_branch, to_branch), capture=True)
        if not files:
            puts('No migrations')
            return
    current_remote = local('git rev-parse --abbrev-ref --symbolic-full-name @{u}', capture=True)
    if from_branch != current_remote:
        local('git checkout %s' % from_branch)
    with settings(command_prefixes=[prefix]):
        for path in files.splitlines():
            match = re.search('(\w+)/migrations/(\d+)', path)
            if match:
                local('python manage.py sqlmigrate %s %s' % (match.group(1), match.group(2)))
    if from_branch != current_remote:
        local('git checkout -')


@task
def check_uwsgi_is_200_ok():
    global app

    with app.activate(), settings(hide('stdout')):
        command = 'uwsgi_curl 127.0.0.1:{uwsgi_port} {healthcheck_url} | head -n 1 | grep "200 OK"'.format(
            uwsgi_port=env.uwsgi_port, healthcheck_url=env.healthcheck_url)
        result = sudo(command, warn_only=True, user=env.user)
        return result


@task
def check_http_is_200_ok():
    with settings(hide('stdout')):
        command = 'curl -sSL -D - {healthcheck_url} -o /dev/null | head -n 1 | grep "200 OK"'.format(
            healthcheck_url=env.healthcheck_url)
        result = sudo(command, warn_only=True, shell=False, user=env.user)
        return result


def check_role_is_up(role, check_task_func):
    is_service_up_values = execute(check_task_func, role=role).values()
    all_hosts_up = all(r.succeeded for r in is_service_up_values)
    joint_stderr = '\n'.join(r.stdout for r in is_service_up_values)
    return all_hosts_up, joint_stderr


def wait_until_role_is_up(role,
                          healthcheck_url,
                          check_task_func=check_http_is_200_ok,
                          poll_interval_seconds=10,
                          max_wait_seconds=20,
                          warn_only=False):
    """
    Wait until all role hosts are considered healthy, e.g. returns 200 OK in response to GET healthcheck_url

    :param role:
    :param healthcheck_url: URL that must return 200 OK for host to be considered healthy
    :param check_task_func: fabric task that does actual check, returns command result
    :param poll_interval_seconds: health checks frequency in seconds
    :param max_wait_seconds: maximum global wait timeout across all healthchecks
    :param warn_only: If False (default), abort execution
    :return: boolean
    """
    wait = 0
    stderr = '-'
    while wait < max_wait_seconds:
        wait += poll_interval_seconds
        sleep(poll_interval_seconds)
        with settings(healthcheck_url=healthcheck_url):
            is_up, stderr = check_role_is_up(role, check_task_func)
        if is_up:
            return True
    else:
        with settings(warn_only=warn_only):
            error('Waited for %s seconds, role %s is not up. %s \n %s' % (
                wait, role, 'Aborting' if not warn_only else '', stderr))