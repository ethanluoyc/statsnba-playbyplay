#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'requests', 'gevent', 'pandas', 'pymongo', 'grequests', 'luigi', 'pytest' # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='statsnba-pbp',
    version='0.1.0',
    description="API access package for playbyplay data on Stats NBA",
    long_description=readme + '\n\n' + history,
    author="Yicheng Luo",
    author_email='ethanluoyc@gmail.com',
    url='https://github.com/ethanluoyc/statsnba-pbp',
    packages=[
        'statsnba-pbp',
    ],
    package_dir={'statsnba-pbp':
                 'statsnba'},
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=False,
    keywords='statsnba-pbp',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
