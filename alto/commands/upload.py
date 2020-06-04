import argparse
import os
import subprocess
import tempfile
import uuid
import json

from collections import defaultdict
from typing import List, Tuple, Dict

import numpy as np
import pandas as pd

import alto



search_inside_file_whitelist = set(['.txt', '.xlsx', '.tsv', '.csv'])

class gsurl_factory:
    def __init__(self, bucket):
        self.unique_urls = set()
        self.bucket = bucket

    def get_unique_url(self, input_path: str):
        counter = 1
        uniq_gsurl = f'gs://{self.bucket}/{os.path.basename(input_path)}'
        root, ext = os.path.splitext(uniq_gsurl)
        while uniq_gsurl in self.unique_urls:
            counter += 1
            uniq_gsurl = f'{root}_{counter}{ext}'
        self.unique_urls.add(uniq_gsurl)

        return uniq_gsurl


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
    return os.path.isdir(path) and os.path.exists(f'{path}/RunInfo.xml')


def run_command(command: List[str], dry_run: bool) -> None:
    print(' '.join(command))
    if not dry_run:
        subprocess.check_call(command)


def transfer_flowcell(source: str, dest: str, dry_run: bool, lanes: List[str]) -> None:
    run_command(['gsutil', 'cp', f'{source}/RunInfo.xml', f'{dest}/RunInfo.xml'], dry_run)
    assert os.path.exists(f'{source}/RTAComplete.txt')
    run_command(['gsutil', 'cp', f'{source}/RTAComplete.txt', f'{dest}/RTAComplete.txt'], dry_run)

    if os.path.exists(f'{source}/runParameters.xml'):
        run_command(['gsutil', 'cp', f'{source}/runParameters.xml', f'{dest}/runParameters.xml'], dry_run)
    elif os.path.exists(f'{source}/RunParameters.xml'):
        run_command(['gsutil', 'cp', f'{source}/RunParameters.xml', f'{dest}/RunParameters.xml'], dry_run)
    else:
        raise FileNotFoundError("Cannot find either runParameters.xml or RunParameters.xml!")
    
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
        run_command(['gsutil', '-m', 'rsync', '-r', lane_string.format(source, lane), lane_string.format(dest, lane)], dry_run)
    # copy locs files
    locs_string = '{0}/Data/Intensities/s.locs'
    if os.path.exists(locs_string.format(source)):
        run_command(['gsutil', 'cp', locs_string.format(source), locs_string.format(dest)], dry_run)
    else:
        locs_string = '{0}/Data/Intensities/{1}'
        for lane in lanes:
            run_command(['gsutil', '-m', 'rsync', '-r', locs_string.format(source, lane), locs_string.format(dest, lane)], dry_run)


def transfer_data(source: str, dest: str, dry_run: bool = False, flowcells: Dict[str, lane_manager] = None) -> None:
    print(('Dry run: ' if dry_run else '') + 'Uploading  ' + source + ' to ' + dest)

    if path_is_flowcell(source):
        lanes = flowcells[source].get_lanes() if flowcells is not None else ['*']
        transfer_flowcell(source, dest, dry_run, lanes)
    else:
        if os.path.isdir(source):
            run_command(['gsutil', '-m', 'rsync', '-r', source, dest], dry_run)
        else:
            run_command(['gsutil', 'cp', source, dest], dry_run)


def transfer_sample_sheet(input_file: str, input_file_to_output_gsurl: dict, gsurl_gen: gsurl_factory, dry_run: bool) -> Tuple[str, bool]:
    """
        Check sample sheet and upload files inside it
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
                sub_gs_url = input_file_to_output_gsurl.get(value, None)
                if sub_gs_url is None:
                    sub_gs_url = gsurl_gen.get_unique_url(value)
                    transfer_data(value, sub_gs_url, dry_run = dry_run, flowcells = flowcells)
                    input_file_to_output_gsurl[value] = sub_gs_url
                row[idxc] = sub_gs_url
                is_changed = True

    if is_changed:
        orig_file = input_file
        input_file = tempfile.mkstemp()[1]
        print(f'Rewriting file {orig_file} to {input_file}.')
        out_sep = ',' if orig_file.endswith('.csv') else '\t'
        df.to_csv(input_file, sep=out_sep, index=False, header=False)

    return input_file, is_changed


def upload_to_google_bucket(inputs: Dict[str, str], workspace: str, dry_run: bool, bucket_folder: str, out_json: str):
    workspace_namespace, workspace_name, workspace_version = alto.fs_split(workspace)

    bucket = alto.get_or_create_workspace(workspace_namespace, workspace_name)['bucketName']
    if bucket_folder is not None:
        bucket += '/' + bucket_folder

    gsurl_gen = gsurl_factory(bucket)
    input_file_to_output_gsurl = {}

    for k, v in inputs.items():
        input_path = v
        if isinstance(input_path, str) and os.path.exists(input_path):
            input_path = os.path.abspath(input_path)
            if input_path in input_file_to_output_gsurl:
                continue

            input_gs_url = gsurl_gen.get_unique_url(input_path)
            input_file_to_output_gsurl[input_path] = input_gs_url

            is_changed = False
            input_path_extension = os.path.splitext(input_path)[1].lower()

            if input_path_extension in search_inside_file_whitelist:
                # look inside input file to see if there are file paths within
                input_path, is_changed = transfer_sample_sheet(input_path, input_file_to_output_gsurl, gsurl_gen, dry_run)

            transfer_data(input_path, input_gs_url, dry_run = dry_run)
            inputs[k] = input_gs_url
            if is_changed:
                os.remove(input_path)

    if out_json is not None:
        with open(out_json, 'w') as fout:
            json.dump(inputs, fout)


def main(argsv):
    parser = argparse.ArgumentParser(description='Upload files/directories to a Google bucket.')
    parser.add_argument('-w', '--workspace', dest='workspace', action='store', required=True,
                        help='Workspace name (e.g. foo/bar). The workspace is created if it does not exist')
    parser.add_argument('--bucket-folder', metavar='<folder>', dest='bucket_folder', action='store',
                        help='Store inputs to <folder> under workspace''s bucket')
    parser.add_argument('--dry-run', dest='dry_run', action='store_true',
                        help='Causes upload to run in "dry run" mode, i.e., just outputting what would be uploaded without actually doing any uploading.')
    parser.add_argument('-o', dest='out_json', action='store', metavar='<updated_json>', help='Output updated input JSON file to <updated_json>')
    parser.add_argument(dest='input', help='Input JSON or file, such as a sample sheet.', nargs='+')
    inputs = {}
    args = parser.parse_args(argsv)
    for path in args.input:
        if not os.path.exists(path) or path.endswith('.json'):
            inputs.update(alto.get_wdl_inputs(path))
        else:
            inputs.update({str(uuid.uuid1()): path})
    upload_to_google_bucket(inputs, args.workspace, args.dry_run, args.bucket_folder, args.out_json)
