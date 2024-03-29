.. role:: small

Version 2.3.0 :small:`June 21, 2023`
----------------------------------------

* Add ``cromwell get_task_status`` command to get a summary JSON file on the status of all WDL tasks of a job.

Version 2.2.0 :small:`November 4, 2022`
----------------------------------------

* In ``cromwell run`` command, automatically create zip file on dependency WDLs for a local WDL workflow.
* Remove ``query`` command.
* Bug fix.

Version 2.1.2 :small:`August 15, 2022`
--------------------------------------

* Bug fix on BCL folder and FASTQ file uploading. [PR `#30 <https://github.com/lilab-bcb/altocumulus/pull/30>`_]
* In ``cromwell list_jobs`` command, assign informative names for jobs with ``nan`` workflow name. [PR `#31 <https://github.com/lilab-bcb/altocumulus/pull/31>`_ and `#32 <https://github.com/lilab-bcb/altocumulus/pull/32>`_]

Version 2.1.1 :small:`August 12,2022`
--------------------------------------

* Add ``--type`` option to ``query`` command to specify query type.

Version 2.1.0 :small:`August 4, 2022`
--------------------------------------

* Altocumulus now only works with Python 3.8+.
* Improve FASTQ file uploading. [PR `#28 <https://github.com/lilab-bcb/altocumulus/pull/28>`_]
* Add ``query`` command to query project metadata from a LIMS (Laboratory Information Management System) via RESTful APIs.

Version 2.0.3 :small:`May 24, 2022`
--------------------------------------

* Support uploading only the FASTQ files with filename prefix specified within the source folder, instead of the whole folder, to the Cloud. [PR `#24 <https://github.com/lilab-bcb/altocumulus/pull/24>`_]
* In ``cromwell list_jobs`` command, add ``-n`` option to show only top *n* jobs. [PR `#21 <https://github.com/lilab-bcb/altocumulus/pull/21>`_]
* Bug fix:

  * Make all the temporary files with filenames unique per process, and remove them even when submission fails.
  * Fix the issue in ``cromwell list_jobs`` command when workflows' names are not returned by Cromwell API. [PR `#20 <https://github.com/lilab-bcb/altocumulus/pull/20>`_ by `Asma Bankapur <https://github.com/asmariyaz23>`_]
  * Fix the issue in ``cromwell get_logs`` command when no subworkflow exists in a WDL subtask call. [PR `#22 <https://github.com/lilab-bcb/altocumulus/pull/22>`_]

Version 2.0.2 :small:`March 16, 2022`
--------------------------------------

* Fix the issue when submitting jobs using Dockstore workflow without specifying version (i.e. implicitly using default version):

  * Dockstore API points to an incorrect path in the top-level ``workflow_path`` value.
  * So always search through all versions to use the corresponding ``workflow_path`` inside the default version entry.

Version 2.0.1 :small:`March 1, 2022`
--------------------------------------

* Add ``--profile`` option to allow use a specific AWS profile when dealing with AWS backend:

  * In **terra** command: ``run`` and ``get_logs`` sub-commands.
  * In **upload** command.
* In **cromwell** ``run`` sub-command:

  * Add ``-d`` option to allow attach dependency WDL files along with the main workflow WDL file specified in ``-m`` option.
  * Fix the issue on processing floating numbers in workflow input JSON files.

Version 2.0.0 :small:`January 12, 2022`
----------------------------------------

* Make method-related commands in legacy version as sub-commands under **terra** command, including:

  * ``run``, ``add_method``, ``remove_method``, ``storage_estimate``.
* Create sub-commands under **cromwell** command for interaction between users and Cromwell server, including:

  * ``run``, ``check_status``, ``abort``, ``get_metadata``, ``get_logs``, ``list_jobs``.
* Make uploading local data to Cloud buckets a separate command **upload**.
* Add **parse_monitoring_log** command to extract computing resource usage info from monitoring logs generated by Cumulus_ WDL workflows.

Version 1.1.1 :small:`September 3, 2021`
-----------------------------------------

Legacy version:

- Make sure that float values would look the same as in JSON input. For example, if ``0.00005`` is given, altocumulus should pass ``0.00005`` instead of ``5e-05`` to Terra.

.. _Cumulus: https://cumulus.readthedocs.io
