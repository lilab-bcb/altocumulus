import os
import re
import json
import tempfile
from collections import namedtuple
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import numpy as np
import pandas as pd

from alto.utils import prefix_float, run_command

from .bcl_utils import lane_manager, path_is_bcl, transfer_flowcell
from .fastq_utils import path_is_fastq, sample_manager, transfer_fastq


FlowcellType = namedtuple("FlowcellType", ["type", "manager"])

import_pattern = '^import "(.+)"'


def _get_scheme(path):
    scheme = urlparse(path).scheme
    return (
        "file" if len(scheme) <= 1 else scheme
    )  # for file paths: /foo/bar/test.h5ad or C:/foo/bar/test.h5ad


def get_workflow_imports(path):
    workflow_imports = []
    with open(path, "rt") as f:
        for line in f:
            line = line.strip()
            result = re.match(import_pattern, line)
            if result:
                workflow_imports.append(result.group(1))
    return workflow_imports


def read_wdl_inputs(input_json: str) -> dict:
    """Load inputs from either a JSON file or a JSON string.

    Parameters
    ----------
    input_json: `str`
        input_json can represents either the path of a JSON file or a JSON string. Altocumulus will automatically detect the right choice (between path and string)

    Returns
    -------
    `dict` object.
        A dictionary object with loaded WDL inputs.

    Examples
    --------
    >>> wdl_inputs = read_wdl_inputs('inputs.json')
    """
    float_parser = lambda x: prefix_float + x

    assert isinstance(input_json, str)

    wdl_inputs = None
    if os.path.exists(input_json):
        with open(input_json, "r") as f:
            wdl_inputs = json.loads(f.read(), parse_float=float_parser)
    else:
        wdl_inputs = json.loads(input_json, parse_float=float_parser)

    return wdl_inputs


class cloud_url_factory:  # class to make sure all cloud urls are unique
    def __init__(
        self, backend, bucket
    ):  # here bucket should also include bucket folder information
        assert backend in {"gcp", "aws"}
        self.scheme = "gs" if backend == "gcp" else "s3"
        self.bucket = bucket
        self.unique_urls = set()

    def get_unique_url(self, input_path: str):
        counter = 1
        uniq_url = f"{self.scheme}://{self.bucket}/{os.path.basename(input_path)}"
        root, ext = os.path.splitext(uniq_url)
        while uniq_url in self.unique_urls:
            counter += 1
            uniq_url = f"{root}_{counter}{ext}"
        self.unique_urls.add(uniq_url)

        return uniq_url


def transfer_data(
    source: str,
    dest: str,
    dry_run: bool,
    flowcells: Dict[str, FlowcellType] = None,
    profile: Optional[str] = None,
    verbose: bool = True,
) -> None:
    """Transfer source to dest (cloud destination).

    backend, choosing from gcp and aws. flowcells is a global flowcell manangement object.
    """
    if verbose:
        print(f'{"Dry run: " if dry_run else ""}Uploading {source} to {dest}.')

    if flowcells is not None and source in flowcells:
        flowcell = flowcells[source]
        if flowcell.type == "bcl":
            transfer_flowcell(
                source=source,
                dest=dest,
                lanes=flowcell.manager.get_lanes(),
                dry_run=dry_run,
                profile=profile,
                verbose=verbose,
            )
        else:
            assert flowcell.type == "fastq"
            transfer_fastq(
                source=source,
                dest=dest,
                sample_map=flowcell.manager.get_sample_map(),
                dry_run=dry_run,
                profile=profile,
                verbose=verbose,
            )
    else:
        if os.path.isdir(source):
            strato_cmd = [
                "strato",
                "sync",
                "--ionice",
                "-m",
                "--quiet",
                source,
                dest,
            ]
        else:
            strato_cmd = ["strato", "cp", "--ionice", "--quiet", source, dest]

        if profile is not None:
            strato_cmd.extend(["--profile", profile])
        run_command(strato_cmd, dry_run, suppress_stdout=not verbose)


def transfer_sample_sheet(
    input_file: str,
    input_ext: str,
    input_file_to_output_url: dict,
    url_gen: cloud_url_factory,
    dry_run: bool,
    profile: Optional[str] = None,
    nrows: Optional[int] = 10005,
    verbose: bool = True,
) -> Tuple[str, bool]:
    """Check sample sheet and upload files inside it.
    input_file: sample sheet
    input_ext: input file extension, either '.xlsx', '.tsv', or '.csv'
    input_file_to_output_url: global dictionary maps local files to cloud urls
    url_gen: cloud url factory to make sure no duplicated cloud urls
    dry_run: if dry run
    profile: if not None, use for AWS backend
    nrows: load at most nrows, if loaded rows == nrows, skip; default: 10005
    verbose: if print info

    Returns: path to updated input file (if changed) and if sample sheet is changed
    """
    is_changed = False

    # Terminate if no access to sample sheet.
    if not os.access(input_file, os.R_OK):
        raise PermissionError(f"Need read access to '{input_file}'!")

    if input_ext == ".csv":
        df = pd.read_csv(input_file, sep=",", header=None, index_col=False, nrows=nrows)
    elif input_ext == ".tsv":
        df = pd.read_csv(input_file, sep="\t", header=None, index_col=False, nrows=nrows)
    else:
        assert input_ext == ".xlsx"
        df = pd.read_excel(input_file, header=None, index_col=False, nrows=nrows)

    if df.shape[0] >= nrows:
        return (
            input_file,
            is_changed,
        )  # if can load nrows, the file is too large to be a sample sheet

    df = df.applymap(lambda s: s.strip() if isinstance(s, str) else s)  # only strip for strings

    flowcells = {}
    col_names = np.char.array(df.iloc[0, :], unicode=True).lower()

    # Upload BCL folder or FASTQ files if needed.
    if ("flowcell" in col_names) or ("location" in col_names):
        flowcell_keyword = "flowcell" if "flowcell" in col_names else "location"
        df.columns = col_names

        sample_keyword = None
        if "library" in col_names:
            sample_keyword = "library"
        elif "sample" in col_names:
            sample_keyword = "sample"
        else:
            raise ValueError("Cannot detect either Library or Sample column in the sample sheet!")

        for _, row in df[1:].iterrows():
            if isinstance(row[flowcell_keyword], str):
                path = row[flowcell_keyword]

                if path.startswith("gs://") or path.startswith("s3://"):
                    continue

                path = os.path.abspath(path)
                if not os.path.exists(path):
                    raise ValueError(f"{path} does not exist!")
                if not os.path.isdir(path):
                    break  # For file type Location values
                elif not os.access(path, os.X_OK):
                    raise PermissionError(f"Need execution access to folder '{path}'!")
            else:
                raise ValueError(f"{row[flowcell_keyword]} is not in string type!")

            flowcell = None
            if path in flowcells:
                flowcell = flowcells[path]
            else:
                if path_is_bcl(path):
                    flowcell = FlowcellType(type="bcl", manager=lane_manager())
                elif path_is_fastq(path):
                    flowcell = FlowcellType(type="fastq", manager=sample_manager())
                else:
                    raise ValueError(f"{path} is neither a BCL folder nor a FASTQ folder!")
                flowcells[path] = flowcell

            if flowcell.type == "bcl":
                flowcell.manager.update_lanes(row["lane"] if "lane" in row else "*")
            else:
                flowcell.manager.update_sample_map(row[sample_keyword])

    for idxr, row in df[1:].iterrows() if input_ext != ".tsv" else df.iterrows():
        for idxc, value in row.items():
            if isinstance(value, str) and os.path.exists(value):
                source = os.path.abspath(value)
                sub_url = input_file_to_output_url.get(source, None)

                if sub_url is None:
                    sub_url = url_gen.get_unique_url(source)
                    transfer_data(
                        source=source,
                        dest=sub_url,
                        dry_run=dry_run,
                        flowcells=flowcells,
                        profile=profile,
                        verbose=verbose,
                    )
                    input_file_to_output_url[source] = sub_url

                df.loc[idxr, idxc] = sub_url
                is_changed = True

    if is_changed:
        orig_file = input_file
        input_file = tempfile.mkstemp()[1]
        if verbose:
            print(f"Rewriting file {orig_file} to {input_file}.")
        out_sep = "," if orig_file.endswith(".csv") else "\t"
        df.to_csv(input_file, sep=out_sep, index=False, header=False)

    return input_file, is_changed


search_inside_file_whitelist = set([".xlsx", ".tsv", ".csv"])


def upload_to_cloud_bucket(
    inputs: Dict[str, str],
    backend: str,
    bucket: str,
    bucket_folder: str,
    out_json: str,
    dry_run: bool,
    profile: Optional[str] = None,
    nrows: Optional[int] = 10005,
    verbose: bool = True,
) -> None:
    """Check and upload local files to the cloud bucket.

    Parameters
    ----------
    inputs: `Dict[str, str]`
        WDL inputs loaded from a JSON file.
    backend: `str`
        Cloud backend, choosing from 'gcp' and 'aws'.
    bucket:
        Cloud bucket name. Note scheme should not be included (e.g. gs:// or s3://).
    bucket_folder: `str`
        Path under the bucket for where the uploaded file should be stored.
    out_json: `str`
        Path for the JSON file storing updated inputs.
    dry_run: `bool`
        If dry run, only print commands but do not execute.
    profile: `str`, default: ``None``
        For AWS backend only, it's used for specifying a non-default AWS profile.
    nrows: `int`, default: 10005
        For scanning sample sheets, if file has >= nrows lines, skip.
    verbose: `bool`, default: ``True``
        If print out the underlying upload commands on screen.

    Returns
    -------
    None

    Examples
    --------
    >>> upload_to_cloud_bucket(inputs, 'gcp', 'my_bucket', 'input_files', 'updated_inputs.json')
    """
    if bucket_folder is not None:
        bucket += f"/{bucket_folder.strip('/')}"

    url_gen = cloud_url_factory(backend, bucket)
    input_file_to_output_url = {}

    for k, v in inputs.items():
        input_path = v
        if isinstance(input_path, str) and os.path.exists(input_path):
            input_path = os.path.abspath(input_path)
            if input_path in input_file_to_output_url:  # if this file has been processed, skip
                inputs[k] = input_file_to_output_url[input_path]
                continue

            input_url = url_gen.get_unique_url(input_path)
            input_file_to_output_url[input_path] = input_url

            is_changed = False
            input_path_extension = os.path.splitext(input_path)[1].lower()

            if input_path_extension in search_inside_file_whitelist:
                # look inside input file to see if there are file paths within
                input_path, is_changed = transfer_sample_sheet(
                    input_file=input_path,
                    input_ext=input_path_extension,
                    input_file_to_output_url=input_file_to_output_url,
                    url_gen=url_gen,
                    dry_run=dry_run,
                    profile=profile,
                    nrows=nrows,
                    verbose=verbose,
                )

            transfer_data(
                source=input_path,
                dest=input_url,
                dry_run=dry_run,
                profile=profile,
                verbose=verbose,
            )

            inputs[k] = input_url
            if is_changed:  # delete temporary file after uploading
                os.remove(input_path)

    if out_json is not None:
        with open(out_json, "w") as fout:
            res_str = json.dumps(inputs, indent=4)
            fout.write(re.sub(f'"{prefix_float}(.+)"', r"\1", res_str))
