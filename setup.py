#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import Command
import subprocess

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'requests', 'pandas', 'inflection'
]

test_requirements = [
    'pytest'
]


class CodeGenWrapper(Command):
    description = "Generate the wrapper for accessing statsnba's endpoint"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        subprocess.call(["make", "codegen-api"])


setup(
    name='statsnba-playbyplay',
    version='0.3.0',
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
    package_data={
        'statsnba': ['nba.json']
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='statsnba',
    classifiers=[],
    test_suite='pytest',
    tests_require=test_requirements,
    cmdclass={
        "api_wrapper": CodeGenWrapper
    }
)
