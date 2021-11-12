import argparse, json, requests

from alto.utils import run_command
from subprocess import CalledProcessError


def get_localize_path(cloud_uri, job_id):
    uri_list = cloud_uri.split('://')
    backend = 'local'
    if len(uri_list) > 1:
        backend = 'aws' if uri_list[0] == 's3' else 'gcp'

    local_path = cloud_uri[cloud_uri.find(job_id):]

    return backend, local_path


def get_remote_log_file(cloud_uri, job_id):
    backend, local_path = get_localize_path(cloud_uri, job_id)
    try:
        run_command(['strato', 'cp', '--backend', backend, cloud_uri, local_path], dry_run=False)
    except CalledProcessError:
        print(f"{cloud_uri} does not exist.")

def get_logs_per_task(server, port, job_id, meta_dict):
    # For tasks with no subworkflow ID
    resp_top = requests.get(f"http://{server}:{port}/api/workflows/v1/{job_id}/logs")
    resp_top_dict = resp_top.json()

    processed_tasks = set()
    if 'calls' in resp_top_dict.keys():
        for task_name, log_list in resp_top_dict['calls'].items():
            for log in log_list:
                get_remote_log_file(log['stderr'], job_id)
                get_remote_log_file(log['stdout'], job_id)
            processed_tasks.add(task_name)
    else:
        print("No call logs for this job.")

    # For tasks with subworkflow ID
    if 'calls' in meta_dict.keys():
        for task_name, task_list in meta_dict['calls'].items():
            if task_name not in processed_tasks:
                for task in task_list:
                    subworkflow_id = task['subWorkflowId']
                    resp_task = requests.get(f"http://{server}:{port}/api/workflows/v1/{subworkflow_id}/logs")
                    resp_task_dict = resp_task.json()
                    for task_name, log_list in resp_task_dict['calls'].items():
                        for log in log_list:
                            get_remote_log_file(log['stderr'], job_id)
                            get_remote_log_file(log['stdout'], job_id)
    else:
        print("No call logs for subworkflows of this job.")



def get_logs(server, port, job_id):
    resp_meta = requests.get(f"http://{server}:{port}/api/workflows/v1/{job_id}/metadata")
    meta_dict = resp_meta.json()

    if resp_meta.status_code == 200:
        get_logs_per_task(server, port, job_id, meta_dict)
    else:
        print(meta_dict['message'])

def main(argv):
    parser = argparse.ArgumentParser(
        description="Get the logs for a submitted job."
    )
    parser.add_argument('-s', '--server', dest='server', action='store', required=True,
        help="Server hostname or IP address."
    )
    parser.add_argument('-p', '--port', dest='port', action='store', default='8000',
        help="Port number for Cromwell service. The default port is 8000."
    )
    parser.add_argument('--id', dest='job_id', action='store', required=True,
        help="Workflow ID returned in 'alto cromwell run' command."
    )

    args = parser.parse_args(argv)

    get_logs(args.server, args.port, args.job_id)
