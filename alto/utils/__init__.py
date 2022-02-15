import subprocess
from typing import List


prefix_float = "_&@&_"

def run_command(
    command: List[str],
    dry_run: bool,
    suppress_stdout: bool = False,
    suppress_stderr: bool = False,
) -> None:
    """ Print command and execute it (if dry_run == False).
    """
    cur_stdout = subprocess.DEVNULL if suppress_stdout else None
    cur_stderr = subprocess.DEVNULL if suppress_stderr else None

    if not suppress_stdout:
        print(' '.join(command))

    if not dry_run:
        subprocess.check_call(command, stdout=cur_stdout, stderr=cur_stderr)

from .io_utils import read_wdl_inputs, upload_to_cloud_bucket
from .dockstore_utils import parse_dockstore_workflow, get_dockstore_workflow
from .firecloud_utils import parse_firecloud_workflow, get_firecloud_workflow, parse_workspace, get_workspace_info, update_workflow_config_in_workspace, submit_a_job_to_terra
