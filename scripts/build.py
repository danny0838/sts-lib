#!/usr/bin/env python3
"""Build htmlpage"""
import glob
import os
import shutil

import jinja2

from sts import StsMaker

PUBLIC_DIR = '_public'


def check_update(file, ref_files):
    """Check if the file needs update."""
    if not os.path.isfile(file):
        return True

    mtime = os.path.getmtime(file)
    for ref_file in ref_files:
        if os.path.getmtime(ref_file) > mtime:
            return True

    return False


def render_on_demand(file, tpl, env, *args, **kwargs):
    ref_files = (env.get_template(t).filename for t in env.list_templates())
    if not check_update(file, ref_files):
        return

    print(f'building: {file}')
    with open(file, 'w', encoding='utf-8') as fh:
        tpl.stream(*args, **kwargs).dump(fh)


def make_from_configs(config_dir, dest_dir, maker):
    config_files = os.path.join(glob.escape(config_dir), '[!_]*.json')
    for config_file in glob.iglob(config_files):
        file = maker.make(config_file, quiet=True)
        basename = os.path.basename(file)
        dest = os.path.join(dest_dir, basename)

        if not os.path.isfile(dest) or os.path.getmtime(file) > os.path.getmtime(dest):
            print(f'updating: {dest}')
            shutil.copyfile(file, dest)


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
    render_on_demand(file, tpl, env, single_page=True)

    # build static site contents under PUBLIC_DIR
    www_dir = os.path.join(root_dir, PUBLIC_DIR)
    os.makedirs(www_dir, exist_ok=True)

    # -- build page
    for fn in ('index.html', 'index.css', 'index.js', 'sts.js'):
        file = os.path.join(www_dir, fn)
        tpl = env.get_template(fn)
        render_on_demand(file, tpl, env)

    # -- compile dicts
    maker = StsMaker()

    config_dir = os.path.join(data_dir, 'external', 'opencc', 'config')
    dicts_dir = os.path.join(www_dir, 'dicts', 'opencc')
    os.makedirs(dicts_dir, exist_ok=True)
    make_from_configs(config_dir, dicts_dir, maker)

    config_dir = os.path.join(data_dir, 'external', 'mw', 'config')
    dicts_dir = os.path.join(www_dir, 'dicts', 'mw')
    os.makedirs(dicts_dir, exist_ok=True)
    make_from_configs(config_dir, dicts_dir, maker)

    config_dir = os.path.join(data_dir, 'external', 'tongwen', 'config')
    dicts_dir = os.path.join(www_dir, 'dicts', 'tongwen')
    os.makedirs(dicts_dir, exist_ok=True)
    make_from_configs(config_dir, dicts_dir, maker)


if __name__ == '__main__':
    main()
