#!/usr/bin/env python3
# ZFS Assistant - Setup script for AppImage packaging
# Author: am2998

from setuptools import setup, find_packages
import os

# Read requirements
requirements_path = os.path.join('src', 'requirements.txt')
with open(requirements_path) as f:
    requirements = [line.strip() for line in f.readlines() 
                   if line.strip() and not line.startswith('#')]

# Read README
readme_path = 'README.md'
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()

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
    python_requires='>=3.8',
    author="am2998",
    description="A GUI tool for managing ZFS snapshots",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications :: GTK",
        "Topic :: System :: Filesystems",
        "Topic :: System :: Systems Administration",
        "Intended Audience :: System Administrators",
    ],
    keywords="zfs snapshot filesystem backup gui gtk",
    project_urls={
        "Source": "https://github.com/am2998/zfs-assistant",
        "Bug Reports": "https://github.com/am2998/zfs-assistant/issues",
    },
)
