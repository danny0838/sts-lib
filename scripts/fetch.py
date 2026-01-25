#!/usr/bin/env python3
"""Fetch and update external resources."""
import argparse
import json
import logging
import os
import re
import zipfile

import requests
import yaml

from sts import Table

logging.basicConfig(format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

UNIHAN_VER = '17.0.0'
UNIHAN_URL = f'https://www.unicode.org/Public/{UNIHAN_VER}/ucd/Unihan.zip'
UNIHAN_TABLES = {
    'kTraditionalVariant': 'TraditionalVariant',
    'kSimplifiedVariant': 'SimplifiedVariant',
    'kSemanticVariant': 'SemanticVariant',
    'kSpecializedSemanticVariant': 'SpecializedSemanticVariant',
    'kZVariant': 'ZVariant',
    'kSpoofingVariant': 'SpoofingVariant',
}

OPENCC_VER = 'eec2a142e9debfc2c6070d349a4bd183c4a5e046'  # e.g. 'ver.1.1.7', 'master'
OPENCC_URL = f'https://github.com/BYVoid/OpenCC/archive/{OPENCC_VER}.zip'
OPENCC_DIR_MAP = {
    'data/dictionary': 'dictionary',
    'test/testcases': 'tests',
}

MW_VER = '1.43.1'  # e.g. '1.41.1', 'master'
MW_URL = f'https://raw.githubusercontent.com/wikimedia/mediawiki/{MW_VER}/includes/languages/data/ZhConversion.php'
MW_DICT_PATTERN = re.compile(r'public static \$(\w+) = \[(.*?)\];', re.M + re.S)
MW_DICT_SUBPATTERN = re.compile(r"'([^']*)' => '([^']*)',")

NTW_VER = '1.0.2'  # e.g. '1.0.1', 'latest'
NTW_URL_PREFIX = f'https://www.unpkg.com/tongwen-dict@{NTW_VER}/dist/'
NTW_SRCS = [
    's2t-char.min.json',
    's2t-phrase.min.json',
    't2s-char.min.json',
    't2s-phrase.min.json',
]

FANHUAJI_VER = '58502aea63ca2e5f5e06a2f8b3ea4041b6fc5708'
FANHUAJI_URL = f'https://gist.githubusercontent.com/n6333373/f06a3aa27fcde0ba31c5955cfc33ca85/raw/{FANHUAJI_VER}/converter_testbench.yaml'
FANHUAJI_CONVERTER_MAP = {
    'Simplified': 't2s',
    'Traditional': 's2t',
    'China': 'tw2sp',
    'Taiwan': 's2twp',
    'Hongkong': None,
}

REQUEST_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}


def fetch_on_demand(url, dest):
    if os.path.isfile(dest):
        logger.debug('skipped fetching (up-to-date): %s', dest)
        return

    logger.info('fetching: %s', url)
    response = requests.get(url, stream=True, headers=REQUEST_HEADERS)
    if not response.ok:
        raise RuntimeError(f'failed to fetch: {url}')

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'wb') as fh:
        for chunk in response.iter_content(chunk_size=None):
            fh.write(chunk)


def handle_unihan(root_dir):
    file = os.path.join(root_dir, '_cache', f'Unihan-{UNIHAN_VER}.zip')
    fetch_on_demand(UNIHAN_URL, file)

    tables = {t: Table() for t in UNIHAN_TABLES.values()}

    with zipfile.ZipFile(file) as zh:
        zipinfo = zh.getinfo('Unihan_Variants.txt')
        with zh.open(zipinfo) as fh:
            for line in fh:
                if line.startswith(b'#'):
                    continue

                line = line.rstrip(b'\n')
                if not line:
                    continue

                line = line.decode('UTF-8')
                try:
                    code_from, rel, code_tos, *_ = line.split('\t')
                except ValueError:
                    continue

                try:
                    table = tables[UNIHAN_TABLES[rel]]
                except KeyError:
                    continue

                key = chr(int(code_from[2:], 16))
                values = [chr(int(c.split('<')[0][2:], 16)) for c in code_tos.split(' ')]

                # The order of values seems randomized.
                # Move key to first to prevent unexpected conversion.
                # The order can be further decided by an upper dictionary.
                try:
                    values.remove(key)
                except ValueError:
                    pass
                else:
                    values.insert(0, key)

                table.add(key, values)

    for name, table in tables.items():
        dest = os.path.join(root_dir, 'dictionary', f'{name}.txt')
        logger.info('updating: %s', dest)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        table.dump(dest)


def handle_opencc(root_dir):
    file = os.path.join(root_dir, '_cache', f'opencc-{OPENCC_VER}.zip')
    fetch_on_demand(OPENCC_URL, file)

    with zipfile.ZipFile(file) as zh:
        for zinfo in zh.infolist():
            # remove top dir from path
            subpath = '/'.join(zinfo.filename.split('/')[1:])

            if not os.path.splitext(subpath)[1].lower() in ('.txt', '.json'):
                continue

            dir_, filename = os.path.split(subpath)
            try:
                newdir = OPENCC_DIR_MAP[dir_]
            except KeyError:
                continue

            zinfo.filename = f'{newdir}/{filename}'
            logger.info('extracting: %s => %s', subpath, zinfo.filename)
            zh.extract(zinfo, root_dir)


def handle_mw(root_dir):
    file = os.path.join(root_dir, '_cache', MW_VER, 'ZhConversion.php')
    fetch_on_demand(MW_URL, file)

    with open(file, encoding='UTF-8') as fh:
        text = fh.read()

    for match in MW_DICT_PATTERN.finditer(text):
        name, data = match.group(1), match.group(2)
        table = Table()
        for m in MW_DICT_SUBPATTERN.finditer(data):
            table.add(m.group(1), m.group(2), skip_check=True)

        dest = os.path.join(root_dir, 'dictionary', f'{name}.txt')
        logger.info('updating: %s', dest)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        table.dump(dest, check=True)


def handle_tongwen(root_dir):
    for src in NTW_SRCS:
        url = f'{NTW_URL_PREFIX}{src}'

        # remove .min.json
        fn, _ = os.path.splitext(src)
        fn, _ = os.path.splitext(fn)

        file = os.path.join(root_dir, '_cache', NTW_VER, f'{fn}.json')
        fetch_on_demand(url, file)

        dest = os.path.join(root_dir, 'dictionary', f'{fn}.json')
        logger.info('updating: %s', dest)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(file, encoding='UTF-8') as fh:
            data = json.load(fh)
        with open(dest, 'w', encoding='UTF-8') as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False, check_circular=False)


def _fanhuaji_convert_tests(data):
    results = []

    for group in data:
        common = group['commons']

        if common['options'] != {'modules': {'*': 0}}:
            raise ValueError(f'Unknown options: {common["options"]}')

        config = FANHUAJI_CONVERTER_MAP[common['converter']]
        if not config:
            continue

        for test in group['tests']:
            input, expected = test['texts']
            results.append({
                'input': input,
                'expected': {
                    config: expected,
                },
            })

    return {'cases': results}


def handle_fanhuaji(root_dir):
    file = os.path.join(root_dir, '_cache', f'{FANHUAJI_VER}.yaml')
    fetch_on_demand(FANHUAJI_URL, file)

    dest = os.path.join(root_dir, 'tests', 'testcases.json')
    logger.info('updating: %s', dest)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(file, encoding='UTF-8') as fh:
        data = yaml.safe_load(fh)
    with open(dest, 'w', encoding='UTF-8') as fh:
        json.dump(_fanhuaji_convert_tests(data), fh, indent=2, ensure_ascii=False, check_circular=False)


def fetch(verbosity=logging.INFO):
    logger.setLevel(verbosity)

    root_dir = os.path.normpath(os.path.join(__file__, '..', '..'))
    data_dir = os.path.normpath(os.path.join(root_dir, 'sts', 'data'))

    handle_unihan(os.path.join(data_dir, 'external', 'unihan'))
    handle_opencc(os.path.join(data_dir, 'external', 'opencc'))
    handle_mw(os.path.join(data_dir, 'external', 'mw'))
    handle_tongwen(os.path.join(data_dir, 'external', 'tongwen'))
    handle_fanhuaji(os.path.join(data_dir, 'external', 'fanhuaji'))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-q', '--quiet', dest='verbosity', const=logging.WARN, default=logging.INFO, action='store_const',
        help='do not show processing information',
    )
    parser.add_argument(
        '-v', '--verbose', dest='verbosity', const=logging.DEBUG, default=logging.INFO, action='store_const',
        help='show processing details',
    )
    return parser.parse_args(argv)


def main():
    args = parse_args()
    fetch(args.verbosity)


if __name__ == '__main__':
    main()
