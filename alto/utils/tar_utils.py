import os
import glob
from typing import Set, List, Optional

from alto.utils import run_command


class sample_manager:
    def __init__(self):
        self.sample_map = set()

    def update_sample_map(self, sample_name: str):
        if sample_name in self.sample_map:
            raise ValueError(f"{sample_name} is duplicated!")
        self.sample_map.add(sample_name)

    def get_sample_map(self) -> Set[str]:
        return self.sample_map


def path_is_tar(path: str) -> bool:
    return len(glob.glob(f"{path}/*.tar")) > 0

def transfer_tar(
    source: str,
    dest: str,
    sample_map: Set[str],
    dry_run: bool,
    profile: Optional[str] = None,
    verbose: bool = True,
) -> None:
    for sample in sample_map:
        tar_list = glob.glob(f"{source}/*.tar")
        if len(tar_list) == 0:
            raise ValueError(f"'{sample}' doesn't have any corresponding TAR file in {source}!")
        elif len(tar_list) > 1:
            raise ValueError(f"{sample} has multiple TAR files in {source}!")

        tar_file = tar_list[0]
        strato_cmd = [
            "strato",
            "cp",
            "--ionice",
            "-m",
            "--quiet",
            tar_file,
            f"{dest}/",
        ]

        if profile is not None:
            strato_cmd.extend(["--profile", profile])

        run_command(strato_cmd, dry_run, suppress_stdout=not verbose)
