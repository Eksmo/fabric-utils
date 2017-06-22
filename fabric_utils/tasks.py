# coding: utf-8
import re

from fabric.context_managers import lcd, settings, hide
from fabric.decorators import task, runs_once
from fabric.operations import local
from fabric.state import env
from fabric.utils import puts


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
