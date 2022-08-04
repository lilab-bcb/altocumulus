import glob, os
from alto.utils import run_command
from typing import Optional

class sample_manager:
    def __init__(self):
        self.samples = set()

    def update_samples(self, sample_name: str):
        if sample_name in self.samples:
            raise ValueError(f"{sample_name} is duplicated!")
        self.samples.add(sample_name)

    def get_samples(self) -> List[str]:
        return list(self.samples)


def path_is_fastq(path: str) -> bool:
    """If path represents FASTQ files .
    """
    return len(glob.glob(f"{path}/*.fastq.gz")) > 0 or len(glob.glob(f"{path}/*/*.fastq.gz")) > 0


def transfer_fastq(
    source: str,
    dest: str,
    backend: str,
    samples: List[str],
    dry_run: bool,
    profile: Optional[str] = None,
    verbose: bool = True,
) -> None:
    if os.path.isdir(source):
        strato_cmd = ['strato', 'sync', '--backend', backend, '--ionice', '-m', '--quiet', source, dest]
    else:
        strato_cmd = ['strato', 'cp', '--backend', backend, '--ionice', '-m', '--quiet', source, os.path.dirname(dest) + '/']

    if profile is not None:
        strato_cmd.extend(['--profile', profile])

    run_command(strato_cmd, dry_run, suppress_stdout=not verbose)
