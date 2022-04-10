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


def get_remote_log_file(cloud_uri, job_id, profile):
    backend, local_path = get_localize_path(cloud_uri, job_id)
    try:
        strato_cmd = ['strato', 'cp', '--backend', backend, '--quiet', cloud_uri, local_path]
        if profile is not None:
            strato_cmd.extend(['--profile', profile])
        run_command(strato_cmd, dry_run=False)
    except CalledProcessError:
        print(f"{cloud_uri} does not exist.")


def get_logs(server, port, top_job_id, cur_job_id, profile):
    # For tasks directly called by current job
    resp_logs = requests.get(f"http://{server}:{port}/api/workflows/v1/{cur_job_id}/logs")
    logs_dict = resp_logs.json()
    if resp_logs.status_code != 200:
        raise Exception(logs_dict['message'])

    processed_tasks = set()
    if 'calls' in logs_dict.keys():
        for task_name, log_list in logs_dict['calls'].items():
            for log in log_list:
                get_remote_log_file(log['stderr'], top_job_id, profile)
                get_remote_log_file(log['stdout'], top_job_id, profile)
            processed_tasks.add(task_name)

    resp_meta = requests.get(f"http://{server}:{port}/api/workflows/v1/{cur_job_id}/metadata")
    meta_dict = resp_meta.json()
    if resp_meta.status_code != 200:
        raise Exception(meta_dict['message'])

    # For tasks with subworkflow ID
    if 'calls' in meta_dict.keys():
        for task_name, task_list in meta_dict['calls'].items():
            if task_name not in processed_tasks:
                for task in task_list:
                    if 'subWorkflowId' in task.keys():
                        subworkflow_id = task['subWorkflowId']
                        get_logs(server, port, top_job_id, subworkflow_id, profile)


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
    parser.add_argument('--profile', dest='profile', type=str,
        help="AWS profile. Only works if dealing with AWS, and if not set, use the default profile."
    )

    args = parser.parse_args(argv)

    # Create log folder even if there is no log file.
    run_command(['mkdir', '-p', args.job_id], dry_run=False)

    get_logs(args.server, args.port, args.job_id, args.job_id, args.profile)
