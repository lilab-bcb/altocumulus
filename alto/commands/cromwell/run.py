import os
import json
import time
import getpass
import zipfile
import argparse
import tempfile

import requests

from alto.utils import get_dockstore_workflow, parse_dockstore_workflow
from alto.utils.io_utils import get_workflow_imports, read_wdl_inputs, upload_to_cloud_bucket


def parse_bucket_folder_url(bucket):
    assert "://" in bucket, "Bucket folder URL must start with 's3://' or 'gs://'."

    res = bucket.split("://")
    backend = "aws"
    if res[0] == "gs":
        backend = "gcp"

    res2 = res[1].split("/")  # Remove the trailing slash if exists.
    bucket_id = res2[0]
    bucket_folder = "/".join(res2[1:])

    return (backend, bucket_id, bucket_folder)


def wait_and_check(server, port, job_id, time_out, freq=60):
    url = f"http://{server}:{port}/api/workflows/v1/{job_id}/status"

    time_out_seconds = time_out * 3600
    seconds_passed = 0
    status = ""

    while seconds_passed < time_out_seconds:
        time.sleep(freq)
        seconds_passed += freq
        resp = requests.get(url)
        resp_dict = resp.json()
        if resp.status_code == 200:
            if resp_dict["status"] in ["Succeeded", "Failed", "Aborted"]:
                status = resp_dict["status"]
                break
        else:
            print(resp_dict["message"])
            break

    if seconds_passed >= time_out_seconds:
        print(f"{time_out}-hour time-out is reached!")

    return status


def parse_workflow_str(method_str, no_ssl_verify):
    is_url = False
    workflow_str = method_str

    if "://" in method_str:
        assert method_str.split("://")[0] in [
            "http",
            "https",
        ], "Only http or https URL is acceptable!"
        is_url = True
    elif ":" in method_str:
        organization, collection, workflow, version = parse_dockstore_workflow(method_str)
        workflow_def = get_dockstore_workflow(
            organization, collection, workflow, version, ssl_verify=not no_ssl_verify
        )
        is_url = True
        workflow_str = workflow_def["url"]

    return workflow_str, is_url


def check_zip(dependency_str):
    is_dependency = False
    if os.path.isfile(dependency_str) and zipfile.is_zipfile(dependency_str):
        is_dependency = True
    return is_dependency


def submit_to_cromwell(
    server,
    port,
    method_str,
    wf_input_path,
    out_json,
    bucket,
    no_cache,
    no_ssl_verify,
    time_out,
    profile,
    dependency_str,
):
    files = dict()
    data = dict()
    label_dict = dict()

    # Process job's workflow WDL
    workflow_str, is_url = parse_workflow_str(method_str, no_ssl_verify)
    if is_url:
        data["workflowUrl"] = workflow_str
    else:
        files["workflowSource"] = open(workflow_str, "rb")

    tmp_zip_file = None
    # Process workflow WDL's dependency
    if dependency_str is not None:
        if check_zip(dependency_str):
            files["workflowDependencies"] = open(dependency_str, "rb")
        else:
            raise Exception("Dependency zip file does not exist or is not given in zip format.")
    elif not is_url:
        deps = set()

        def add_deps(path):
            workflow_dir = os.path.dirname(path)
            for d in get_workflow_imports(path):
                imported_path = os.path.abspath(os.path.join(workflow_dir, d))
                if os.path.exists(imported_path):
                    deps.add(imported_path)
                    add_deps(imported_path)

        # add imports recursively
        if os.path.exists(workflow_str):
            add_deps(workflow_str)
            if len(deps) > 0:
                tmp_zip_file = tempfile.mkstemp(prefix="alto", suffix=".zip")[1]
                with zipfile.ZipFile(tmp_zip_file, "w", zipfile.ZIP_DEFLATED) as out:
                    for dep in deps:
                        out.write(dep, arcname=os.path.basename(dep))
                files["workflowDependencies"] = open(tmp_zip_file, "rb")

    # Process job's workflow inputs
    inputs = read_wdl_inputs(wf_input_path)

    # Upload input data to cloud bucket if needed.
    if out_json is not None:
        backend, bucket_id, bucket_folder = parse_bucket_folder_url(bucket)
        upload_to_cloud_bucket(
            inputs=inputs,
            backend=backend,
            bucket=bucket_id,
            bucket_folder=bucket_folder,
            out_json=out_json,
            dry_run=False,
            verbose=True if time_out is None else False,
            profile=profile,
        )

    files["workflowInputs"] = open(wf_input_path if out_json is None else out_json, "rb")

    # Add username to the job labels
    label_dict["creator"] = getpass.getuser()

    wf_label_filename = tempfile.mkstemp(prefix="alto_wf_label_", suffix=".json")[1]
    with open(wf_label_filename, "w") as fp:
        json.dump(label_dict, fp)
    files["labels"] = open(wf_label_filename, "rb")

    wf_option_filename = None
    # Process job's workflow options.
    if no_cache:
        wf_option_dict = {
            "read_from_cache": False,
        }
        wf_option_filename = tempfile.mkstemp(prefix="alto_wf_option_", suffix=".json")[1]
        with open(wf_option_filename, "w") as fp:
            json.dump(wf_option_dict, fp)
        files["workflowOptions"] = open(wf_option_filename, "rb")

    # Send HTTP request to Cromwell server
    try:
        resp = requests.post(
            f"http://{server}:{port}/api/workflows/v1",
            files=files,
            data=data,
        )
    finally:
        # Remove intermediate input files
        if tmp_zip_file is not None and os.path.exists(tmp_zip_file):
            os.remove(tmp_zip_file)
        if os.path.exists(wf_label_filename):
            os.remove(wf_label_filename)
        if wf_option_filename is not None and os.path.exists(wf_option_filename):
            os.remove(wf_option_filename)

    # Process response
    resp_dict = resp.json()
    successful_submission = resp.status_code == 201
    if successful_submission:
        if time_out is None:  # Only print this message when --time-out is not set.
            print(f"Job {resp_dict['id']} is submitted.")
    else:
        import sys

        print(resp_dict["message"])
        sys.exit(-1)

    # Wait for job to complete
    if time_out is not None:
        status = wait_and_check(server, port, resp_dict["id"], time_out)
        print(f"{{\"job_id\": \"{resp_dict['id']}\", \"status\": \"{status}\"}}")

    if successful_submission:
        return resp_dict["id"]


def main(argv):
    parser = argparse.ArgumentParser(
        description="Submit WDL jobs to a Cromwell server for execution. \
        Workflows should be from Dockstore. For Dockstore workflows, collection and name would be used as config namespace and name respectively. \
        If local files are detected, automatically upload files to the workspace Google Cloud bucket. \
        After a successful submission, a URL pointing to the job status would be printed out."
    )
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
        dest="port",
        action="store",
        default="8000",
        help="Port number for Cromwell service. The default port is 8000.",
    )
    parser.add_argument(
        "-m",
        "--method",
        dest="method_str",
        action="store",
        required=True,
        help='Three forms of workflow WDL file is accepted: \
              (1) Workflow name from Dockstore, with name specified as "organization:collection:name:version" (e.g. "broadinstitute:cumulus:cumulus:1.5.0"). If \'version\' part is not specified, the default version defined on Dockstore would be used. \
              (2) An HTTP or HTTPS URL of a WDL file. \
              (3) A local path to a WDL file.',
    )
    parser.add_argument(
        "-d",
        "--dependency",
        dest="dependency_str",
        action="store",
        help="ZIP file containing workflow source files that are used \
              to resolve local imports. This zip bundle will be unpacked \
              in a sandbox accessible to the workflow.",
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="input",
        action="store",
        required=True,
        help="Path to a local JSON file specifying workflow inputs.",
    )
    parser.add_argument(
        "-o",
        "--upload",
        dest="out_json",
        metavar="<updated_json>",
        action="store",
        help="Upload files/directories to the workspace cloud bucket and output updated input json (with local path replaced by cloud bucket urls) to <updated_json>.",
    )
    parser.add_argument(
        "-b",
        "--bucket",
        dest="bucket",
        action="store",
        metavar="[s3|gs]://<bucket-name>/<bucket-folder>",
        help="Cloud bucket folder for uploading local input data. Start with 's3://' if an AWS S3 bucket is used, 'gs://' for a Google bucket. \
        Must be specified when '-o' option is used.",
    )
    parser.add_argument(
        "--no-cache",
        dest="no_cache",
        action="store_true",
        help="Disable call-caching, i.e. do not read from cache.",
    )
    parser.add_argument(
        "--no-ssl-verify",
        dest="no_ssl_verify",
        action="store_true",
        default=False,
        help="Disable SSL verification for web requests. Not recommended for general usage, but can be useful for intra-networks which don't support SSL verification.",
    )
    parser.add_argument(
        "--time-out",
        dest="time_out",
        type=float,
        help="Keep on checking the job's status until time_out (in hours) is reached. Notice that if this option is set, Altocumulus won't terminate until reaching time_out.",
    )
    parser.add_argument(
        "--profile",
        dest="profile",
        type=str,
        help="AWS profile. Only works if dealing with AWS, and if not set, use the default profile.",
    )
    parser.add_argument(
        "--job-id",
        dest="job_id",
        type=str,
        help="Write the job id to the specified output file",
    )

    args = parser.parse_args(argv)

    job_id = submit_to_cromwell(
        args.server,
        args.port,
        args.method_str,
        args.input,
        args.out_json,
        args.bucket,
        args.no_cache,
        args.no_ssl_verify,
        args.time_out,
        args.profile,
        args.dependency_str,
    )
    if args.job_id is not None:
        with open(args.job_id, "wt") as f:
            if job_id is not None:
                f.write(str(job_id))
            f.write("\n")
