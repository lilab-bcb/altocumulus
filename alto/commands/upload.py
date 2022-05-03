import os
import argparse

from alto.utils import upload_to_cloud_bucket, parse_workspace, get_workspace_info, read_wdl_inputs



def main(argv):
    parser = argparse.ArgumentParser(description='Upload files/directories to a Cloud (gcp or aws) bucket.')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-b', '--bucket', dest='bucket', action='store',
                        help='Cloud bucket url including scheme (e.g. gs://my_bucket). If bucket starts with gs, backend is gcp; otherwise, bucket should start with s3 and backend is aws.')
    group.add_argument('-w', '--workspace', dest='workspace', action='store', help='Terra workspace name (e.g. foo/bar).')

    parser.add_argument('--bucket-folder', metavar='<folder>', dest='bucket_folder', action='store',
                        help='Store inputs to <folder> under workspace''s bucket')
    parser.add_argument('--dry-run', dest='dry_run', action='store_true',
                        help='Causes upload to run in "dry run" mode, i.e., just outputting what would be uploaded without actually doing any uploading.')
    parser.add_argument('-o', dest='out_json', action='store', metavar='<updated_json>', help='Output updated input JSON file to <updated_json>')
    parser.add_argument('--profile', dest='profile', action='store', help='AWS profile. Only works if dealing with AWS S3 buckets, and if not set, use the default profile.')
    parser.add_argument(dest='input', help='Input JSONs or files (e.g. sample sheet).', nargs='+')


    args = parser.parse_args(argv)

    if args.bucket is not None:
        if args.bucket.startswith('gs://'):
            backend = 'gcp'
        elif args.bucket.startswith('s3://'):
            backend = 'aws'
        else:
            raise ValueError(f'Unable to recognize the backend from bucket {args.bucket}!')
        bucket = args.bucket[5:]
    else:
        backend = 'gcp'
        workspace_namespace, workspace_name = parse_workspace(args.workspace)
        workspace_def = get_workspace_info(workspace_namespace, workspace_name)
        bucket = workspace_def['bucketName']

    inputs = {}
    for path in args.input:
        if not os.path.exists(path) or path.endswith('.json'):
            inputs.update(read_wdl_inputs(path))
        else:
            import uuid
            inputs.update({str(uuid.uuid1()): path})

    upload_to_cloud_bucket(
        inputs=inputs,
        backend=backend,
        bucket=bucket,
        bucket_folder=args.bucket_folder,
        out_json=args.out_json,
        dry_run=args.dry_run,
        profile=args.profile,
    )
