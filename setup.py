# stargazers
# Copyright (C) 2020 Bruno Constanzo
#
# This program is free software; you can redistribute it and/or modify it under the terms of the GNU
# Lesser General Public License as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program; if not,
# write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA 

from setuptools import setup, find_packages
import haruspex

with open("README.md") as f_readme:
    long_desc = f_readme.read()

setup(
    name = "haruspex",
    version = haruspex.__version__,
    description = "filesystem haruspicy",
    long_description = long_desc,
    long_description_content_type='text/markdown',
    author = "Bruno Constanzo",
    author_email = "bconstanzo@ufasta.edu.ar",
    license = "LGPL 2.1",
    #install_requires = [],
    python_requires='>=3.6',
    packages = find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: System :: Filesystems',
        'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Programming Language :: Python :: 3.6',
    ],
    project_urls={
        #'Funding': 'https://donate.pypi.org',
        'Source': 'https://github.com/bconstanzo/haruspex/',
        #'Tracker': 'https://github.com/bconstanzo/haruspex/issues',
    },
)
