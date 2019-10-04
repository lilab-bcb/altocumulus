#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = [
        'firecloud', 'pandas'
]

setup_requirements = [
        # put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
        'unittest'
]

setuptools.setup(
    name='cumulus-util',
    version='0.1.0',
    description="Cumulus Utilities",
    author="Cumulus Team",
    author_email='cumulus@broadinstitute.org',
    url='https://github.com/klarman-cell-observatory/cumulus-util',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(include=['cumulus-util']),
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
    setup_requires=setup_requirements,
    python_requires='>= 3',
    entry_points={
            'console_scripts': [
                    'cumulus-util=cumulus_util.__main__:main'
            ]
    }
)
