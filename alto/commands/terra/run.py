import argparse
from typing import Union

from alto.utils import *



def detect_workflow_source(workflow_string: str) -> str:
    """Detect if a workflow is from Dockerstore or Broad Methods Repository
    """
    if workflow_string.find(':') >= 0:
        return 'Dockstore'
    return 'Broad Methods Repository'


def convert_inputs(inputs: dict) -> dict:
    """ Convert elements in the dictionary loaded by json to formats that Terra accepts as inputs
    """
    results = {}
    for key, value in inputs.items():
        if isinstance(value, bool):
            value = 'true' if value else 'false'
        elif isinstance(value, str) and value.startswith(prefix_float) :
            # input is float, prefix_float + 'float'
            value = value[len(prefix_float):]
        elif isinstance(value, str):
            value = f'"{value}"'
        elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], str):
            for i in range(len(value)):
                value[i] = f'"{value[i]}"'
            value = f'[{",".join(value)}]'
        else:
            value = str(value)
        results[key] = value
    return results


def submit_to_terra(
    workflow_string: str, 
    workspace: str, 
    wdl_inputs: Union[str, dict], 
    out_json: str = None, 
    bucket_folder: str = None, 
    use_callcache: bool = True
) -> str:
    """Submit a workflow to Terra. The workflow can from either Dockstore or Broad Methods Repository.

    Parameters
    ----------
    workflow_string: `str`
        String indicating which workflow to use. The workflow can come from either Dockstore or Broad Methods Repository. If it comes from Dockstore, specify the name as organization:collection:name:version (e.g. broadinstitute:cumulus:cumulus:1.5.0) and the default version would be used if version is omitted. If it comes from Broad Methods Repository, specify the name as namespace/name/version (e.g. cumulus/cumulus/43) and the latest snapshot would be used if version is omitted.
        
    workspace: `str`
        Terra Workspace name, which consists of a namespace and a name.

    wdl_inputs: `str` or `dict`
        Workflow inputs specified as a JSON file. If wdl_inputs is `str`, it refers to the path to the JSON file. Otherwise, it is a dictionary representing an in-memory JSON.

    out_json: `str`, optional (default: None)
        Path for the updated JSON file where local paths are replaced by gs URLs. Specify this parameter implies that users want altocumulus to transfer local files to the workspace-asscociated Google Bucket.

    bucket_folder: `str`, optional (default: None)
        This pamameter refers to a local path under the workspace-associated Google Bucket. Local files will be uploaded under this folder.
    
    use_callcache: `bool`, optional (default: True)
        If use call caching. 

    Returns
    -------
    `str` object.
        A URL referring to the job status would be returned.

    Examples
    --------
    >>> status_url = submit_to_terra('broadinstitute:cumulus:cumulus', 'kco-tech/Cumulus', 'cumulus_inputs.json', out_json = 'cumulus_inputs_updated.json', bucket_folder = 'cumulus_input', cache = True)
    """
    inputs = read_wdl_inputs(wdl_inputs)  # read inputs from JSON

    # check method 
    workflow_def = None
    config_namespace = config_name = None
    if detect_workflow_source(workflow_string) == 'Dockstore':
        organization, collection, workflow, version = parse_dockstore_workflow(workflow_string)
        config_namespace = collection
        config_name = workflow
        workflow_def = get_dockstore_workflow(organization, collection, workflow, version)
    else:
        namespace, name, version = parse_firecloud_workflow(workflow_string)
        config_namespace = namespace
        config_name = name
        workflow_def = get_firecloud_workflow(namespace, name, version)

    # check workspace
    workspace_namespace, workspace_name = parse_workspace(workspace)
    workspace_def = get_workspace_info(workspace_namespace, workspace_name)

    # upload input data to google bucket and generate modified JSON input file
    if out_json is not None:
        bucket = workspace_def['bucketName']
        upload_to_cloud_bucket(inputs, 'gcp', bucket, bucket_folder, out_json, False)

    # update workflow configuration in the workspace
    method_body = {
        'namespace': config_namespace,
        'name': config_name,
        'rootEntityType': None, # Do not use data model
        'inputs': convert_inputs(inputs),
        'outputs': {},
        'prerequisites': {},
        'methodRepoMethod': {
            'methodUri': workflow_def['methodUri']
        },
        'methodConfigVersion': 1,
        'deleted': False
    }
    update_workflow_config_in_workspace(config_namespace, config_name, method_body, workspace_namespace, workspace_name)

    # submit a job to terra
    return submit_a_job_to_terra(workspace_namespace, workspace_name, config_namespace, config_name, use_callcache = use_callcache)



def main(argv):
    parser = argparse.ArgumentParser(description='Submit workflows to Terra for execution. Workflows can from either Dockstore or Broad Methods Repository. If local files are detected, automatically upload files to the workspace Google Cloud bucket. For Dockstore workflows, collection and name would be used as config namespace and name respectively. Otherwise, namespace and name would be used. After a successful submission, a URL pointing to the job status would be printed out.')
    parser.add_argument('-m', '--method', dest='method', action='store', required=True, 
        help='Workflow name. The workflow can come from either Dockstore or Broad Methods Repository. If it comes from Dockstore, specify the name as organization:collection:name:version (e.g. broadinstitute:cumulus:cumulus:1.5.0) and the default version would be used if version is omitted. If it comes from Broad Methods Repository, specify the name as namespace/name/version (e.g. cumulus/cumulus/43) and the latest snapshot would be used if version is omitted.')
    parser.add_argument('-w', '--workspace', dest='workspace', action='store', required=True,
        help='Workspace name (e.g. foo/bar). The workspace is created if it does not exist')
    parser.add_argument('--bucket-folder', metavar='<folder>', dest='bucket_folder', action='store',
        help='Store inputs to <folder> under workspace''s google bucket')
    parser.add_argument('-i', '--input', dest='wdl_inputs', action='store', required=True,
        help='WDL input JSON.')
    parser.add_argument('-o', '--upload', dest='out_json', metavar='<updated_json>', action='store',
        help='Upload files/directories to the workspace Google Cloud bucket and output updated input json (with local path replaced by google bucket urls) to <updated_json>.')
    parser.add_argument('--no-cache', dest='no_cache', action='store_true', help='Disable call caching.')
    args = parser.parse_args(argv)
    
    url = submit_to_terra(args.method, args.workspace, args.wdl_inputs, out_json = args.out_json, bucket_folder = args.bucket_folder, use_callcache = not args.no_cache)
    
    print(url)
