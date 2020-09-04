import os
import re


__all__ = [
    'branch_to_db',
    'branch_to_domain',
    'branch_to_slug',
    'branch_to_url',
    'get_active_branch_name',
]


def get_active_branch_name(path=None):
    from git import Repo
    return Repo(path or os.getcwd()).active_branch.name


def branch_to_domain(branch_name, domain_pattern=None):
    """
    Convert a git branch name into a valid domain string.
    """
    # obtain domain name using regex
    if domain_pattern:
        if isinstance(domain_pattern, (tuple, list)):
            pattern, replacer = domain_pattern
        else:
            pattern, replacer = domain_pattern, None

        match_obj = re.search(pattern, branch_name, flags=re.I)
        if match_obj:
            if replacer:
                return re.sub(pattern, replacer, branch_name, flags=re.I)
            else:
                return match_obj.group(1)
    # replace all non-alphanumeric characters with a hyphen
    domain = re.sub(r'[^a-z0-9\-]', '-', branch_name.lower())
    # replace double hyphens with a single character
    return re.sub(r'-{2,}', '-', domain)


def branch_to_url(base_domain, branch_name, domain_pattern=None):
    domain = branch_to_domain(branch_name, domain_pattern)
    if domain == 'master':
        return base_domain
    return f'{domain}.{base_domain}'


def branch_to_slug(branch_name, **kwargs):
    """
    Convert branch name to valid slug
    """
    return branch_to_domain(branch_name.split('/', 1)[-1], **kwargs)


def branch_to_db(branch_name, **kwargs):
    """
    Convert branch name to valid database name
    """
    return branch_to_domain(branch_name, **kwargs).replace('-', '')
