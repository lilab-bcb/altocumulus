import argparse

from firecloud import api as fapi
from six.moves.urllib.parse import urljoin


def main(argv):
    parser = argparse.ArgumentParser(
        description='Export workspace storage cost estimates to TSV')
    parser.add_argument('--output', help='Output TSV path', required=True)
    parser.add_argument('--access', help='Workspace access levels', choices=['owner', 'reader', 'writer'],
        action='append')
    args = parser.parse_args(argv)
    workspaces = fapi.list_workspaces().json()
    access = args.access
    if access is None:
        access = []
    output = args.output
    access_filter = set()
    if 'reader' in access:
        access_filter.add('READER')
    if 'writer' in access:
        access_filter.add('WRITER')
    if 'owner' in access or len(access) == 0:
        access_filter.add('PROJECT_OWNER')
    with open(output, 'wt') as out:
        out.write('namespace\tname\testimate\n')
        for w in workspaces:
            if w['accessLevel'] in access_filter:
                namespace = w['workspace']['namespace']
                name = w['workspace']['name']

                headers = fapi._fiss_agent_header()
                root_url = fapi.fcconfig.root_url
                r = fapi.__SESSION.get(
                    urljoin(root_url, 'workspaces/{}/{}/storageCostEstimate'.format(namespace, name)),
                    headers=headers).json()
                estimate = r['estimate']
                out.write('{}\t{}\t{}\n'.format(namespace, name, estimate))


if __name__ == '__main__':
    main()
