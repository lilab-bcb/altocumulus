import argparse, requests

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


def get_logs(server, port, top_job_id, cur_job_id):
    # For tasks directly called by current job
    resp_logs = requests.get(f"http://{server}:{port}/api/workflows/v1/{cur_job_id}/logs")
    logs_dict = resp_logs.json()
    if resp_logs.status_code != 200:
        raise Exception(logs_dict['message'])

    processed_tasks = set()
    if 'calls' in logs_dict.keys():
        for task_name, log_list in logs_dict['calls'].items():
            for log in log_list:
                get_remote_log_file(log['stderr'], top_job_id)
                get_remote_log_file(log['stdout'], top_job_id)
            processed_tasks.add(task_name)
    #else:
    #    print("No call log for this job.")

    resp_meta = requests.get(f"http://{server}:{port}/api/workflows/v1/{cur_job_id}/metadata")
    meta_dict = resp_meta.json()
    if resp_meta.status_code != 200:
        raise Exception(meta_dict['message'])

    # For tasks with subworkflow ID
    if 'calls' in meta_dict.keys():
        for task_name, task_list in meta_dict['calls'].items():
            if task_name not in processed_tasks:
                for task in task_list:
                    subworkflow_id = task['subWorkflowId']
                    get_logs(server, port, top_job_id, subworkflow_id)
    #else:
    #    print("No call log for subworkflows of this job.")


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

    # Create log folder even if there is no log file.
    run_command(['mkdir', '-p', args.job_id], dry_run=False)

    get_logs(args.server, args.port, args.job_id, args.job_id)
