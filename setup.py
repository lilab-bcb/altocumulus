#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = [
        'firecloud', 'numpy', 'pandas', 'python-dateutil', 'matplotlib', 'six'
]

setup_requirements = [
        # put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
        'unittest'
]

setuptools.setup(
    name='altocumulus',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description="Command line utilities for running workflows",
    author="Cumulus Team",
    author_email='cumulus@broadinstitute.org',
    url='https://github.com/klarman-cell-observatory/altocumulus',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(include=['alto']),
    include_package_data=True,
    install_requires=requirements,
    license="BSD license",
    zip_safe=False,
    keywords='Terra',
    classifiers=[
            'License :: OSI Approved :: BSD License',
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'Natural Language :: English',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Topic :: Scientific/Engineering :: Bio-Informatics'
    ],
    test_suite='tests',
    tests_require=test_requirements,
    python_requires='>= 3',
    entry_points={
            'console_scripts': [
                    'alto=alto.__main__:main'
            ]
    }
)
