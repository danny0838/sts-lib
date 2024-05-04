#!/usr/bin/env python3
"""Fetch and update external resources"""
import json
import os
import re
import zipfile

import requests

from sts import Table

OPENCC_VER = 'ver.1.1.7'  # e.g. 'ver.1.1.7', 'master'
OPENCC_URL = f'https://github.com/BYVoid/OpenCC/archive/{OPENCC_VER}.zip'
OPENCC_DIR_MAP = {
    'data/dictionary': 'dictionary',
}

MW_VER = '1.41.1'  # e.g. '1.41.1', 'master'
MW_URL = f'https://raw.githubusercontent.com/wikimedia/mediawiki/{MW_VER}/includes/languages/data/ZhConversion.php'
MW_DICT_PATTERN = re.compile(r'public static \$(\w+) = \[(.*?)\];', re.M + re.S)
MW_DICT_SUBPATTERN = re.compile(r"'([^']*)' => '([^']*)',")

NTW_VER = '1.0.1'  # e.g. '1.0.1', 'latest'
NTW_URL_PREFIX = f'https://www.unpkg.com/tongwen-dict@{NTW_VER}/dist/'
NTW_SRCS = [
    's2t-char.min.json',
    's2t-phrase.min.json',
    't2s-char.min.json',
    't2s-phrase.min.json',
]

REQUEST_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}


def fetch_on_demand(url, dest):
    if os.path.isfile(dest):
        print(f'skipped fetching (up-to-date): {dest}')
        return

    print(f'fetching: {url}')
    response = requests.get(url, stream=True, headers=REQUEST_HEADERS)
    if not response.ok:
        raise RuntimeError(f'failed to fetch: {url}')

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'wb') as fh:
        for chunk in response.iter_content(chunk_size=None):
            fh.write(chunk)


def handle_opencc(root_dir):
    file = os.path.join(root_dir, '_cache', f'opencc-{OPENCC_VER}.zip')
    fetch_on_demand(OPENCC_URL, file)

    with zipfile.ZipFile(file) as zh:
        for zinfo in zh.infolist():
            # remove top dir from path
            zinfo.filename = '/'.join(zinfo.filename.split('/')[1:])

            for src, dst in OPENCC_DIR_MAP.items():
                if os.path.dirname(zinfo.filename) == src:
                    zinfo.filename = f'{dst}/{os.path.basename(zinfo.filename)}'
                    print(f'extracting: {zinfo.filename}')
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
        print(f'updating: {dest}')
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
        print(f'updating: {dest}')
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(file, encoding='UTF-8') as fh:
            data = json.load(fh)
        with open(dest, 'w', encoding='UTF-8') as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False, check_circular=False)


def main():
    root_dir = os.path.normpath(os.path.join(__file__, '..', '..'))
    data_dir = os.path.normpath(os.path.join(root_dir, 'sts', 'data'))

    handle_opencc(os.path.join(data_dir, 'external', 'opencc'))
    handle_mw(os.path.join(data_dir, 'external', 'mw'))
    handle_tongwen(os.path.join(data_dir, 'external', 'tongwen'))


if __name__ == '__main__':
    main()
