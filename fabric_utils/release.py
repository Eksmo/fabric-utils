import os
import re
from functools import wraps
from typing import List

from fabric.api import quiet, sudo, fastprint, warn, prompt, execute, abort, settings
from collections import namedtuple, OrderedDict


Commit = namedtuple('Commit', ['sha', 'sha_short', 'msg'])
Release = namedtuple('Release', ['base', 'release', 'changelog'])


def get_release(target_branch: str) -> Release:
    """
    Return an ordered list of (sha,msg,diff stat) commit tuples for diff between given git revisions
    The first commit is the last commit in the local branch
    """
    commits = []

    teamcity_release_sha = os.environ.get('BUILD_VCS_NUMBER')
    to_revision = teamcity_release_sha or target_branch

    with quiet():
        sudo('git fetch origin')
        git_log = _get_revision_diff('HEAD~1', to_revision)
        if not git_log:
            git_log = _get_revision_diff(f'{to_revision}~1', to_revision)

        # remove empty lines and non git-log lines (such as freebsd login tips)
        lines = []
        accept_line = False
        for raw_line in git_log.strip().split('\n'):
            gitlog_line = raw_line.strip()
            if not gitlog_line:
                continue
            if re.match(r'^[a-f0-9]{7,}\s', gitlog_line):
                accept_line = True
            if accept_line:
                lines.append(gitlog_line)

        # gather changelog
        for commit in lines:
            sha, msg = commit.split(None, 1)
            sha_short = sha[:7]
            commits.append(Commit(sha=sha, sha_short=sha_short, msg=msg))

    base_commit = commits[-1] if commits else None
    release_commit = commits[0] if commits else None
    changelog_commits = _get_commits_for_release(commits[:-1], auto=bool(teamcity_release_sha))

    return Release(base=base_commit, release=release_commit, changelog=changelog_commits)


def _get_revision_diff(from_revision, to_revision):
    return sudo(f'git --no-pager log --pretty=oneline --no-color --no-decorate {from_revision}..{to_revision}')


def _get_commits_for_release(commits: List[Commit], auto: bool = False) -> List[Commit]:
    candidate_commits = OrderedDict([
        (commit.sha, commit)
        for commit in commits
    ])

    # do not prompt for release sha in auto mode
    if not auto and len(commits) > 1:
        commits_log = '\n'.join([
            f'{commit.sha} {commit.msg}'
            for i, commit in enumerate(commits)
        ])
        release_commit_sha = None

        fastprint(f'You are about to release commits (not tip of master branch):\n{commits_log}\n')
        while not release_commit_sha:
            commit_text_user_prompt = prompt('Type full commit hash you are releasing >',
                                             validate=lambda n: n if len(n) == 40 else False)
            if not commit_text_user_prompt:
                warn('There should be 40 characters in commit hash')
            elif commit_text_user_prompt not in candidate_commits:
                warn(f'Your input "{commit_text_user_prompt}" does not match any commit hash:\n{commits_log}')
            else:
                release_commit_sha = commit_text_user_prompt

        # drop all the top commits not matching the chosen one
        for candidate_commit_sha in list(candidate_commits):
            if candidate_commit_sha == release_commit_sha:
                break
            else:
                candidate_commits.pop(candidate_commit_sha)

    # reverse the order of commits
    return list(candidate_commits.values())


class FabricException(Exception):
    pass


def with_deploy_lock(set_lock_task, delete_lock_task):
    def decorator(deploy_task):
        @wraps(deploy_task)
        def inner(*args, **kwargs):
            lock_acquired = list(execute(set_lock_task).values())[0]
            if not lock_acquired:
                abort('deploy lock is set')
            with settings(abort_exception=FabricException):
                try:
                    result = deploy_task(*args, **kwargs)
                finally:
                    execute(delete_lock_task)
            return result
        return inner
    return decorator
