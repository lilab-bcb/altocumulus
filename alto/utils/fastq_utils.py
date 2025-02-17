import glob
from typing import Set, List, Optional

from alto.utils import run_command


# Associated with one Flowcell path
class sample_manager:
    def __init__(self):
        self.sample_set = set()

    def update_sample_set(self, sample_name: str):
        if sample_name in self.sample_set:
            raise ValueError(f"{sample_name} is duplicated!")
        self.sample_set.add(sample_name)

    def get_sample_set(self) -> Set[str]:
        return self.sample_set


def path_is_fastq(path: str) -> bool:
    """If path represents FASTQ files ."""
    return len(glob.glob(f"{path}/*.fastq.gz")) > 0 or len(glob.glob(f"{path}/*/*.fastq.gz")) > 0


def transfer_fastq(
    source: str,
    dest: str,
    sample_set: Set[str],
    dry_run: bool,
    profile: Optional[str] = None,
    verbose: bool = True,
) -> None:
    for sample in sample_set:
        if len(glob.glob(f"{source}/{sample}_*.fastq.gz")) > 0:
            strato_cmd = [
                "strato",
                "cp",
                "--ionice",
                "-m",
                "--quiet",
                f"{source}/{sample}_*.fastq.gz",
                dest + "/",
            ]
        elif len(glob.glob(f"{source}/{sample}/{sample}_*.fastq.gz")) > 0:   # TODO: Check naming convention before upload
            strato_cmd = [
                "strato",
                "sync",
                "--ionice",
                "-m",
                "--quiet",
                f"{source}/{sample}",
                f"{dest}/{sample}",
            ]
        else:
            raise ValueError(f"'{sample}' doesn't have any corresponding FASTQ file!")

        if profile is not None:
            strato_cmd.extend(["--profile", profile])

        run_command(strato_cmd, dry_run, suppress_stdout=not verbose)
