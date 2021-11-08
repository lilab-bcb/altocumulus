import sys
import argparse
from alto.commands import terra, upload, parse_monitoring_log, cromwell

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

try:
    from importlib.metadata import version
except ImportError:  # < Python 3.8: Use backport module
    from importlib_metadata import version

def main():
    str2module = {'terra': terra, 'upload': upload, 'parse_monitoring_log': parse_monitoring_log, 'cromwell': cromwell}

    parser = argparse.ArgumentParser(description='Run an altocumulus command.')
    parser.add_argument('command', help='The command', choices=['terra', 'upload', 'parse_monitoring_log', 'cromwell'])
    parser.add_argument('command_args', help='The command arguments', nargs=argparse.REMAINDER)
    parser.add_argument('-v', '--version', action="version", version=version('altocumulus'))
    my_args = parser.parse_args()

    cmd = str2module[my_args.command]
    sys.argv[0] = f'alto {my_args.command}'
    cmd.main(my_args.command_args)


if __name__ == '__main__':
    main()
