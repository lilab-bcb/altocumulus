#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

from alto.commands import *


def main():
    command_list = [run, upload, add_method, download_method, remove_method, create_input_stub, sample_sheet,
                    parse_monitoring_log, workspace_storage_estimate]
    parser = argparse.ArgumentParser(description='Run an alto command')
    command_list_strings = list(map(lambda x: x.__name__[len('alto.commands.'):], command_list))
    parser.add_argument('command', help='The command', choices=command_list_strings)
    parser.add_argument('command_args', help='The command arguments', nargs=argparse.REMAINDER)
    my_args = parser.parse_args()
    command_name = my_args.command
    command_args = my_args.command_args
    cmd = command_list[command_list_strings.index(command_name)]
    sys.argv[0] = cmd.__file__
    cmd.main(command_args)


if __name__ == '__main__':
    main()
