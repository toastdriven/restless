#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup

import restless


setup(
    name='restless',
    version=restless.VERSION,
    description='A lightweight REST miniframework for Python.',
    author='Daniel Lindsley',
    author_email='daniel@toastdriven.com',
    url='https://github.com/toastdriven/restless/',
    long_description=open('README.rst', 'r').read(),
    packages=[
        'restless',
    ],
    requires=[
        'six(>=1.4.0)',
    ],
    install_requires=[
        'six>=1.4.0',
    ],
    tests_require=[
        'mock',
        'tox',
    ],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Flask',
        'Framework :: Pyramid',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Utilities'
    ],
)
