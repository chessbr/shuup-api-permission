# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

try:
    long_description = open("README.md").read()
except IOError:
    long_description = ""

setup(
    name="shuup-api-permission",
    version="0.1.0",
    description="Shuup API Permission",
    license="MIT",
    author="Christian Hess",
    packages=find_packages(),
    install_requires=[
        "rest-jwt-permission>=0.2.0,<2"
    ],
    long_description=long_description,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 2.7",
    ]
)
