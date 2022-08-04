import argparse
from argparse import RawTextHelpFormatter
import pandas as pd



def main(argv):
    parser = argparse.ArgumentParser(description='Query project metadata from a LIMS (Laboratory Information Management System) via RESTful APIs.\n\n\
Given one project ID, this subcommand tries to fetch and display metadata from all libraries under the project. \
This subcommand also provides an option to write the metadata into a CSV file.\n\n\
Using this subcommand requires `lims_query` Python package installed. \
Users who want to use this subcommand need to write their own lims_query package, which should contain one function:\n\
    query_project_id(project_id: str) -> pd.DataFrame.', formatter_class=RawTextHelpFormatter)

    parser.add_argument('pid', metavar='projectID', help='Project ID.')
    parser.add_argument('-o', dest='csv_file', help='Write metadata information to a CSV file.')

    args = parser.parse_args(argv)

    try:
        from lims_query import query_project_id
    except ImportError as e:
        import sys
        print(f"{e}\nPlease install lims_query package first.")
        sys.exit(-1)

    df = query_project_id(args.pid)

    if args.csv_file != None:
        df.to_csv(args.csv_file)
    else:
        print(df.to_string())
