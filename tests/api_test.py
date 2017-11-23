# coding: utf-8

import pytest

from fabric_utils.git import *


@pytest.mark.parametrize('branch,domain', [
    ('demo', 'demo'),
    ('feature/some-stuff-MYB-3456', 'myb3456'),
    (u'feature/soMR3ALLyЩЩЩЩ12238__feature-1', 'feature-somr3ally-12238-feature-1'),
    ('master', 'master'),
])
def test_branch_to_domain_replacer(branch, domain):
    assert branch_to_domain(branch, domain_pattern=(r'^.*myb-?(\d+)$', r'myb\1')) == domain


@pytest.mark.parametrize('branch,domain', [
    ('feature/some-stuff-MYB-3456', 'MYB-3456'),
])
def test_branch_to_domain_no_replacer(branch, domain):
    assert branch_to_domain(branch, domain_pattern=r'^.*(myb-?\d+)$') == domain


def test_get_active_branch_name_smoke():
    assert get_active_branch_name('.')


@pytest.mark.parametrize('branch,slug', [
    ('feature/some-stuff-MYB-3456', 'some-stuff-myb-3456'),
    ('master', 'master'),
])
def test_branch_to_slug(branch, slug):
    assert branch_to_slug(branch) == slug


@pytest.mark.parametrize('branch,db_name', [
    ('feature/some-stuff-MYB-3456', 'featuresomestuffmyb3456'),
    ('master', 'master'),
])
def test_branch_to_db(branch, db_name):
    assert branch_to_db(branch) == db_name


@pytest.mark.parametrize('branch,url', [
    ('feature/some-stuff-MYB-3456', 'feature-some-stuff-myb-3456.example.com'),
    ('master', 'example.com'),
])
def test_branch_to_url(branch, url):
    assert branch_to_url('example.com', branch) == url
