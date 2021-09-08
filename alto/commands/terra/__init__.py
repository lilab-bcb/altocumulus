import sys
import argparse
from . import run, add_method, remove_method, storage_estimate

def main(args):
    str2module = {'run': run, 'add_method': add_method, 'remove_method': remove_method, 'storage_estimate': storage_estimate}

    parser = argparse.ArgumentParser(description='Run a terra sub-command.')
    parser.add_argument('subcommand', help='The sub-command', choices=['run', 'add_method', 'remove_method', 'storage_estimate'])
    parser.add_argument('subcommand_args', help='The sub-command arguments', nargs=argparse.REMAINDER)
    my_args = parser.parse_args(args)

    subcmd = str2module[my_args.subcommand]
    sys.argv[0] = f'alto terra {my_args.subcommand}'
    subcmd.main(my_args.subcommand_args)
