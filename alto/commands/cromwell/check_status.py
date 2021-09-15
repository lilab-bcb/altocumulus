import argparse, requests


def get_status(server, port, job_id, no_ssl_verify):
    resp = requests.get(f"http://{server}:{port}/api/workflows/v1/{job_id}/status", verify=not no_ssl_verify)
    resp_dict = resp.json()

    if resp.status_code == 200:
        print(f"Job {resp_dict['id']} is in status {resp_dict['status']}.")
    else:
        print(resp_dict['message'])

def main(argv):
    parser = argparse.ArgumentParser(
        description="Check the current status for a workflow on a Cromwell server."
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
    parser.add_argument('--no-ssl-verify', dest='no_ssl_verify', action='store_true', default=False,
        help="Disable SSL verification for web requests. Not recommended for general usage, but can be useful for intra-networks which don't support SSL verification."
    )

    args = parser.parse_args(argv)

    get_status(args.server, args.port, args.job_id, args.no_ssl_verify)
