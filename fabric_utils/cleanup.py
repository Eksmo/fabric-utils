from datetime import datetime, date, timedelta
from typing import Callable, Any, List

from fabric.api import puts, task, settings, execute
from fabric.colors import green as g, yellow as y

from .ci import teamcity
from .helpers import to_bool


@task
def get_stale_docker_branches(run: Callable, *, days: int,
                              project_label: str, project_name: str, branch_label: str) -> List[str]:
    cmd = ("docker ps "
           "--format '{{ .Label \"%(branch_label)s\" }}:{{ .CreatedAt }}' "
           "--filter 'label=%(project_label)s=%(project_name)s'")
    result = run(cmd % {'branch_label': branch_label,
                        'project_label': project_label,
                        'project_name': project_name})
    stale_branches = []
    least_recent_date = (datetime.today() - timedelta(days=days)).date()

    for line in result.split('\n'):
        line = line.strip()
        if not line:
            continue

        branch_slug, timestamp = line.split(':', 1)
        if not branch_slug:
            continue

        branch_deploy_date = datetime.strptime(timestamp[:10], '%Y-%m-%d').date()
        if branch_deploy_date <= least_recent_date:
            stale_branches.append(branch_slug)

    return stale_branches


@task
def prune_stale_branches(get_stale_branches: Callable,
                         destroy_branch: Callable,
                         protected_branches: List[str],
                         days: int = 7, dry_run: bool = False, **kwargs: Any) -> None:
    """
    Destroy all branch instances that were last deployed this or greater days ago.
    Although demo and master should be kept protected from this deadly action.
    """
    inside_teamcity = kwargs.get('teamcity')
    dry_run = to_bool(dry_run)

    stale_branch_slugs = get_stale_branches(days=days)

    if dry_run:
        puts(g(f'Dry run. WONT destroy {len(stale_branch_slugs)} instances'))
    else:
        puts(y(f'WILL destroy {len(stale_branch_slugs)} instances'))

    total_count = 0
    failure_count = 0

    teamcity('testSuiteStarted', 'cleanup', force=inside_teamcity)

    for branch_slug in stale_branch_slugs:
        # protect essential branches
        if branch_slug in protected_branches:
            puts(f'wont remove protected branch {branch_slug}')
            continue

        puts(f'removing branch {branch_slug}')
        test_name = f'Destroy {branch_slug}'
        total_count += 1
        teamcity('testStarted', test_name, force=inside_teamcity)
        try:
            with settings(abort_exception=Exception):
                if not dry_run:
                    execute(destroy_branch, branch_slug)
                    puts(y(f'destroyed branch {branch_slug}'))
                else:
                    puts(g(f'would destroy branch {branch_slug}'))
        except Exception as exc:
            puts(f'failed to remove branch {branch_slug} due to {exc}')
            teamcity('testFailed', test_name, f'Exception: {type(exc).__name__}', force=inside_teamcity)
            failure_count += 1
        finally:
            teamcity('testFinished', test_name, force=inside_teamcity)

    teamcity('testSuiteFinished', 'cleanup', force=inside_teamcity)
    teamcity('buildStatus', f'Branches destroyed: {total_count}, failures: {failure_count}', force=inside_teamcity)
