import os
from typing import List, Optional
from alto.utils import run_command

class lane_manager:
    def __init__(self):
        self.lanes = set()
        self.isall = False

    def update_lanes(self, lane_str: str):
        if lane_str == '*':
            self.isall = True
            self.lanes.clear()
        else:
            fields = lane_str.split('-')
            assert len(fields) <= 2
            if len(fields) == 1:
                self.lanes.add(int(lane_str))
            else:
                for i in range(int(fields[0]), int(fields[1]) + 1):
                    self.lanes.add(i)

    def get_lanes(self) -> List[str]:
        if self.isall or len(self.lanes) == 0:
            return ['*']
        res = []
        for lane in list(self.lanes):
            res.append(f'L{lane:03}')
        return res


def path_is_flowcell(path: str) -> bool:
    """If path represents BCL files of one sequencing flowcell.
    """
    return os.path.isdir(path) and os.path.exists(f'{path}/RunInfo.xml')


def transfer_flowcell(
    source: str,
    dest: str,
    backend: str,
    lanes: List[str],
    dry_run: bool,
    profile: Optional[str] = None,
    verbose: bool = True,
) -> None:
    """Transfer one flowcell (with selected lanes) to cloud

    Parameters
    ----------
    source: `str`
        Local path to the flowcell directory.
    dest: `str`
        Cloud address to copy the flowcell to. For example, it should be something like 'gs://my_bucket/flowecell' for copying to Google bucket.
    backend: `str`
        Cloud backend, choosing from 'gcp' and 'aws'.
    lanes: `List[str]`
        A list of lanes to copy to cloud.
    dry_run: `bool`
        If dry run, only print commands but do not execute.
    profile: `str`, optional, default: `None`
        If not None, use this profile for AWS backend.
    verbose: `bool`, optional, default: `True`
        Print messages to STDOUT.

    Returns
    -------
    None

    Examples
    --------
    >>> transfer_flowcell('flowcell', 'gs://my_bucket/flowcell', 'gcp', ['*'], False)
    """
    strato_cmd = ['strato', 'cp', '--backend', backend, '--ionice', '--quiet', f'{source}/RunInfo.xml', f'{dest}/RunInfo.xml']
    if profile is not None:
        strato_cmd.extend(['--profile', profile])
    run_command(strato_cmd, dry_run, suppress_stdout=not verbose)

    if not os.path.exists(f'{source}/RTAComplete.txt'):
        raise FileNotFoundError("Cannot find RTAComplete.txt. Please check if sequencing is completed!")
    strato_cmd = ['strato', 'cp', '--backend', backend, '--ionice', '--quiet', f'{source}/RTAComplete.txt', f'{dest}/RTAComplete.txt']
    if profile is not None:
        strato_cmd.extend(['--profile', profile])
    run_command(strato_cmd, dry_run, suppress_stdout=not verbose)

    if os.path.exists(f'{source}/runParameters.xml'):
        strato_cmd = ['strato', 'cp', '--backend', backend, '--ionice', '--quiet', f'{source}/runParameters.xml', f'{dest}/runParameters.xml']
    elif os.path.exists(f'{source}/RunParameters.xml'):
        strato_cmd = ['strato', 'cp', '--backend', backend, '--ionice', '--quiet', f'{source}/RunParameters.xml', f'{dest}/RunParameters.xml']
    else:
        raise FileNotFoundError("Cannot find either runParameters.xml or RunParameters.xml!")
    if profile is not None:
        strato_cmd.extend(['--profile', profile])
    run_command(strato_cmd, dry_run, suppress_stdout=not verbose)

    basecall_string = '{0}/Data/Intensities/BaseCalls'
    if len(lanes) == 1 and lanes[0] == '*':
        # find all lanes
        lanes = []
        with os.scandir(path = basecall_string.format(source)) as dirobj:
            for entry in dirobj:
                if entry.is_dir() and entry.name.startswith('L0'):
                    lanes.append(entry.name)
    # copy bcl files
    for lane in lanes:
        lane_string = basecall_string + '/{1}'
        strato_cmd = ['strato', 'sync', '--backend', backend, '--ionice', '-m', '--quiet', lane_string.format(source, lane), lane_string.format(dest, lane)]
        if profile is not None:
            strato_cmd.extend(['--profile', profile])
        run_command(strato_cmd, dry_run, suppress_stdout=not verbose)

    # copy locs files
    locs_string = '{0}/Data/Intensities/s.locs'
    if os.path.exists(locs_string.format(source)):
        strato_cmd = ['strato', 'cp', '--backend', backend, '--ionice', '--quiet', locs_string.format(source), locs_string.format(dest)]
        if profile is not None:
            strato_cmd.extend(['--profile', profile])
        run_command(strato_cmd, dry_run, suppress_stdout=not verbose)
    else:
        locs_string = '{0}/Data/Intensities/{1}'
        for lane in lanes:
            strato_cmd = ['strato', 'sync', '--backend', backend, '--ionice', '-m', '--quiet', locs_string.format(source, lane), locs_string.format(dest, lane)]
            if profile is not None:
                strato_cmd.extend(['--profile', profile])
            run_command(strato_cmd, dry_run, suppress_stdout=not verbose)
