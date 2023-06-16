import sys
import argparse

from . import abort, check_status, get_logs, get_metadata, get_task_status, list_jobs, run, timing


def main(args):
    str2module = {
        "run": run,
        "check_status": check_status,
        "abort": abort,
        "get_metadata": get_metadata,
        "get_task_status": get_task_status,
        "get_logs": get_logs,
        "list_jobs": list_jobs,
        "timing": timing,
    }

    parser = argparse.ArgumentParser(description="Run a terra sub-command.")
    parser.add_argument(
        "subcommand",
        help="The sub-command",
        choices=[
            "run",
            "check_status",
            "abort",
            "get_metadata",
            "get_task_status",
            "get_logs",
            "list_jobs",
            "timing",
        ],
    )
    parser.add_argument(
        "subcommand_args", help="The sub-command arguments", nargs=argparse.REMAINDER
    )
    my_args = parser.parse_args(args)

    subcmd = str2module[my_args.subcommand]
    sys.argv[0] = f"alto cromwell {my_args.subcommand}"
    subcmd.main(my_args.subcommand_args)
