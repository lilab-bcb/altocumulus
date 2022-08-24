import subprocess
from typing import List


prefix_float = "_&@&_"


def run_command(
    command: List[str],
    dry_run: bool,
    suppress_stdout: bool = False,
    suppress_stderr: bool = False,
) -> None:
    """Print command and execute it (if dry_run == False)."""
    cur_stdout = subprocess.DEVNULL if suppress_stdout else None
    cur_stderr = subprocess.DEVNULL if suppress_stderr else None

    if not suppress_stdout:
        print(" ".join(command))

    if not dry_run:
        subprocess.check_call(command, stdout=cur_stdout, stderr=cur_stderr)


from .dockstore_utils import get_dockstore_workflow, parse_dockstore_workflow  # noqa: F401, E402
from .firecloud_utils import (  # noqa: F401, E402
    get_firecloud_workflow,
    get_workspace_info,
    parse_firecloud_workflow,
    parse_workspace,
    submit_a_job_to_terra,
    update_workflow_config_in_workspace,
)
from .io_utils import read_wdl_inputs, upload_to_cloud_bucket  # noqa: F401, E402
