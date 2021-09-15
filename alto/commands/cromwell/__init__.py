import sys, argparse
from . import run, check_status

def main(args):
    str2module = {'run': run, 'check_status': check_status}

    parser = argparse.ArgumentParser(description='Run a terra sub-command.')
    parser.add_argument('subcommand', help='The sub-command', choices=['run', 'check_status'])
    parser.add_argument('subcommand_args', help='The sub-command arguments', nargs=argparse.REMAINDER)
    my_args = parser.parse_args(args)

    subcmd = str2module[my_args.subcommand]
    sys.argv[0] = f'alto cromwell {my_args.subcommand}'
    subcmd.main(my_args.subcommand_args)
