#!/usr/bin/env python3
"""Build htmlpage"""
import glob
import os
import re
import shutil
import tempfile

import jinja2
import requests

from sts import StsMaker, Table, Trie


PUBLIC_DIR = '_public'

MW_REF = 'master'
MW_URL = f'https://raw.githubusercontent.com/wikimedia/mediawiki/{MW_REF}/includes/languages/data/ZhConversion.php'
MW_DICTS = {
    'zh2Hant': ['zh2Hant'],
    'zh2Hans': ['zh2Hans'],
    'zh2TW': ['zh2TW', 'zh2Hant'],
    'zh2HK': ['zh2HK', 'zh2Hant'],
    'zh2CN': ['zh2CN', 'zh2Hans'],
}
MW_DICT_PATTERN = re.compile(r'public static \$(\w+) = \[(.*?)\];', re.M + re.S)
MW_DICT_SUBPATTERN = re.compile(r"'([^']*)' => '([^']*)',")

NTW_REF = 'latest'
NTW_URL_PREFIX = f'https://www.unpkg.com/tongwen-dict@{NTW_REF}/dist/'
NTW_SRCS = [
    's2t-char.min.json',
    's2t-phrase.min.json',
    't2s-char.min.json',
    't2s-phrase.min.json',
]
NTW_DICTS = {
    's2t': ['s2t-char'],
    's2tp': ['s2t-char', 's2t-phrase'],
    't2s': ['t2s-char'],
    't2sp': ['t2s-char', 't2s-phrase'],
}


def check_update(file, tpl):
    """Check if the file needs update."""
    return not os.path.isfile(file) or os.path.getmtime(tpl.filename) > os.path.getmtime(file)


def render_on_demand(file, tpl, *args, **kwargs):
    # @TODO: render only if the template or an included file is updated
    # if not check_update(file, tpl):
        # return

    print(f'building: {file}')
    with open(file, 'w', encoding='utf-8') as fh:
        tpl.stream(*args, **kwargs).dump(fh)


def main():
    root_dir = os.path.normpath(os.path.join(__file__, '..', '..'))
    data_dir = os.path.normpath(os.path.join(root_dir, 'sts', 'data'))
    tpl_dir = os.path.normpath(os.path.join(data_dir, 'htmlpage'))

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(tpl_dir),
    )

    # build template for CLI -f htmlpage
    file = os.path.join(data_dir, 'htmlpage.tpl.html')
    tpl = env.get_template('index_single.html')
    render_on_demand(file, tpl, single_page=True)

    # build static site contents under PUBLIC_DIR
    www_dir = os.path.join(root_dir, PUBLIC_DIR)
    os.makedirs(www_dir, exist_ok=True)
    for fn in ('index.html', 'index.css', 'index.js', 'sts.js'):
        file = os.path.join(www_dir, fn)
        tpl = env.get_template(fn)
        render_on_demand(file, tpl)

    # -- compile *.tlist for opencc
    maker = StsMaker()

    dicts_dir = os.path.join(www_dir, 'dicts', 'opencc')
    os.makedirs(dicts_dir, exist_ok=True)
    config_files = os.path.join(glob.escape(StsMaker.config_dir), '[!_]*.json')
    for config_file in glob.iglob(config_files):
        file = maker.make(config_file, quiet=True)
        basename = os.path.basename(file)
        dest = os.path.join(dicts_dir, basename)

        if not os.path.isfile(dest) or os.path.getmtime(file) > os.path.getmtime(dest):
            print(f'updating: {dest}')
            shutil.copyfile(file, dest)

    # -- compile *.tlist for MediaWiki
    print(f'fetching: {MW_URL}')
    response = requests.get(MW_URL)
    if not response.ok:
        raise RuntimeError(f'failed to fetch: {MW_URL}')
    text = response.text

    dicts_dir = os.path.join(www_dir, 'dicts', 'mw')
    os.makedirs(dicts_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp_dir:
        for match in MW_DICT_PATTERN.finditer(text):
            name, data = match.group(1), match.group(2)
            table = Table()
            for m in MW_DICT_SUBPATTERN.finditer(data):
                table.add(m.group(1), m.group(2), skip_check=True)
            file = os.path.join(tmp_dir, f'{name}.list')
            table.dump(file)

        for dst, srcs in MW_DICTS.items():
            srcs = (os.path.join(tmp_dir, f'{src}.list') for src in srcs)
            dest = os.path.join(dicts_dir, f'{dst}.tlist')
            print(f'building: {dest}')
            table = Trie().load(*srcs)
            table.dumpjson(dest)

    # -- compile *.tlist for tongwen-dict
    dicts_dir = os.path.join(www_dir, 'dicts', 'tongwen')
    os.makedirs(dicts_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp_dir:
        for src in NTW_SRCS:
            url = f'{NTW_URL_PREFIX}{src}'
            print(f'fetching: {url}')
            response = requests.get(url)
            if not response.ok:
                raise RuntimeError(f'failed to fetch: {url}')

            dict_ = response.json()
            table = Table()
            for k, v in dict_.items():
                table.add(k, v, skip_check=True)

            # remove .min.json
            fn, _ = os.path.splitext(src)
            fn, _ = os.path.splitext(fn)

            file = os.path.join(tmp_dir, f'{fn}.list')
            table.dump(file)

        for dst, srcs in NTW_DICTS.items():
            srcs = (os.path.join(tmp_dir, f'{src}.list') for src in srcs)
            dest = os.path.join(dicts_dir, f'{dst}.tlist')
            print(f'building: {dest}')
            table = Trie().load(*srcs)
            table.dumpjson(dest)


if __name__ == '__main__':
    main()
