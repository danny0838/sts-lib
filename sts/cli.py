#!/usr/bin/env python3
"""Command line interface."""
import argparse
import os
import re
import sys

from . import StsConverter, StsMaker, Table
from . import __doc__ as _doc
from . import __version__


def sort(args):
    """Sort a conversion list.
    """
    inputs = args['file']
    outputs = args['output']

    for i, input in enumerate(inputs):
        output = input if i >= len(outputs) else outputs[i]
        Table().load(input).dump(output, sort=True)


def swap(args):
    """Swap the key and value of a conversion list.
    """
    inputs = args['file']
    outputs = args['output']

    for i, input in enumerate(inputs):
        output = input if i >= len(outputs) else outputs[i]
        Table().load(input).swap().dump(output, sort=True)


def merge(args):
    """Merge conversion lists.
    """
    input = args['input']
    output = args['output']

    Table().load(*input).dump(output, sort=True)


def find(args):
    """Find the keyword in a conversion list.
    """
    keyword = args['keyword']
    input = args['input']

    for key, values in Table().load(input).find(keyword):
        print(f'{key} => {" ".join(values)}')


def make(args):
    """Generate conversion dictionary(ies).
    """
    configs = args['config']
    skip_check = args['force']
    quiet = args['quiet']

    for config in configs:
        StsMaker().make(config, skip_check=skip_check, quiet=quiet)


def convert(args):
    """Convert text using the given config or dictionary.
    """
    inputs = args['file']
    outputs = args['output']
    force_stdout = args['stdout']
    config = args['config']
    dict_ = args['dict']
    format = args['format']
    exclude = args['exclude']
    input_encoding = args['in_enc']
    output_encoding = args['out_enc']

    if dict_ is None:
        dict_ = StsMaker().make(config, quiet=True)

    converter = StsConverter(dict_)

    # read STDIN if no input file is specified
    if not len(inputs):
        inputs.append(None)

    for i, input in enumerate(inputs):
        output = None if force_stdout else input if i >= len(outputs) else outputs[i]
        converter.convert_file(input, output, input_encoding, output_encoding,
                               format=format, exclude=exclude)


def regex(text):
    """Compile a regex str with nice error message."""
    try:
        return re.compile(text)
    except re.error as exc:
        raise ValueError(f'regex syntax error: {exc}') from None


def parse_args(argv=None):
    # Improve program name when executed through python -m
    # NOTE: We don't expect a bad command name such as having a space.
    if os.path.basename(sys.argv[0]) == '__main__.py':
        prog = f'{os.path.basename(sys.executable)} -m sts'
    else:
        prog = None

    parser = argparse.ArgumentParser(prog=prog, description=_doc)
    parser.add_argument('--version', action='version', version=f'{__package__} {__version__}',
                        help="""show version information and exit""")
    subparsers = parser.add_subparsers(dest='func', metavar='COMMAND',
                                       help="""The sub-command to run. Get usage help with e.g. %(prog)s convert -h""")

    # subcommand: convert
    parser_convert = subparsers.add_parser('convert',
                                           help=convert.__doc__, description=convert.__doc__)
    parser_convert.add_argument('file', nargs='*',
                                help="""file(s) to convert (default: STDIN)""")
    parser_convert.add_argument('-c', '--config', default='s2t',
                                help="""the config for conversion, either a built-in config name or the path to a custom JSON file
(built-in configs: s2t|t2s|s2tw|tw2s|s2twp|tw2sp|s2hk|hk2s|t2tw|tw2t|t2hk|hk2t|t2jp|jp2t)
(default: %(default)s)""")
    parser_convert.add_argument('-d', '--dict',
                                help="""the dictionary file for conversion (overrides --config)""")
    parser_convert.add_argument('-f', '--format', default='txt',
                                choices=['txt', 'txtm', 'html', 'htmlpage', 'json'], metavar='FORMAT',
                                help="""output format (txt|txtm|html|htmlpage|json) (default: %(default)s)""")
    parser_convert.add_argument('--exclude', type=regex,
                                help="""exclude text matching given regex from conversion, and replace it with the
"return" (or "return1", "return2", etc.) subgroup value if exists""")
    parser_convert.add_argument('--in-enc', default='UTF-8', metavar='ENCODING',
                                help="""encoding for input (default: %(default)s)""")
    parser_convert.add_argument('--out-enc', default='UTF-8', metavar='ENCODING',
                                help="""encoding for output (default: %(default)s)""")
    parser_convert.add_argument('-o', '--output', default=[], action='append',
                                help="""path to output (for each corresponding input) (default: to input)""")
    parser_convert.add_argument('--stdout', default=False, action='store_true',
                                help="""write all converted text to STDOUT instead""")

    # subcommand: sort
    parser_sort = subparsers.add_parser('sort',
                                        help=sort.__doc__, description=sort.__doc__)
    parser_sort.add_argument('file', nargs='+',
                             help="""file(s) to sort""")
    parser_sort.add_argument('-o', '--output', default=[], action='append',
                             help="""path to output (for the corresponding input) (default: to input)""")

    # subcommand: swap
    parser_swap = subparsers.add_parser('swap',
                                        help=swap.__doc__, description=swap.__doc__)
    parser_swap.add_argument('file', nargs='+',
                             help="""file(s) to swap""")
    parser_swap.add_argument('-o', '--output', default=[], action='append',
                             help="""path to output (for the corresponding input) (default: to input)""")

    # subcommand: merge
    parser_merge = subparsers.add_parser('merge',
                                         help=merge.__doc__, description=merge.__doc__)
    parser_merge.add_argument('input', nargs='+',
                              help="""files to merge""")
    parser_merge.add_argument('output',
                              help="""file to save as""")

    # subcommand: find
    parser_find = subparsers.add_parser('find',
                                        help=find.__doc__, description=find.__doc__)
    parser_find.add_argument('keyword',
                             help="""keyword to find""")
    parser_find.add_argument('input',
                             help="""file to find""")

    # subcommand: make
    parser_make = subparsers.add_parser('make',
                                        help=make.__doc__, description=make.__doc__)
    parser_make.add_argument('config', nargs='+',
                             help="""the config(s) to generate""")
    parser_make.add_argument('--force', default=False, action='store_true',
                             help="""bypass update check and generate dicitonary(ies) anyway""")
    parser_make.add_argument('-q', '--quiet', default=False, action='store_true',
                             help="""do not show process information""")

    return parser.parse_args(argv)


def main():
    args = vars(parse_args())
    if args['func']:
        globals()[args['func']](args)
    else:
        parse_args(['-h'])


if __name__ == '__main__':
    main()
