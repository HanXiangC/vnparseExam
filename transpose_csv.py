"""
Utility script to transpose a CSV and write it back to file.

Use pandas, which is faster than np.genfromtxt, and more flexible with dtype
"""

# Thanks to
# http://stackoverflow.com/questions/4869189/how-to-pivot-data-in-a-csv-file

import csv
from itertools import izip

def write_transpose(in_csv, out_csv):
    a = izip(*csv.reader(open(in_csv, "rb")))
    csv.writer(open(out_csv, "wb")).writerows(a)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('in_csv', help="csv to read")
    parser.add_argument('out_csv', help="csv to write")

    args = parser.parse_args()

    write_transpose(args.in_csv, args.out_csv)
