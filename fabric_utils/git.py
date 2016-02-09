# coding: utf-8
from __future__ import absolute_import
import os
import re

from git import Repo


def get_active_branch_name(path=None):
    return Repo(path or os.getcwd()).active_branch.name


def branch_to_slug(branch_name):
    return branch_to_domain(branch_name.split('/', 1)[-1])


def branch_to_domain(branch_name):
    return re.sub(r'-{2,}', '-', re.sub(r'[^a-zA-Z0-9\-]', '-', branch_name.lower()))


def branch_to_db(branch_name):
    return branch_to_domain(branch_name).replace('-', '')
