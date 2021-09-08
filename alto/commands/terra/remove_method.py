import argparse

from firecloud import api as fapi
from alto.utils import *



def main(argv):
    parser = argparse.ArgumentParser(description='Remove methods from Broad Methods Repository.')
    parser.add_argument('-m', '--method', dest='method', action='store', required=True, help='Method takes the format of namespace/name/version. If only namespace is provided, delete all methods under that namespace. If both namespace and name are provided, delete all snapshots for that method. If namespace, name and version are provided, only delete the specific snapshot.')
    args = parser.parse_args(argv)

    fields = args.method.split('/')
    if len(fields) == 0:
        raise ValueError('No namespace specified!')

    method_namespace = fields[0]
    method_name = fields[1] if len(fields) > 0 else None
    method_version = fields[2] if len(fields) > 1 else None

    methods = fapi.list_repository_methods(namespace=method_namespace, name=method_name).json()
    if len(methods) == 0:
        raise ValueError('No methods found')

    if method_name is None:  # delete all methods under specified namespace
        for method in methods:
            if method['namespace'] == method_namespace:
                fapi.delete_repository_method(method['namespace'], method['name'], method['snapshotId'])
                print(f'Deleted {method["namespace"]}/{method["name"]}/{method["snapshotId"]}')
    elif method_version is None:  # delete all versions
        for selected_method in methods:
            if selected_method['namespace'] == method_namespace and selected_method['name'] == method_name:
                fapi.delete_repository_method(selected_method['namespace'], selected_method['name'], selected_method['snapshotId'])
                print(f'Deleted {selected_method["namespace"]}/{selected_method["name"]}/{selected_method["snapshotId"]}')
    else: # delete the specific version
        selected_method = methods[0]
        fapi.delete_repository_method(selected_method['namespace'], selected_method['name'], selected_method['snapshotId'])
        print(f'Deleted {selected_method["namespace"]}/{selected_method["name"]}/{selected_method["snapshotId"]}')
