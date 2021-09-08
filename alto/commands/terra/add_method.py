import os
import argparse

from firecloud import api as fapi
from alto.utils import *



def main(argv):
    parser = argparse.ArgumentParser(description='Add one or more methods to Broad Methods Repository.')
    parser.add_argument('-n', '--namespace', dest='namespace', action='store', required=True, help='Methods namespace')
    parser.add_argument('-p', '--public', dest='public', action='store_true', help='Make methods publicly readable')
    parser.add_argument(dest='wdl', help='Path to WDL file.', nargs='+')
    args = parser.parse_args(argv)

    namespace = args.namespace
    public = args.public

    n_success = 0
    for wdl in args.wdl:
        method_name = os.path.basename(wdl)
        suffix = method_name.lower().rfind('.wdl')
        if suffix != -1:
            method_name = method_name[0:suffix]

        method_acl = []
        try:
            existing_method = get_firecloud_workflow(namespace, method_name)
            method_acl = fapi.get_repository_method_acl(namespace=existing_method['namespace'], method=existing_method['name'], snapshot_id=existing_method['snapshotId']).json()
        except ValueError:
            pass

        if public:
            existing_public_user = False
            for i in range(len(method_acl)):
                if method_acl[i]['user'] == 'public':
                    existing_public_user = True
                    method_acl[i] = dict(user='public', role='READER')
                    break
            if not existing_public_user:
                method_acl.append(dict(user='public', role='READER'))

        result = fapi.update_repository_method(namespace=namespace, method=method_name, wdl=wdl, synopsis='')
        if result.status_code == 201:
            result = result.json()
            if len(method_acl) > 0:
                fapi.update_repository_method_acl(namespace=result['namespace'], method=result['name'], snapshot_id=result['snapshotId'], acl_updates=method_acl)
            print(f'Workflow {method_name} is imported! See https://api.firecloud.org/ga4gh/v1/tools/{result["namespace"]}:{result["name"]}/versions/{result["snapshotId"]}/plain-WDL/descriptor')
            n_success += 1
        else:
            print(f'Unable to add workflow {method_name} - {result.json()}')

    print(f'Successfully added {n_success} workflows.')
