"""Run from any working directory: python /path/to/main.py."""
import argparse
from src.analysis import ROOT, main

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='Reproduce California schools SQL analyses, CSVs and charts.')
    parser.add_argument('--db',default=ROOT/'data'/'schools_analysis.sqlite')
    parser.add_argument('--output',default=ROOT/'outputs')
    args=parser.parse_args()
    main(args.db,args.output)
