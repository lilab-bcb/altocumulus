import argparse, getpass, json, requests
import pandas as pd


class bcolors:
    SUCCESS = '\033[92m'
    FAILED = '\033[91m'
    ENDC = '\033[0m'


def show_one_job(s, status):
    if status == 'Succeeded':
        print(f"{bcolors.SUCCESS}{s}{bcolors.ENDC}")
    elif status in ['Failed', 'Aborted']:
        print(f"{bcolors.FAILED}{s}{bcolors.ENDC}")
    else:
        print(s)


def show_jobs(df, top_level_only):
    if top_level_only:
        df = df.loc[df['parentWorkflowId'].isnull()].copy()

    if 'creator' not in df.columns:
        df['creator'] = ""

    # Print headers
    if top_level_only:
        print("Job ID\tCreator\tWorkflow\tStatus\tSubmitted\tStart\tEnd")
    else:
        print("Job ID\tTask ID\tCreator\tWorkflow\tStatus\tSubmitted\tStart\tEnd")

    for _, row in df.iterrows():
        if top_level_only:
            show_str = f"{row['id']}\t{row['creator']}\t{row['name']}\t{row['status']}\t{row['submission']}\t{row['start']}\t{row['end']}"
        else:
            show_str = f"{row['parentWorkflowId']}\t{row['id']}\t{row['creator']}\t{row['name']}\t{row['status']}\t{row['submission']}\t{row['start']}\t{row['end']}"
        show_one_job(show_str, row['status'])


def list_jobs(server, port, is_all, username, job_id, job_status):
    top_level_only = True if job_id is None else False
    query_data = dict()

    if not is_all:
        if job_id is not None:
            query_data['id'] = job_id
        else:
            query_data['additionalQueryResultFields'] = ['labels']
            query_data['label'] = [f"creator:{username}"]

        if job_status is not None:
            query_data['status'] = [job_status]

    resp = requests.get(
        f"http://{server}:{port}/api/workflows/v1/query",
        data=query_data,
    )
    resp_dict = resp.json()

    if resp.status_code == 200:
        df_jobs = pd.DataFrame.from_records(resp_dict['results'])
        show_jobs(df_jobs, top_level_only)
    else:
        print(resp_dict['message'])

def main(argv):
    parser = argparse.ArgumentParser(
        description="List jobs submitted to the server."
    )
    parser.add_argument('-s', '--server', dest='server', action='store', required=True,
        help="Server hostname or IP address."
    )
    parser.add_argument('-p', '--port', dest='port', action='store', default='8000',
        help="Port number for Cromwell service. The default port is 8000."
    )
    parser.add_argument('-a', '--all', dest='is_all', action='store_true', default=False,
        help="List all the jobs on the server."
    )
    parser.add_argument('-u', '--user', dest='user', action='store', default=getpass.getuser(),
        help="List jobs submitted by this user."
    )
    parser.add_argument('--id', dest='job_id', action='store',
        help="List all the subtasks of the specified job."
    )
    parser.add_argument('--only-succeeded', dest='only_succeeded', action='store_true', default=False,
        help="Only show jobs succeeded."
    )

    args = parser.parse_args(argv)

    job_status = None
    if args.only_succeeded:
        job_status = "Succeeded"


    list_jobs(args.server, args.port, args.is_all, args.user, args.job_id, job_status)
