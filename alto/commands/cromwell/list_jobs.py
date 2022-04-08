import argparse
import getpass
import requests
import pandas as pd
from datetime import datetime
from dateutil import parser
import time
from typing import List, Optional


def datetime_from_utc_to_local(utc_datetime: str) -> str:
    if not utc_datetime:
        return ""
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(
        now_timestamp
    )
    return (parser.parse(utc_datetime) + offset).strftime("%d %b %Y, %H:%M:%S")


class bcolors:
    SUCCESS = "\033[92m"
    FAILED = "\033[91m"
    ENDC = "\033[0m"


def show_one_job(s: str, status: str):
    if status == "Succeeded":
        print(f"{bcolors.SUCCESS}{s}{bcolors.ENDC}")
    elif status in ["Failed", "Aborted"]:
        print(f"{bcolors.FAILED}{s}{bcolors.ENDC}")
    else:
        print(s)


def show_jobs(
    df: pd.DataFrame,
    num_shown: Optional[int],
) -> None:
    if "creator" not in df.columns:
        df["creator"] = ""
    print(
        "{:<38} {:<16} {:<24} {:<13} {:<28} {:<28} {:<28}".format(
            "Job ID", "Creator", "Workflow", "Status", "Submitted", "Start", "End"
        )
    )

    if num_shown is not None:
        df = df[0:num_shown]

    for _, row in df.iterrows():
        show_str = "{:<38} {:<16} {:<24} {:<13} {:<28} {:<28} {:<28}".format(
            row["id"],
            row["creator"],
            row["name"] if row.get("name") is not None else "",
            row["status"],
            row["submission"],
            row["start"],
            row["end"],
        )
        show_one_job(show_str, row["status"])


def list_jobs(
    server: str,
    port: int,
    is_all: bool,
    username: str,
    job_statuses: List[str],
    num_shown: Optional[int],
) -> None:
    query_data = []
    query_data.append({"additionalQueryResultFields": "labels"})
    if not is_all:
        query_data.append({"additionalQueryResultFields": "labels"})
        query_data.append({"label": f"creator:{username}"})

    for job_status in job_statuses:
        query_data.append({"status": job_status})
    resp = requests.post(
        f"http://{server}:{port}/api/workflows/v1/query",
        json=query_data,
    )
    resp_dict = resp.json()
    for res in resp_dict["results"]:
        if "labels" in res:
            res["creator"] = res["labels"].get("creator", "")
            del res["labels"]
        else:
            res["creator"] = ""
        res["submission"] = datetime_from_utc_to_local(res.get("submission", ""))
        res["start"] = datetime_from_utc_to_local(res.get("start", ""))
        res["end"] = datetime_from_utc_to_local(res.get("end", ""))
    if resp.status_code == 200:
        df_jobs = pd.DataFrame.from_records(resp_dict["results"])
        show_jobs(df_jobs, num_shown=num_shown)
    else:
        print(resp_dict["message"])


def main(argv):
    parser = argparse.ArgumentParser(description="List jobs submitted to the server.")
    parser.add_argument(
        "-s",
        "--server",
        dest="server",
        action="store",
        required=True,
        help="Server hostname or IP address.",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        dest="port",
        action="store",
        default=8000,
        help="Port number for Cromwell service. The default port is 8000.",
    )
    parser.add_argument(
        "-a",
        "--all",
        dest="is_all",
        action="store_true",
        default=False,
        help="List all the jobs on the server.",
    )
    parser.add_argument(
        "-u",
        "--user",
        dest="user",
        action="store",
        default=getpass.getuser(),
        help="List jobs submitted by this user.",
    )
    parser.add_argument(
        "--only-succeeded",
        dest="only_succeeded",
        action="store_true",
        default=False,
        help="Only show jobs succeeded.",
    )
    parser.add_argument(
        "--only-running",
        dest="only_running",
        action="store_true",
        default=False,
        help="Only show jobs that are running.",
    )
    parser.add_argument(
        "--only-failed",
        dest="only_failed",
        action="store_true",
        default=False,
        help="Only show jobs that have failed or have aborted.",
    )
    parser.add_argument(
        "-n",
        type=int,
        dest="num_shown",
        action="store",
        default=None,
        help="Only show the <num_shown> most recent jobs.",
    )

    args = parser.parse_args(argv)

    job_statuses = []
    if args.only_succeeded:
        job_statuses.append("Succeeded")
    elif args.only_failed:
        job_statuses.append("Failed")
        job_statuses.append("Aborted")
    elif args.only_running:
        job_statuses.append("Running")

    list_jobs(args.server, args.port, args.is_all, args.user, job_statuses, args.num_shown)
