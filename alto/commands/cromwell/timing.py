import argparse

import requests


def get_timing(server, port, job_id, output_file):
    resp = requests.get(f"http://{server}:{port}/api/workflows/v1/{job_id}/timing")

    if resp.status_code == 200:
        if output_file is None:
            output_file = job_id + ".html"
        with open(output_file, "wt") as out:
            out.write(resp.text)
    else:
        print("Invalid response from server")


def main(argv):
    parser = argparse.ArgumentParser(description="Get a visual diagram of a running workflow.")
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
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        action="store",
        help="HTML file to save timing diagram. Defaults to <job_id>.html",
    )

    args = parser.parse_args(argv)

    get_timing(args.server, args.port, args.job_id, args.output)
