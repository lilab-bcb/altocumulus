import glob, os
from alto.utils import run_command
from typing import Optional

def folder_is_fastq(
    path: str,
    prefix: Optional[str] = None,
) -> Optional[str]:
    if (prefix is None) or (not os.path.isdir(path)):
        return None

    # Check folder permission.
    if not os.access(path, os.X_OK):
        raise PermissionError(f"Need execution access to folder '{path}'!")

    fa_list = glob.glob(f"{path}/{prefix}_*.fastq.gz")
    if len(fa_list) > 0:
        # Check fastq file permission.
        for f in fa_list:
            if not os.access(f, os.R_OK):
                raise PermissionError(f"Need read access to '{f}'!")

        return os.path.abspath(f"{path}/{prefix}_*.fastq.gz")
    elif os.path.isdir(f"{path}/{prefix}"):
        # Check subfolder permission.
        if not os.access(f"{path}/{prefix}", os.X_OK):
            raise PermissionError(f"Need execution access to folder '{path}/{prefix}'!")

        fa_list = glob.glob(f"{path}/{prefix}/{prefix}_*.fastq.gz")
        if len(fa_list) > 0:
            # Check fastq file permission.
            for f in fa_list:
                if not os.access(f, os.R_OK):
                    raise PermissionError(f"Need read access to '{f}'!")

            return os.path.abspath(f"{path}/{prefix}/{prefix}_*.fastq.gz")
        else:
            return None
    else:
        return None


def transfer_fastq(
    source: str,
    dest: str,
    backend: str,
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
