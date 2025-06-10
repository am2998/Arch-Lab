#!/usr/bin/env python3
# ZFS Assistant - Setup script
# Author: GitHub Copilot

from setuptools import setup, find_packages

# Read requirements
with open('src/requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="zfs-assistant",
    version="0.1.0",
    packages=['zfs_assistant'],
    package_dir={'zfs_assistant': 'src'},
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'zfs-assistant=zfs_assistant.__main__:main',
        ],
    },
    python_requires='>=3.6',
    author="am2998",
    description="A GUI tool for managing ZFS snapshots",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
)
