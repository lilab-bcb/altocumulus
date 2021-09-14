import os
import json
import warnings
from typing import Tuple

from firecloud import api as fapi

warnings.filterwarnings('ignore', 'Your application has authenticated', UserWarning, 'google')



def parse_firecloud_workflow(workflow_string: str) -> Tuple[str, str, int]:
    """Split a Firecloud workflow string.

    Parameters
    ----------
    worklfow_string: `str`
        Workflow string takes the format of 'namespace/name/version'. Version information is optional.

    Returns
    -------
    `tuple` object.
        A tuple containing namespace, name and version strings.

    Examples
    --------
    >>> method_namespace, method_name, method_version = parse_firecloud_workflow('cumulus/cumulus/43')
    """
    fields = workflow_string.split('/')
    if len(fields) < 2 or len(fields) > 3:
        raise ValueError(f"workflow_string should contain only 2 or 3 items. But {workflow_string} contains {len(fields)} items!")

    namespace = fields[0]
    name = fields[1]
    version = int(fields[2]) if len(fields) == 3 else None

    return namespace, name, version


def get_firecloud_workflow(method_namespace: str, method_name: str, method_version: int = None) -> dict:
    """Locate a workflow using the method_namespace, method_name and method_version hierachy and return results in a dictionary.

    Parameters
    ----------
    method_namespace: `str`
        The namespace that workflow belongs to (case-sensitive).
    method_name: `str`
        The workflow name (case-sensitive).
    version: `int`, optional (default: None)
        Snapshot ID. By default, the lastest snapshot recorded in Broad Methods Repository would be used.

    Returns
    -------
    `dict` object.
        A dictionary object containing the following entries:
            'namespace': workflow namespace as recorded in Broad Methods Repository.
            'name': workflow name as recorded in Broad Methods Repository.
            'snapshotId': workflow version as recorded in Broad Methods Repository.
            'url': URL to the WDL file.
            'methodUri': Uniform Resource Identifier that is recognized by Terra platform.

    Examples
    --------
    >>> results = get_firecloud_workflow('cumulus', 'cumulus')
    """
    method_record = None

    if method_version is not None:
        method_def = fapi.get_repository_method(method_namespace, method_name, method_version)
        if method_def.status_code != 200:
            raise ValueError(f"Unable to fetch workflow {method_namespace}/{method_name}/{method_version} - {method_def.json()}!")
        method_record = method_def.json()
    else:
        list_methods = fapi.list_repository_methods(namespace=method_namespace, name=method_name)
        if list_methods.status_code != 200:
            raise ValueError(f"Unable to list methods - {list_methods.json()}!")
        methods = list_methods.json()
        if len(methods) == 0:
            raise ValueError(f"Unable to locate workflow {method_namespace}/{method_name}!")

        method_record = methods[0]
        for method in methods[1:]:
            if method_record["snapshotId"] < method["snapshotId"]:
                method_record = method

    results = {
        "namespace": method_record["namespace"],
        "name": method_record["name"],
        "snapshotId": method_record["snapshotId"],
        "url": f"https://api.firecloud.org/ga4gh/v1/tools/{method_record['namespace']}:{method_record['name']}/versions/{method_record['snapshotId']}/plain-WDL/descriptor",
        "methodUri": f"agora://{method_record['namespace']}/{method_record['name']}/{method_record['snapshotId']}"
    }

    return results


def parse_workspace(workspace: str) -> Tuple[str, str]:
    """Parse a workspace string
    """
    fields = workspace.split('/')
    if len(fields) != 2:
        raise ValueError(f"workspace {workspace} is not in the right format!")
    return fields[0], fields[1]


def get_workspace_info(workspace_namespace: str, workspace_name: str) -> dict:
    """Get workspace attributes using workspace_namespace and workspace_name.
    """
    ws = fapi.get_workspace(workspace_namespace, workspace_name)
    if ws.status_code == 404:
        raise ValueError(f"Unable to fetch information from workspace {workspace_namespace}/{workspace_name} - {ws.json()}!")
    return ws.json()["workspace"]


def update_workflow_config_in_workspace(config_namespace: str, config_name: str, method_body: dict, workspace_namespace: str, workspace_name: str):
    """Update workflow configuration in the given workspace. If config does not exist, create one.
    """
    config_exists = fapi.get_workspace_config(workspace_namespace, workspace_name, config_namespace, config_name)
    if config_exists.status_code == 200:
        config_submission = fapi.update_workspace_config(workspace_namespace, workspace_name, config_namespace, config_name, method_body)
        if config_submission.status_code != 200:
            raise ValueError(f"Unable to update workflow config {config_namespace}/{config_name} in the workspace {workspace_namespace}/{workspace_name}. Response: {config_submission.status_code} - {config_submission.json()}!")
    else:
        config_submission = fapi.create_workspace_config(workspace_namespace, workspace_name, method_body)
        if config_submission.status_code != 201:
            raise ValueError(f"Unable to create workflow config {config_namespace}/{config_name} in the workspace {workspace_namespace}/{workspace_name}. Response: {config_submission.status_code} - {config_submission.json()}!")


def submit_a_job_to_terra(workspace_namespace: str, workspace_name: str, config_namespace: str, config_name: str, use_callcache: bool = True) -> str:
    """Create a job submission to Terra and if success, return a URL for checking job status.
    """
    launch_submission = fapi.create_submission(workspace_namespace, workspace_name, config_namespace, config_name, use_callcache = use_callcache)
    if launch_submission.status_code != 201:
        raise ValueError(f"Unable to launch submission - {launch_submission.json()}!")

    submission_id = launch_submission.json()["submissionId"]
    status_url = f"https://app.terra.bio/#workspaces/{workspace_namespace}/{workspace_name}/job_history/{submission_id}"
    return status_url
