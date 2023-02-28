import glob
from typing import Dict, List, Optional

from alto.utils import run_command


class sample_manager:
    def __init__(self):
        self.sample_map = dict()

    def update_sample_map(self, sample_name: str, file_list: List[str] = None):
        if sample_name in self.sample_map.keys():
            raise ValueError(f"{sample_name} is duplicated!")
        self.sample_map[sample_name] = file_list if file_list is not None else ["*"]

    def get_sample_map(self) -> Dict[str, List[str]]:
        return self.sample_map


def path_is_fastq(path: str) -> bool:
    """If path represents FASTQ files ."""
    return len(glob.glob(f"{path}/*.fastq.gz")) > 0 or len(glob.glob(f"{path}/*/*.fastq.gz")) > 0


def transfer_fastq(
    source: str,
    dest: str,
    sample_map: Dict[str, List[str]],
    dry_run: bool,
    profile: Optional[str] = None,
    verbose: bool = True,
) -> None:
    for sample, path_list in sample_map.items():
        if path_list == ["*"]:
            # Copy all FASTQ files
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
            elif len(glob.glob(f"{source}/{sample}/{sample}_*.fastq.gz")) > 0:
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
        else:
            # Copy specific files
            strato_cmd = [
                "strato",
                "cp",
                "--ionice",
                "-m",
                "--quiet",
            ]
            strato_cmd.extend(path_list)
            strato_cmd.append(dest + "/")

        if profile is not None:
            strato_cmd.extend(["--profile", profile])

        run_command(strato_cmd, dry_run, suppress_stdout=not verbose)
