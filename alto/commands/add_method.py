import argparse
from firecloud import api as fapi
import os
import alto


def main(argsv):
    parser = argparse.ArgumentParser(description='Add one or more methods to Broad Methods Repository')
    parser.add_argument('-n', '--namespace', dest='namespace', action='store', required=True, help='Methods namespace')
    parser.add_argument('-p', '--public', dest='public', action='store_true', help='Make methods publicly readable')
    parser.add_argument(dest='wdl', help='Path to WDL file.', nargs='+')
    args = parser.parse_args(argsv)
    namespace = args.namespace
    public = args.public
    for wdl in args.wdl:
        method_name = os.path.basename(wdl)
        suffix = method_name.lower().rfind('.wdl')
        if suffix != -1:
            method_name = method_name[0:suffix]
        method_acl = []
        try:
            existing_method = alto.get_method(namespace, method_name)
            method_acl = fapi.get_repository_method_acl(namespace=existing_method['namespace'],
                method=existing_method['name'], snapshot_id=existing_method['snapshotId']).json()
        except ValueError:
            pass
        if public:
            existing_public_user = False
            for i in range(len(method_acl)):
                if method_acl[i]['user'] == 'public':
                    existing_public_user = True
                    method_acl[i] = dict(user="public", role="READER")
                    break
            if not existing_public_user:
                method_acl.append(dict(user="public", role="READER"))
        result = fapi.update_repository_method(namespace=namespace, method=method_name, wdl=wdl, synopsis='')
        if result.status_code == 201:
            result = result.json()
            if len(method_acl) > 0:
                fapi.update_repository_method_acl(namespace=result['namespace'], method=result['name'],
                    snapshot_id=result['snapshotId'], acl_updates=method_acl)
            print('import "https://api.firecloud.org/ga4gh/v1/tools/{}:{}/versions/{}/plain-WDL/descriptor"'.format(
                result['namespace'], result['name'], result['snapshotId']))
        else:
            print('Unable to add {}'.format(method_name))
            print(result.json())
