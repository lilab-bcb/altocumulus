import argparse
from argparse import RawTextHelpFormatter
import pandas as pd



def main(argv):
    parser = argparse.ArgumentParser(description='Query project metadata from a LIMS (Laboratory Information Management System) via RESTful APIs.\n\n\
Given one project ID, this subcommand tries to fetch and display a vareity of metadata from the project. \
This subcommand also provides an option to write the metadata into a CSV file if the query type is "ngs".\n\n\
Using this subcommand requires `lims_query` Python package installed. \
Users who want to use this subcommand need to write their own lims_query package, which should at least contain one function:\n\
    query_ngs(project_id: str) -> pd.DataFrame.', formatter_class=RawTextHelpFormatter)

    parser.add_argument('pid', metavar='projectID', help='Project ID.')
    parser.add_argument('--type', choices = ['ngs', 'project'], default='ngs', help='Specify query type. Choose from "ngs" for FASTQ info or "project" for project metadata.')
    parser.add_argument('-o', dest='csv_file', help='Write metadata information to a CSV file.')

    args = parser.parse_args(argv)

    try:
        from lims_query import query_project, query_ngs
    except ImportError as e:
        import sys
        print(f"{e}\nPlease install lims_query package first.")
        sys.exit(-1)

    if args.type == "ngs":
        df = query_ngs(args.pid)
        if args.csv_file != None:
            df.to_csv(args.csv_file)
            print(f"Metadata is written to '{args.csv_file}'.")
        else:
            print(df.to_string())
    else:
        res_dict = query_project(args.pid)
        for key, value in res_dict.items():
            print(f"{key}: {value}")
