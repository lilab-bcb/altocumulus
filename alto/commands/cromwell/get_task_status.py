import json
import argparse

import requests


class JobIDFetcher:
    def __init__(self, server, port):
        self.base_url = f"http://{server}:{port}/api/workflows/v1/"
        self.workflow_jobs = {}

    def get_metadata(self, job_id):
        resp = requests.get(f"{self.base_url}{job_id}/metadata")
        d = resp.json()
        return d["calls"]

    def get_workflow_status(self, job_id):
        metadata = self.get_metadata(job_id)
        for task_name in metadata.keys():
            if "jobId" in metadata[task_name][0]:
                jobID_status = self.get_jobID(task_name, metadata[task_name])
            else:
                jobID_status = self.subworkflow_IDs(metadata[task_name])
            self.workflow_jobs.update(jobID_status)
        return self.workflow_jobs

    def get_jobID(self, task_name, task_metadata):
        jobID_status = {}
        task_status = {}
        for job in task_metadata:
            jobID_status[job["jobId"]] = job["executionStatus"]
        task_status[task_name] = jobID_status
        return task_status

    def subworkflow_IDs(self, task_metadata):
        subworkflow_status = {}
        for sub_workflow in task_metadata:
            task_status_temp = self.get_workflow_status(sub_workflow["subWorkflowId"])
            for key, value in task_status_temp.items():
                if key not in subworkflow_status.keys():
                    subworkflow_status[key] = value
                else:
                    for key_temp, value_temp in value.items():
                        subworkflow_status[key][key_temp] = value_temp
        return subworkflow_status

    def get_task_status(self, job_id):  # returns a json file with the results
        self.get_workflow_status(job_id)
        with open(f"{job_id}.task_status.json", "w") as fp:
            json.dump(self.workflow_jobs, fp, indent=4)


def main(argv):
    parser = argparse.ArgumentParser(description="Get status of all WDL tasks of a job.")
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
        "--id",
        dest="job_id",
        action="store",
        required=True,
        help="Workflow ID returned in 'alto cromwell run' command.",
    )

    args = parser.parse_args(argv)

    fetcher = JobIDFetcher(args.server, args.port)
    fetcher.get_task_status(args.job_id)
