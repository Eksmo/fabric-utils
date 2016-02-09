# coding: utf-8
from fabric.api import env, sudo


def psql(sql):
    sudo('psql {} -c "{};"'.format(env.pgdb, sql), user=env.pguser)


def createdb(name, user=None, **kwargs):
    if user:
        kwargs['OWNER'] = user
    if kwargs:
        options = ' '.join(('{}="{}"'.format(*item) for item in kwargs.items()))
    else:
        options = ''
    psql('CREATE DATABASE "{}" {}'.format(name, options).rstrip())


def dropdb(name):
    psql('DROP DATABASE "{}"'.format(name))
