#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    name='restless',
    version='2.0.1',
    description='A lightweight REST miniframework for Python.',
    author='Daniel Lindsley',
    author_email='daniel@toastdriven.com',
    url='http://github.com/toastdriven/restless/',
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
    ],
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
        'Programming Language :: Python :: 3',
        'Topic :: Utilities'
    ],
)
