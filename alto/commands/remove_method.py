import argparse
from firecloud import api as fapi
import alto


def main(argsv):
    parser = argparse.ArgumentParser(description='Remove one or more methods from Broad Methods Repository')

    parser.add_argument('-m', '--method', dest='method', action='store', required=True, help=alto.METHOD_HELP)
    args = parser.parse_args(argsv)

    method_namespace, method_name, method_version = alto.fs_split(args.method)
    if method_namespace is None:
        raise ValueError('No namespace specified')
    if method_name == '':
        method_name = None

    methods = fapi.list_repository_methods(namespace=method_namespace, name=method_name).json()
    if len(methods) == 0:
        raise ValueError('No methods found')
    if method_name is None:  # delete all methods under specified namespace
        for method in methods:
            if method['namespace'] == method_namespace:
                fapi.delete_repository_method(method['namespace'], method['name'], method['snapshotId'])
                print('Deleted {}/{}:{}'.format(method['namespace'], method['name'], method['snapshotId']))
    else:
        if method_version is None:  # delete all versions
            for selected_method in methods:
                if selected_method['namespace'] == method_namespace and selected_method['name'] == method_name:
                    fapi.delete_repository_method(selected_method['namespace'], selected_method['name'],
                        selected_method['snapshotId'])
                    print('Deleted {}/{}:{}'.format(selected_method['namespace'], selected_method['name'],
                        selected_method['snapshotId']))
        else:
            selected_method = methods[0]
            fapi.delete_repository_method(selected_method['namespace'], selected_method['name'],
                selected_method['snapshotId'])
            print('Deleted {}/{}:{}'.format(selected_method['namespace'], selected_method['name'],
                selected_method['snapshotId']))
