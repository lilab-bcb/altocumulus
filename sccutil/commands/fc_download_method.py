import argparse
from firecloud import api as fapi
import sccutil


def main(argsv):
    parser = argparse.ArgumentParser(description='Download one or more methods from FireCloud')
    parser.add_argument('-m', '--method', dest='method', action='store', required=True,
        help=sccutil.METHOD_HELP)

    args = parser.parse_args(argsv)
    method_namespace, method_name, method_version = sccutil.fs_split(args.method)
    list_methods = fapi.list_repository_methods(namespace=method_namespace, name=method_name, snapshotId=method_version)
    if list_methods.status_code != 200:
        raise ValueError('Unable to list methods ' + ' - ' + str(list_methods.json))
    methods = list_methods.json()
    for method in methods:
        wdl = fapi.get_repository_method(method_namespace, method_name, method['snapshotId']).json()['payload']
        with open('{}_{}.wdl'.format(method_name, method['snapshotId']), 'w') as w:
            w.write(wdl)
