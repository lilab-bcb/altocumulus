==============
Altocumulus
==============

|PyPI| |Python| |License| |Docs|

.. |PyPI| image:: https://img.shields.io/pypi/v/altocumulus.svg
   :target: https://pypi.org/project/altocumulus
.. |Python| image:: https://img.shields.io/pypi/pyversions/altocumulus
   :target: https://pypi.org/project/altocumulus
.. |License| image:: https://img.shields.io/github/license/lilab-bcb/altocumulus
   :target: https://github.com/lilab-bcb/altocumulus/blob/master/LICENSE
.. |Docs| image:: https://readthedocs.org/projects/altocumulus/badge/?version=latest
   :target: https://altocumulus.readthedocs.io

Command line utilities for running workflows on `Terra <https://app.terra.bio/>`_ or `Cromwell <https://github.com/broadinstitute/cromwell>`_ including:

- Run a Terra method. Replace local file paths with workspace Google Cloud bucket URLs. Automatically upload referenced files to workspace Google bucket.
- Bulk add/delete methods in Terra.
- Parse monitoring log files to determine optimal instance type and disk space.

Re: useful links:

`FireCloud Swagger <https://api.firecloud.org/>`_

`Dockstore Swagger <https://dockstore.org/api/static/swagger-ui/index.html>`_

`fiss <https://github.com/broadinstitute/fiss>`_ In particular, look at the api.py

Installation
+++++++++++++++

Use the commands below to install Altocumulus from repo::

    git clone https://github.com/lilab-bcb/altocumulus.git
    cd altocumulus
    pip install -e .

Usage
++++++++

Type ``alto`` for a list of all commands.


Legacy Release
+++++++++++++++++

Version `1.1.1 <https://github.com/klarman-cell-observatory/altocumulus>`_, making sure that float values would look the same as in json input. For example, if 0.00005 is given, altocumulus will pass '0.00005' instead of '5e-05' to Terra.
