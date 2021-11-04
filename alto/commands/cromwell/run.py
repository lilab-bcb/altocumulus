import argparse, getpass, json, os, requests, time
from alto.utils.io_utils import read_wdl_inputs, upload_to_cloud_bucket
from alto.utils import parse_dockstore_workflow, get_dockstore_workflow

wf_label_filename = ".workflow_labels.json"
wf_option_filename = ".workflow_options.json"

label_filename = '.workflow_label.json'
wf_option_filename = '.workflow_options.json'


def parse_bucket_folder_url(bucket):
    assert '://' in bucket, "Bucket folder URL must start with 's3://' or 'gs://'."

    res = bucket.split('://')
    backend = 'aws'
    if res[0] == 'gs':
        backend = 'gcp'

    res2 = res[1].split('/')  # Remove the trailing slash if exists.
    bucket_id = res2[0]
    bucket_folder = '/'.join(res2[1:])

    return (backend, bucket_id, bucket_folder)


def wait_and_check(server, port, job_id, time_out, freq=60):
    url = f"http://{server}:{port}/api/workflows/v1/{job_id}/status"

    time_out_seconds = time_out * 3600
    seconds_passed = 0

    while seconds_passed < time_out_seconds:
        time.sleep(freq)
        seconds_passed += freq
        resp = requests.get(url)
        resp_dict = resp.json()
        if resp.status_code == 200:
            if resp_dict['status'] in ['Succeeded', 'Failed', 'Aborted', 'Aborting']:
                break
        else:
            print(resp_dict['message'])
            break

    if seconds_passed >= time_out_seconds:
        print(f"{time_out}-hour time-out is reached!")


def submit_to_cromwell(server, port, method_str, wf_input_path, out_json, bucket, no_cache, no_ssl_verify, time_out):
    is_url = False
    if method_str.startswith("https://") or method_str.startswith("http://"):
        is_url = True
    else:
        organization, collection, workflow, version = parse_dockstore_workflow(method_str)
        workflow_def = get_dockstore_workflow(organization, collection, workflow, version, ssl_verify=not no_ssl_verify)

    inputs = read_wdl_inputs(wf_input_path)

    # Upload input data to cloud bucket if needed.
    if out_json is not None:
        backend, bucket_id, bucket_folder = parse_bucket_folder_url(bucket)
        upload_to_cloud_bucket(inputs, backend, bucket_id, bucket_folder, out_json, False)

    files = {
        'workflowInputs': open(wf_input_path if out_json is None else out_json, 'rb'),
    }

    data = {
        'workflowUrl': workflow_def['url'] if not is_url else method_str,
    }

    # Set username to the label
    label_dict = {
        'creator': getpass.getuser()
    }
    with open(wf_label_filename, 'w') as fp:
        json.dump(label_dict, fp)
    files['labels'] = open(wf_label_filename, 'rb')

    if no_cache:
        wf_option_dict = {
            'write_to_cache': False,
            'read_from_cache': False,
        }
        with open(wf_option_filename, 'w') as fp:
            json.dump(wf_option_dict, fp)
        files['workflowOptions'] = open(wf_option_filename, 'rb')

    resp = requests.post(
        f"http://{server}:{port}/api/workflows/v1",
        files=files,
        data=data,
    )

    if os.path.exists(wf_label_filename):
        os.remove(wf_label_filename)
    if os.path.exists(wf_option_filename):
        os.remove(wf_option_filename)

    resp_dict = resp.json()

    if resp.status_code == 201:
        if time_out is None:
            print(f"Job {resp_dict['id']} is in status {resp_dict['status']}.")
        else:
            print(f"{{\"job_id\": \"{resp_dict['id']}\"}}")
    else:
        print(resp_dict['message'])

    if time_out is not None:
        wait_and_check(server, port, resp_dict['id'], time_out)


def main(argv):
    parser = argparse.ArgumentParser(description="Submit WDL jobs to a Cromwell server for execution. \
        Workflows should be from Dockstore. For Dockstore workflows, collection and name would be used as config namespace and name respectively. \
        If local files are detected, automatically upload files to the workspace Google Cloud bucket. \
        After a successful submission, a URL pointing to the job status would be printed out."
    )
    parser.add_argument('-s', '--server', dest='server', action='store', required=True,
        help="Server hostname or IP address."
    )
    parser.add_argument('-p', '--port', dest='port', action='store', default='8000',
        help="Port number for Cromwell service. The default port is 8000."
    )
    parser.add_argument('-m', '--method', dest='method_str', action='store', required=True,
        help="Workflow name from Dockstore, with name specified as organization:collection:name:version (e.g. broadinstitute:cumulus:cumulus:1.5.0). \
              The default version would be used if version is omitted. \
              Alternatively, a workflow URL in HTTPS or HTTP can be specified here."
    )
    parser.add_argument('-i', '--input', dest='input', action='store', required=True,
        help="Path to a local JSON file specifying workflow inputs."
    )
    parser.add_argument('-o', '--upload', dest='out_json', metavar='<updated_json>', action='store',
        help="Upload files/directories to the workspace cloud bucket and output updated input json (with local path replaced by cloud bucket urls) to <updated_json>.")
    parser.add_argument('-b', '--bucket', dest='bucket', action='store', metavar='[s3|gs]://<bucket-name>/<bucket-folder>',
        help="Cloud bucket folder for uploading local input data. Start with 's3://' if an AWS S3 bucket is used, 'gs://' for a Google bucket. \
        Must be specified when '-o' option is used."
    )
    parser.add_argument('--no-cache', dest='no_cache', action='store_true', help="Disable call-caching.")
    parser.add_argument('--no-ssl-verify', dest='no_ssl_verify', action='store_true', default=False,
        help="Disable SSL verification for web requests. Not recommended for general usage, but can be useful for intra-networks which don't support SSL verification."
    )
    parser.add_argument('--time-out', dest='time_out', type=float,
        help="Keep on checking the job's status until time_out (in hours) is reached. Notice that if this option is set, Altocumulus won't terminate until reaching time_out."
    )

    args = parser.parse_args(argv)

    submit_to_cromwell(args.server, args.port, args.method_str, args.input, args.out_json, args.bucket, args.no_cache, args.no_ssl_verify, args.time_out)
