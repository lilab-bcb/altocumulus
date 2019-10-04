import argparse
import os
import subprocess
import tempfile
import uuid

import pandas as pd

import cumulus_util


def get_unique_url(unique_urls, base_url, name):
    counter = 1
    gs_url = base_url + name
    while gs_url in unique_urls:
        gs_url = base_url + name + '-' + str(counter)
        counter = counter + 1
    return gs_url


def upload_to_google_bucket(source, dest, dry_run=False):
    print(('Dry run: ' if dry_run else '') + 'Uploading  ' + source + ' to ' + dest)
    if not dry_run:
        if os.path.isdir(source):
            subprocess.check_call(['gsutil', '-m', 'rsync', '-r', source, dest])
        else:
            subprocess.check_call(['gsutil', '-m', 'cp', '-r', source, dest])


search_inside_file_whitelist = set(['txt', 'xlsx', 'tsv', 'csv'])


def do_fc_upload(inputs, workspace, dry_run, bucket_folder):
    workspace_namespace, workspace_name, workspace_version = cumulus_util.fs_split(workspace)
    bucket = cumulus_util.get_or_create_workspace(workspace_namespace, workspace_name)['bucketName']
    if bucket_folder is not None:
        bucket += '/' + bucket_folder
    unique_urls = set()
    input_file_to_output_gsurl = dict()
    for k, v in inputs.items():
        input_path = v
        if isinstance(input_path, str) and os.path.exists(input_path):
            input_path = os.path.abspath(input_path)
            if input_path in input_file_to_output_gsurl:
                continue
            original_path = input_path
            input_gs_url = get_unique_url(unique_urls, 'gs://' + bucket + '/', os.path.basename(input_path))
            unique_urls.add(input_gs_url)
            input_file_to_output_gsurl[input_path] = input_gs_url
            changed_file_contents = False
            input_path_extension = ''
            extension_index = input_path.rfind('.')
            if extension_index != -1:
                input_path_extension = input_path[extension_index + 1:].lower()

            if input_path_extension in search_inside_file_whitelist:
                # look inside input file to see if there are file paths within
                try:
                    df = pd.read_csv(input_path, sep=None, engine='python', header=None, index_col=False)
                except Exception:
                    pass
                for c in df.columns:
                    values = df[c].values
                    for i in range(len(values)):
                        if isinstance(values[i], str) and os.path.exists(values[i]):
                            values[i] = os.path.abspath(values[i])
                            sub_gs_url = input_file_to_output_gsurl.get(values[i], None)
                            if sub_gs_url is None:
                                sub_gs_url = get_unique_url(unique_urls, 'gs://' + bucket + '/',
                                                            os.path.basename(os.path.abspath(values[i])))
                                unique_urls.add(sub_gs_url)
                                input_file_to_output_gsurl[values[i]] = sub_gs_url
                                upload_to_google_bucket(values[i], sub_gs_url, dry_run)
                            values[i] = sub_gs_url
                            changed_file_contents = True
                    df[c] = values

            if changed_file_contents:
                input_path = tempfile.mkstemp()[1]
                print('Rewriting file paths in ' + original_path + ' to ' + input_path)
                out_sep = ',' if input_path_extension == 'csv' else '\t'
                df.to_csv(input_path, sep=out_sep, index=False, header=False)
            upload_to_google_bucket(input_path, input_gs_url, dry_run)
            inputs[k] = input_gs_url
            if changed_file_contents:
                os.remove(input_path)


def main(argsv):
    parser = argparse.ArgumentParser(description='Upload files/directories to a Google bucket.')
    parser.add_argument('-w', '--workspace', dest='workspace', action='store', required=True,
                        help='Workspace name (e.g. foo/bar). The workspace is created if it does not exist')
    parser.add_argument('--bucket-folder', metavar='<folder>', dest='bucket_folder', action='store',
                        help='Store inputs to <folder> under workspace''s bucket')
    parser.add_argument('--dry-run', dest='dry_run', action='store_true',
                        help='Causes upload to run in "dry run" mode, i.e., just outputting what would be uploaded without actually doing any uploading.')
    parser.add_argument(dest='input', help='Input JSON or file, such as a sample sheet.', nargs='+')
    inputs = {}
    args = parser.parse_args(argsv)
    for path in args.input:
        if not os.path.exists(path) or path.endswith('.json'):
            inputs.update(cumulus_util.get_wdl_inputs(path))
        else:
            inputs.update({str(uuid.uuid1()): path})
    do_fc_upload(inputs, args.workspace, args.dry_run, args.bucket_folder)
