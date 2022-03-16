import os
import requests
from urllib.parse import urljoin
from typing import Tuple


dockstore_api = "https://dockstore.org/api/"



def parse_dockstore_workflow(workflow_string: str) -> Tuple[str, str, str, str]:
    """Split a Dockstore workflow string.

    Parameters
    ----------
    worklfow_string: `str`
        Workflow string takes the format of 'organization:collection:workflow:version'. Version information is optional.

    Returns
    -------
    `tuple` object.
        A tuple containing organization, collection, workflow and version strings.

    Examples
    --------
    >>> organization, collection, workflow, version = parse_dockstore_workflow('broadinstitute:cumulus:cumulus:1.5.0')
    """
    fields = workflow_string.split(':')
    if len(fields) < 3 or len(fields) > 4:
        raise ValueError(f"workflow_string should contain only 3 or 4 items. But {workflow_string} contains {len(fields)} items!")

    organization = fields[0]
    collection = fields[1]
    workflow = fields[2]
    version = fields[3] if len(fields) == 4 else None

    return organization, collection, workflow, version


def get_dockstore_workflow(
    organization: str,
    collection: str,
    workflow: str,
    version: str = None,
    ssl_verify: bool = True,
) -> dict:
    """Locate a workflow using the organization, collection and workflow hierachy and return results in a dictionary.

    Parameters
    ----------
    organization: `str`
        The organization that workflow belongs to. You can find this string by clicking an organization in Dockstore and extract the basename in the URL. For example, this is the URL for Broad Institute 'https://dockstore.org/organizations/BroadInstitute' and you can infer Broad Institute's organization name is 'BroadInstitute'. This parameter is case-insensitive.
    collection: `str`
        The collection that the workflow belongs to. Similarly you can find the collection name using URL (e.g. 'https://dockstore.org/organizations/BroadInstitute/collections/Cumulus' suggests 'Cumulus' is the collection name). The collection must be under the organization and is case-insensitive.
    workflow: `str`
        The workflow name. This parameter is case-insensitive.
    version: `str`, optional (default: None)
        The workflow version to use. This parameter is case-insensitive. By default, the default version recorded in Dockstore would be used.
    ssl_verify: `bool`, optional (default: `True`)
        `True` if enable the SSL verification for GET requests.

    Returns
    -------
    `dict` object.
        A dictionary object containing the following entries:
            'name': workflow name as recorded in Dockstore.
            'path': workflow path as recorded in Dockstore.
            'version': workflow version.
            'workflow_path': workflow_path (relative path in Github).
            'url': URL to the WDL file.
            'methodPath': Method path that can be recognized by the Terra platform.
            'methodUri': Uniform Resource Identifier that can be recognized by the Terra platform.

    Examples
    --------
    >>> results = get_dockstore_workflow('broadinstitute', 'cumulus', 'cumulus')
    """
    org = requests.get(urljoin(dockstore_api, f"organizations/name/{organization}"), verify=ssl_verify)
    if org.status_code != 200:
        raise ValueError(f"Unable to locate organization {organization} - {org.content.decode()}!")
    coll = requests.get(urljoin(dockstore_api, f"organizations/{organization}/collections/{collection}/name"), verify=ssl_verify)
    if coll.status_code != 200:
        raise ValueError(f"Unable to locate collection {collection} - {coll.content.decode()}!")

    workflow_l = workflow.lower() # convert to lowercase
    find_workflow = False
    for entry in coll.json()["entries"]:
        workflow_name = os.path.basename(entry["entryPath"]).lower()
        if workflow_l == workflow_name:
            find_workflow = True
            break

    if not find_workflow:
        raise ValueError(f"Unable to locate workflow {workflow} from collection {collection}!")

    workflow_id = entry["id"]

    workflow_entry = requests.get(urljoin(dockstore_api, f"workflows/published/{workflow_id}"), verify=ssl_verify)
    if workflow_entry.status_code != 200:
        raise ValueError(f"Unable to fetch information for workflow {workflow} - {workflow_entry.content.decode()}!")

    workflow_content = workflow_entry.json()

    if version is None:
        version = workflow_content["defaultVersion"]
        print(f"Workflow version is not specified. Using default version {version} instead.")

    version_l = version.lower()
    find_version = False
    for version_item in workflow_content["workflowVersions"]:
        if version_l == version_item["name"].lower():
            find_version = True
            break

    if not find_version:
        raise ValueError(f"Unable to locate workflow version {version} for workflow {workflow}!")

    if version_item["hidden"]:
        raise ValueError(f"Version {version} of workflow {workflow} is hidden. Unable to use it!")

    version = version_item["name"]
    workflow_path = version_item["workflow_path"]

    table = str.maketrans({'/': '%2F'})
    methodPath = workflow_content["full_workflow_path"].translate(table)

    # Get rid of "github.com" prefix.
    repo_path = '/'.join(workflow_content["path"].split('/')[1:])

    results = {
        "name": workflow_content["workflowName"],
        "path": workflow_content["path"],
        "version": version,
        "workflow_path": workflow_path,
        "url": f"https://raw.githubusercontent.com/{repo_path}/{version}{workflow_path}",
        "methodPath": methodPath,
        "methodUri": f"dockstore://{methodPath}/{version}"
    }

    return results
