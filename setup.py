from setuptools import setup, find_packages
from pathlib import Path

with open("README.rst", "r") as fh:
    long_description = fh.read()

setup(
    name='altocumulus',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description="Command line utilities for running workflows",
    author="Yiming Yang, Joshua Gould, Bo Li",
    author_email="cumulus-support@googlegroups.com",
    url='https://github.com/lilab-bcb/altocumulus',
    long_description=long_description,
    packages=find_packages(include=['alto']),
    include_package_data=True,
    install_requires=[
        l.strip() for l in Path("requirements.txt").read_text("utf-8").splitlines()
    ],
    license="BSD license",
    zip_safe=False,
    keywords=['Terra', 'Cromwell'],
    classifiers=[  # https://pypi.python.org/pypi?%3Aaction=list_classifiers
            'License :: OSI Approved :: BSD License',
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'Natural Language :: English',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 3',
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            'Topic :: Scientific/Engineering :: Bio-Informatics'
    ],
    python_requires='>= 3.8',
    entry_points={'console_scripts': ['alto=alto.__main__:main']},
)
