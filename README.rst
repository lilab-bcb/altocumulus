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

Command line utilities for running workflows on `Terra <https://app.terra.bio>`_ or `Cromwell <https://cromwell.readthedocs.io>`_ including:

- Run a Terra method, and bulk add/delete methods on Terra.
- Submit WDL workflow jobs to a sever running Cromwell, as well as check jobs' status, abort jobs, and get logs.
- Replace local file paths with remote Cloud (Google Cloud or Amazon AWS) bucket URIs, and automatically upload referenced files to Cloud buckets.
- Parse monitoring log files to determine optimal instance type and disk space.

Important tools used by Altocumulus:

- `FireCloud Swagger <https://api.firecloud.org/>`_
- `Dockstore Swagger <https://dockstore.org/api/static/swagger-ui/index.html>`_
- `FireCloud Service Selector <https://github.com/broadinstitute/fiss>`_ (FISS). In particular, `fiss/firecloud/api.py <https://github.com/broadinstitute/fiss/blob/master/firecloud/api.py>`_.
