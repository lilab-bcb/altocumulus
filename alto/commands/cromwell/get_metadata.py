import argparse, json, requests


def get_metadata(server, port, job_id):
    resp = requests.get(f"http://{server}:{port}/api/workflows/v1/{job_id}/metadata")
    resp_dict = resp.json()

    if resp.status_code == 200:
        with open(f"{job_id}.metadata.json", 'w') as fp:
            json.dump(resp_dict, fp, indent=4)
    else:
        print(resp_dict['message'])

def main(argv):
    parser = argparse.ArgumentParser(
        description="Get workflow and call-level metadata for a submitted job."
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

    get_metadata(args.server, args.port, args.job_id)
