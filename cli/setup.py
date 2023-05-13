#!/usr/bin/env python3

from setuptools import setup

setup(
    name="asyncmd",
    version="0.0.1",
    description="asyncmd CLI tool",
    url="http://github.com/Crglglz/asyncmd",
    author="Carlos Gil Gonzalez",
    author_email="carlosgilglez@gmail.com",
    license="MIT",
    packages=["asyncmd"],
    zip_safe=False,
    include_package_data=True,
    scripts=["bin/asyncmd"],
    install_requires=[
        "argcomplete>=2.0.0",
        "asyncio_mqtt",
        "pyyaml",
        "tqdm",
    ],
)
