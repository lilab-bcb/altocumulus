import argparse
import json
from typing import Union

from firecloud import api as fapi

import cumulus_util


def convert_inputs(inputs: dict) -> dict:
    results = dict()
    for key, value in inputs.items():
        if isinstance(value, bool):
            value = 'true' if value else 'false'
        elif isinstance(value, str):
            value = '"{0}"'.format(value)
        elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], str):
            for i in range(len(value)):
                value[i] = '"{0}"'.format(value[i])
            value = '[{0}]'.format(','.join(value))
        else:
            value = str(value)
        results[key] = value
    return results


def do_fc_run(method: str, workspace: str, wdl_inputs: Union[str, dict], out_json: str, bucket_folder: str) -> str:
    """Run a FireCloud method.

    Args:
        method: method namespace/name/version. Version is optional
        workspace: workspace namespace/name
        wdl_inputs: WDL input JSON.
        upload: Whether to upload inputs and convert local file paths to gs:// URLs.
        bucket_folder: The folder under google bucket for uploading files.

    Returns:
        URL to check submission status
   """
    inputs = cumulus_util.get_wdl_inputs(wdl_inputs)
    method_namespace, method_name, method_version = cumulus_util.fs_split(method)
    if method_version is None:
        version = -1
        list_methods = fapi.list_repository_methods(namespace = method_namespace, name = method_name)
        if list_methods.status_code != 200:
            raise ValueError('Unable to list methods ' + ' - ' + str(list_methods.json))
        methods = list_methods.json()
        for method in methods:
            assert method['namespace'] == method_namespace
            version = max(version, method['snapshotId'])
        if version == -1:
            raise ValueError(method_name + ' not found')
        method_version = version

    root_entity = None
    launch_entity = None
    workspace_namespace, workspace_name, workspace_version = cumulus_util.fs_split(workspace)
    cumulus_util.get_or_create_workspace(workspace_namespace, workspace_name)

    if out_json is not None:
        cumulus_util.do_fc_upload(inputs, workspace, False, bucket_folder)
        with open(out_json, 'w') as fout:
            json.dump(inputs, fout)
    config_namespace = method_namespace
    config_name = method_name

    method_body = {
        'name': config_name,
        'namespace': config_namespace,
        'methodRepoMethod': {'methodNamespace': method_namespace, 'methodName': method_name,
                             'methodVersion': method_version, 'sourceRepo': 'agora',
                             'methodUri': 'agora://{0}/{1}/{2}'.format(method_namespace, method_name, method_version)},
        'rootEntityType': root_entity,
        'prerequisites': {},
        'inputs': convert_inputs(inputs),
        'outputs': {},
        'methodConfigVersion': 1,
        'deleted': False
    }

    config_exists = fapi.get_workspace_config(workspace_namespace, workspace_name, config_namespace, config_name)

    if config_exists.status_code == 200:
        config_submission = fapi.update_workspace_config(workspace_namespace, workspace_name, config_namespace,
                                                         config_name, method_body)
        if config_submission.status_code != 200:
            raise ValueError('Unable to update workspace config. Response: ' + str(config_submission.status_code))

    else:
        config_submission = fapi.create_workspace_config(workspace_namespace, workspace_name, method_body)
        if config_submission.status_code != 201:
            raise ValueError('Unable to create workspace config - ' + str(config_submission.json()))

    launch_submission = fapi.create_submission(workspace_namespace, workspace_name, config_namespace, config_name,
                                               launch_entity, root_entity, "")

    if launch_submission.status_code == 201:
        submission_id = launch_submission.json()['submissionId']
        url = 'https://portal.firecloud.org/#workspaces/{}/{}/monitor/{}'.format(workspace_namespace, workspace_name,
                                                                                 submission_id)

        return url
    else:
        raise ValueError('Unable to launch submission - ' + str(launch_submission.json()))


def main(argsv):
    parser = argparse.ArgumentParser(
        description='Run a FireCloud method. Optionally upload files/directories to the workspace Google Cloud bucket.')
    parser.add_argument('-m', '--method', dest='method', action='store', required=True, help=cumulus_util.METHOD_HELP)
    parser.add_argument('-w', '--workspace', dest='workspace', action='store', required=True,
                        help='Workspace name (e.g. foo/bar). The workspace is created if it does not exist')
    parser.add_argument('--bucket-folder', metavar='<folder>', dest='bucket_folder', action='store',
                        help='Store inputs to <folder> under workspace''s google bucket')
    parser.add_argument('-i', '--input', dest='wdl_inputs', action='store', required=True,
                        help='WDL input JSON.')
    parser.add_argument('-o', '--upload', dest='out_json', metavar='<updated_json>', action='store',
                        help='Upload files/directories to the workspace Google Cloud bucket and output updated input json (with local path replaced by google bucket urls) to <updated_json>.')
    # parser.add_argument('-c', '--config_name', dest='config_name', action='store', required=False,
    #                     help='Method configuration name')
    args = parser.parse_args(argsv)
    url = do_fc_run(args.method, args.workspace, args.wdl_inputs, args.out_json, args.bucket_folder)
    print(url)
