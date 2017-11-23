# coding: utf-8
from __future__ import absolute_import
import os
import re

from git import Repo

__all__ = [
    'get_active_branch_name',
    'branch_to_domain',
    'branch_to_slug',
    'branch_to_db',
]


def get_active_branch_name(path=None):
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
    domain = re.sub(r'-{2,}', '-', domain)
    # replace master with empty string
    return re.sub(r'^master$', '', domain)


def branch_to_slug(branch_name, **kwargs):
    """
    Convert branch name to valid slug
    """
    if branch_name == 'master':
        return branch_name
    return branch_to_domain(branch_name.split('/', 1)[-1], **kwargs)


def branch_to_db(branch_name, **kwargs):
    """
    Convert branch name to valid database name
    """
    if branch_name == 'master':
        return branch_name
    return branch_to_domain(branch_name, **kwargs).replace('-', '')
