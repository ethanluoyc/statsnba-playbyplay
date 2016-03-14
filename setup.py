#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'requests', 'pandas', 'pymongo', 'luigi'
]

test_requirements = [
    'pytest'
]

setup(
    name='statsnba-playbyplay',
    version='0.1.0',
    description="Package for parsing play-by-play data from stats.nba.com",
    long_description=readme + '\n\n' + history,
    author="Yicheng Luo",
    author_email='ethanluoyc@gmail.com',
    url='https://github.com/ethanluoyc/statsnba-playbyplay',
    packages=[
        'statsnba',
    ],
    package_dir={'statsnba':
                 'statsnba'},
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=False,
    keywords='statsnba',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
