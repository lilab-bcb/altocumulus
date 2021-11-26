import os
import json
import numpy as np
import pandas as pd
import tempfile
from collections import defaultdict
from typing import Tuple, Dict

from alto.utils import run_command
from .bcl_utils import lane_manager, path_is_flowcell, transfer_flowcell



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
    float_parser = lambda x: (float(x), x)

    assert isinstance(input_json, str)

    wdl_inputs = None
    if os.path.exists(input_json):
        with open(input_json, 'r') as f:
            wdl_inputs = json.loads(f.read(), parse_float=float_parser)
    else:
        wdl_inputs = json.loads(input_json, parse_float=float_parser)

    return wdl_inputs


class cloud_url_factory: # class to make sure all cloud urls are unique
    def __init__(self, backend, bucket): # here bucket should also include bucket folder information
        assert backend in {'gcp', 'aws'}
        self.scheme = 'gs' if backend == 'gcp' else 's3'
        self.bucket = bucket
        self.unique_urls = set()

    def get_unique_url(self, input_path: str):
        counter = 1
        uniq_url = f'{self.scheme}://{self.bucket}/{os.path.basename(input_path)}'
        root, ext = os.path.splitext(uniq_url)
        while uniq_url in self.unique_urls:
            counter += 1
            uniq_url = f'{root}_{counter}{ext}'
        self.unique_urls.add(uniq_url)

        return uniq_url


def transfer_data(source: str, dest: str, backend: str, dry_run: bool, flowcells: Dict[str, lane_manager] = None, verbose: bool = True) -> None:
    """Transfer source to dest (cloud destination).
       backend, choosing from gcp and aws.
       flowcells is a global flowcell manangement object.
    """
    if verbose:
        print(f'{"Dry run: " if dry_run else ""}Uploading {source} to {dest}.')

    if path_is_flowcell(source):
        lanes = flowcells[source].get_lanes() if flowcells is not None else ['*']
        transfer_flowcell(source, dest, backend, lanes, dry_run)
    else:
        if os.path.isdir(source):
            run_command(['strato', 'sync', '--backend', backend, '--ionice', '-m', source, dest], dry_run, suppress_stdout=not verbose)
        else:
            run_command(['strato', 'cp', '--backend', backend, '--ionice', source, dest], dry_run, suppress_stdout=not verbose)


def transfer_sample_sheet(input_file: str, backend: str, input_file_to_output_url: dict, url_gen: cloud_url_factory, dry_run: bool, verbose: bool=True) -> Tuple[str, bool]:
    """Check sample sheet and upload files inside it.
       input_file: sample sheet
       backend: choosing from 'gcp' and 'aws'
       input_file_to_output_url: global dictionary maps local files to cloud urls
       url_gen: cloud url factory to make sure no duplicated cloud urls
       dry_run: if dry run
       verbose: if print info

       Returns: path to updated input file (if changed) and if sample sheet is changed
    """
    is_changed = False

    try:
        df = pd.read_csv(input_file, sep=None, engine='python', header=None, index_col=False)
    except Exception:
        return input_file, is_changed

    flowcells = defaultdict(lane_manager)
    col_names = np.char.array(df.iloc[0,:], unicode = True).lower()

    if ('flowcell' in col_names) and ('lane' in col_names):
        df.columns = col_names
        for idx, row in df[1:].iterrows():
            flowcells[row['flowcell']].update_lanes(row['lane'])

    for idx, row in df[1:].iterrows():
        for idxc, value in row.iteritems():
            if isinstance(value, str) and os.path.exists(value):
                value = os.path.abspath(value)
                sub_url = input_file_to_output_url.get(value, None)
                if sub_url is None:
                    sub_url = url_gen.get_unique_url(value)
                    transfer_data(value, sub_url, backend, dry_run, flowcells=flowcells, verbose=verbose)
                    input_file_to_output_url[value] = sub_url
                row[idxc] = sub_url
                is_changed = True

    if is_changed:
        orig_file = input_file
        input_file = tempfile.mkstemp()[1]
        if verbose:
            print(f'Rewriting file {orig_file} to {input_file}.')
        out_sep = ',' if orig_file.endswith('.csv') else '\t'
        df.to_csv(input_file, sep=out_sep, index=False, header=False)

    return input_file, is_changed


search_inside_file_whitelist = set(['.txt', '.xlsx', '.tsv', '.csv'])

def upload_to_cloud_bucket(
    inputs: Dict[str, str],
    backend: str,
    bucket: str,
    bucket_folder: str,
    out_json: str,
    dry_run: bool,
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

    Returns
    -------
    None

    Examples
    --------
    >>> upload_to_cloud_bucket(inputs, 'gcp', 'my_bucket', 'input_files', 'updated_inputs.json', False)
    """
    if bucket_folder is not None:
        bucket += f"/{bucket_folder.strip('/')}"

    url_gen = cloud_url_factory(backend, bucket)
    input_file_to_output_url = {}

    for k, v in inputs.items():
        input_path = v
        if isinstance(input_path, str) and os.path.exists(input_path):
            input_path = os.path.abspath(input_path)
            if input_path in input_file_to_output_url: # if this file has been processed, skip
                continue

            input_url = url_gen.get_unique_url(input_path)
            input_file_to_output_url[input_path] = input_url

            is_changed = False
            input_path_extension = os.path.splitext(input_path)[1].lower()

            if input_path_extension in search_inside_file_whitelist:
                # look inside input file to see if there are file paths within
                input_path, is_changed = transfer_sample_sheet(input_path, backend, input_file_to_output_url, url_gen, dry_run, verbose)

            transfer_data(input_path, input_url, backend, dry_run, verbose=verbose)
            inputs[k] = input_url
            if is_changed: # delete temporary file after uploading
                os.remove(input_path)

    if out_json is not None:
        with open(out_json, 'w') as fout:
            json.dump(inputs, fout, indent=4)
