#!/usr/bin/env python3
"""Build htmlpage"""
import glob
import os
import shutil

import jinja2

from sts import StsMaker


PUBLIC_DIR = '_public'


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

    # -- compile *.tlist
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


if __name__ == '__main__':
    main()
