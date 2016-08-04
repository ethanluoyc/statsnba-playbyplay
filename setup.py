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
    'requests', 'pandas', 'pymongo', 'luigi', 'inflection'
]

test_requirements = [
    'pytest'
]

setup(
    name='statsnba-playbyplay',
    version='0.2.0',
    description="Package for parsing play-by-play data from stats.nba.com",
    long_description=readme,
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
    license="MIT",
    zip_safe=False,
    keywords='statsnba',
    classifiers=[],
    test_suite='pytest',
    tests_require=test_requirements
)
