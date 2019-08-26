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
    name='sccutil',
    version='0.1.0',
    description="scCloud Utilities",
    author="scCloud Team",
    author_email='sccloud@broadinstitute.org',
    url='https://github.com/klarman-cell-observatory/sccutil',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(include=['sccutil']),
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
                    'sccutil=sccutil.__main__:main'
            ]
    }
)
