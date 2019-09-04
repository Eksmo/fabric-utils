#!/usr/bin/env python
# coding: utf-8
import os
import re


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_version(package):
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


with open('README.rst') as readme_file:
    readme = readme_file.read()


requirements = [
    'GitPython>=1.0.1',
    'Jinja2>=2.7',
    'requests>=2.10.0'
]

setup(
    name='fabric-utils',
    version=get_version('fabric_utils'),
    description='MyBook Fabric Utils',
    long_description=readme,
    author='MyBook Devs',
    author_email='dev@mybook.ru',
    url='https://github.com/MyBook/fabric-utils',
    packages=['fabric_utils'],
    package_dir={'fabric_utils': 'fabric_utils'},
    include_package_data=True,
    install_requires=requirements,
    license='BSD',
    zip_safe=False,
    keywords='fabric utils',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)
