# coding=utf-8
import argparse
import converter
import os
from re import fullmatch

def convert(args):
    if args.format != 'maf' and args.format != 'po':
        parser.error('FILE FORMAT must be \'maf\' or \'po\'')

    if args.m and not fullmatch('\[\d+\:\d+\]', str(args.m)):
        parser.error('Wrong formatting for MERGE_BLOCKS')

    if args.hbmin and args.c != 1:
        parser.error("Option -hbmin requires -c = 1.")

    if (args.min_comp or args.r or args.t or args.multiplier or args.stop or args.re_consensus) and not args.c:
        parser.error("Options -min-comp, -r, -t, -multiplier, -stop and -re_consensus require -c.")

    if args.r and not fullmatch('\[\d+\,\d+\]', str(args.r)):
        parser.error('Wrong formatting for RANGE')

    if args.t and not fullmatch('\[\d+(\,\d+)?\]', str(args.r)):
        parser.error('Wrong formatting for TRESHOLDS')

    try:
        if args.hbmin:
            hbmin = float(args.hbmin)
            if hbmin < 0 or hbmin > 1:
                parser.error('HBMIN must be a float in range [0,1].')
        if args.min_comp:
            min_comp = float(args.min_comp)
            if min_comp < 0 or hbmin > 1:
                parser.error('MIN_COMP must be in range [0,1].')
        if args.stop:
            stop = float(args.stop)
            if stop < 0 or stop > 1:
                parser.error('STOP must be a float in range [0,1].')
    except ValueError:
        parser.error('HBMIN and MIN_COMP must be a float in range [0,1].')

    if args.data != 'ebola' and args.data != 'mycoplasma':
        parser.error('METAVAR must be \'ebola\' or \'mycoplasma\'')

    file_abs_path = os.path.abspath(args.f)
    converter.convert_maf_to_po(file_abs_path,
                                args.format,
                                args.m,
                                args.draw,
                                args.c,
                                args.r,
                                args.multiplier,
                                args.stop,
                                args.re_consensus,
                                args.t,
                                args.hbmin,
                                args.min_comp,
                                args.fasta,
                                args.data)


parser = argparse.ArgumentParser(description='PAN-GENOME tools')

subparsers = parser.add_subparsers(help='Tools available', dest='')
subparsers.required = True

parser_converter = subparsers.add_parser('mln', help='Processing multialignment')
parser_converter.add_argument('-f',
                              metavar='FILE',
                              type=str,
                              required=True,
                              help='path to the MAF (Multiple Alignment Format) file or PO (POAGraph) file')
parser_converter.add_argument('-format',
                              metavar='FILE FORMAT',
                              type=str,
                              required=True,
                              help='maf or po')
parser_converter.add_argument('-m',
                              metavar='MERGE_BLOCKS',
                              required=False,
                              help='''default behaviour is to merge all blocks, where possible; \nprovide MERGE_BLOCKS if special way of merging the blocks is required; \npass [idx1:idx2, idx3:idx4] to choose range of blocks to be merged; \nIDs begin from 1.''')
parser_converter.add_argument('-fasta',
                              action='store_true',
                              required=False,
                              help='generate FASTA files')
parser_converter.add_argument('-c',
                              metavar='CONSENSUS_OPTION',
                              required=False,
                              type=int,
                              help='consensus generation algorithm')
parser_converter.add_argument('-hbmin',
                              metavar='HBMIN',
                              required=False,
                              help='if c: HBMIN value for POA heaviest bundling alogrithm, min 0, max 1')
parser_converter.add_argument('-min_comp',
                              metavar='MINCOMP',
                              required=False,
                              help='if c and iter: minimum compatibility between source and consensus to match them')
parser_converter.add_argument('-r',
                              type=str,
                              required=False,
                              help='percentage range [v1,v2] of compatibilities where the biggest change will be searched, format (v1, v2 - floats): [v1,v2]')
parser_converter.add_argument('-multiplier',
                              metavar='MULTIPLIER',
                              required=False,
                              type=float,
                              help='Used in the tree consensus generation algorithm to establish consensuses levels.')
parser_converter.add_argument('-stop',
                              metavar='STOP_BRANCHING',
                              required=False,
                              type=float,
                              help='Used in the tree consensus generation algorithm to stop tree branching: [0, 1]')
parser_converter.add_argument('-re_consensus',
                              metavar='RECONSIDER_CONSENSUS_ASSIGNMENT',
                              action='store_true',
                              required=False,
                              help='Used in the tree consensus generation algorithm to reconsider consensus assignement after every iteration.')
parser_converter.add_argument('-t',
                              type=str,
                              required=False,
                              help='series of tresholds t1, t2, t3... to be used on tree levels, format (t1, t2... - floats): [t1, t2, t3,...]')
parser_converter.add_argument('-draw',
                              action='store_true',
                              required=False,
                              help='draw poagraph')
parser_converter.add_argument('-data',
                              metavar="DATATYPE",
                              required=True,
                              help='ebola or mycoplasma')
parser_converter.set_defaults(func=convert)

args = parser.parse_args()
args.func(args)

