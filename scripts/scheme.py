#!/usr/bin/env python3
"""Handle scheme files."""
import argparse
import csv
import os
from contextlib import contextmanager
from textwrap import dedent

root = os.path.normpath(os.path.join(__file__, '..', '..'))

csv.register_dialect('char-table', delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE)

scheme_trad_table = {
    'src': os.path.join(root, 'sts', 'data', 'scheme', 'traditional.tsv'),
    'fields': ['trad', 'vars', 'cn', 'tw', 'hk', 'jp', 'jpg', 'notes'],
    'fields_as_list': {'vars', 'cn', 'tw', 'hk', 'jp', 'jpg'},
    'has_header': True,
    'auto_sort': True,
}

scheme_st_multi_table = {
    'src': os.path.join(root, 'sts', 'data', 'scheme', 'st_multi.tsv'),
    'fields': ['simp', 'trads', 'notes', 'examples'],
    'fields_as_list': {'trads'},
}

scheme_ts_multi_table = {
    'src': os.path.join(root, 'sts', 'data', 'scheme', 'ts_multi.tsv'),
    'fields': ['trad', 'simps', 'notes', 'examples'],
    'fields_as_list': {'simps'},
}


class CharTable(dict):
    """Extended dict to allow custom attributes."""
    def __init__(self, scheme=None, **kwargs):
        super().__init__()
        scheme = scheme or kwargs
        self.src = scheme['src']
        self.fields = scheme['fields']
        self.fields_as_list = scheme.get('fields_as_list', set())
        self.dialect = scheme.get('dialect', 'char-table')
        self.has_header = scheme.get('has_header', False)
        self.auto_sort = scheme.get('auto_sort', False)

    @contextmanager
    def open(self, mode='r'):
        if mode == 'r':
            with open(self.src, encoding='UTF-8') as fh:
                reader = csv.DictReader(fh, fieldnames=self.fields, restval='', dialect=self.dialect)
                yield self._open_reader(reader)
        elif mode == 'w':
            with open(self.src, 'w', encoding='UTF-8') as fh:
                writer = csv.DictWriter(fh, fieldnames=self.fields, extrasaction='ignore', dialect=self.dialect)
                if self.has_header:
                    writer.writeheader()
                yield writer
        else:
            raise ValueError(f'unsupported mode: {mode}')

    def _open_reader(self, reader):
        # skip an optional header row
        if self.has_header:
            reader = self._open_iterrows(reader)

        for row in reader:
            for field in self.fields_as_list:
                row[field] = [v for v in row[field].split(' ') if v]
            yield row

    def _open_iterrows(self, reader):
        header = next(reader, None)
        if header and list(header.values()) != self.fields:
            yield header
        yield from reader

    def load(self):
        with self.open() as reader:
            for row in reader:
                self.setdefault(next(iter(row.values())), row)
        return self

    def save(self):
        with self.open('w') as writer:
            keys = sorted(self) if self.auto_sort else self.keys()
            for key in keys:
                row = self[key]
                _row = {
                    k: (' '.join(v) if k in self.fields_as_list else v)
                    for k, v in row.items()
                }
                writer.writerow(_row)


def tidy_trad_table():
    table = CharTable(scheme_trad_table).load()
    table.save()
    return table


def tidy_st_multi_table():
    table = CharTable(scheme_st_multi_table).load()
    table.save()
    return table


def tidy_ts_multi_table():
    table = CharTable(scheme_ts_multi_table).load()
    table.save()
    return table


def tidy_tables():
    tidy_trad_table()
    tidy_st_multi_table()
    tidy_ts_multi_table()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
        epilog=dedent(
            """\
            available methods (non-exhaustive):
              - tidy_tables: tidy table files like {traditional|st_multi|ts_multi}.tsv
            """
        ),
    )
    parser.add_argument(
        'method', nargs='?', default='tidy_tables',
        help="""method to execute (default: %(default)s)""",
    )
    return parser.parse_args(argv)


def main():
    args = parse_args()
    try:
        method = globals()[args.method]
    except KeyError:
        raise ValueError(f'unknown method: {args.method}') from None
    else:
        method()


if __name__ == '__main__':
    main()
