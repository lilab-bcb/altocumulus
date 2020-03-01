import json
import os
import warnings
from typing import Tuple

from firecloud import api as fapi

warnings.filterwarnings('ignore', 'Your application has authenticated', UserWarning, 'google')

METHOD_HELP = 'Method namespace/name (e.g. regev/cellranger_mkfastq_count). A version can optionally be specified (e.g. regev/cell_ranger_mkfastq_count/4), otherwise the latest version of the method is used.'


def get_method(method_namespace: str, method_name: str, method_version: int = None) -> "JSON":
    """
        If method_version is None, get the latest snapshot
    """
    if method_version is None:    
        list_methods = fapi.list_repository_methods(namespace=method_namespace, name=method_name)
        if list_methods.status_code != 200:
            raise ValueError('Unable to list methods ' + ' - ' + str(list_methods.json()))
        methods = list_methods.json()
        version = -1
        for method in methods:
            version = max(version, method['snapshotId'])
        if version == -1:
            raise ValueError(method_name + ' not found')
        method_version = version    

    method_def = fapi.get_repository_method(method_namespace, method_name, method_version)
    if method_def.status_code != 200:
        raise ValueError('Unable to fetch method {0}/{1}/{2} - {3}'.format(method_namespace, method_name, method_version, str(method_def.json())))

    return method_def.json()


def get_or_create_workspace(workspace_namespace, workspace_name):
    ws = fapi.get_workspace(workspace_namespace, workspace_name)
    if ws.status_code == 404:
        ws = fapi.create_workspace(workspace_namespace, workspace_name)
        if ws.status_code != 201:
            raise ValueError('Unable to create workspace')
        return ws.json()
    else:
        return ws.json()['workspace']


def get_wdl_inputs(wdl_inputs):
    if type(wdl_inputs) != dict:
        if os.path.exists(wdl_inputs):
            with open(wdl_inputs, 'r') as f:
                return json.loads(f.read())
                # Filter out any key/values that contain #, and escape strings with quotes as MCs need this to not be treated as expressions
                # inputs = {k: "\"{}\"".format(v) for k, v in inputs_json.items() if '#' not in k}
        elif type(wdl_inputs) == str:
            return json.loads(wdl_inputs)
        else:
            print('Unknown input type: ' + str(type(wdl_inputs)))
    return wdl_inputs


def fs_split(s: str) -> Tuple[str, str, str]:
    """Split a FireCloud namespace/name/version string.

    Args:
        s: namespace/name/version. Version is optional

    Returns:
        Tuple of namespace, name, version
   """
    version = None
    sep = s.find('/')
    if sep == -1:
        return [None, None, None]
    namespace = s[0:sep]
    name = s[sep + 1:]
    # check for version
    sep = name.find('/')
    if sep != -1:
        version = int(name[sep + 1:])
        name = name[0:sep]
    return namespace, name, version


def create_submission(workspace_namespace: str, workspace_name: str, config_namespace: str, config_name: str, launch_entity: str, root_entity: str, use_callcache: bool = True) -> "Response":
    """
        Note that this function is adapted from fiss/firecloud/api.py/create_submission
    """
    uri = "workspaces/{0}/{1}/submissions".format(workspace_namespace, workspace_name)
    body = {
        "methodConfigurationNamespace" : config_namespace,
        "methodConfigurationName" : config_name,
        "useCallCache" : use_callcache
    }

    if launch_entity is not None:
        body["entityType"] = launch_entity
    if root_entity is not None:
        body["entityName"] = root_entity

    return fapi.__post(uri, json = body)
