#!/usr/bin/env python3
"""Build template files and/or static website."""
import argparse
import glob
import logging
import os
import shutil
from textwrap import dedent

import jinja2

from sts import StsMaker

logging.basicConfig(format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        logger.debug('skip building (up-to-date): %s', file)
        return

    logger.info('building: %s', file)
    with open(file, 'w', encoding='utf-8') as fh:
        tpl.stream(*args, **kwargs).dump(fh)


def make_from_configs(config_dir, dest_dir, maker):
    config_files = os.path.join(glob.escape(config_dir), '[!_]*.yaml')
    for config_file in glob.iglob(config_files):
        file = maker.make(config_file)
        basename = os.path.basename(file)
        dest = os.path.join(dest_dir, basename)

        if not os.path.isfile(dest) or os.path.getmtime(file) > os.path.getmtime(dest):
            logger.info('updating: %s', dest)
            shutil.copyfile(file, dest)
        else:
            logger.debug('skip updating (up-to-date): %s', dest)


def build_templates(data_dir, env):
    """Build template files for CLI -f htmlpage."""
    file = os.path.join(data_dir, 'htmlpage.tpl.html')
    tpl = env.get_template('index_single.html')
    render_on_demand(file, tpl, env, single_page=True)


def build_static_site(root_dir, data_dir, env):
    """Build static site contents under PUBLIC_DIR."""
    www_dir = os.path.join(root_dir, PUBLIC_DIR)
    os.makedirs(www_dir, exist_ok=True)

    # build page
    for fn in ('index.html', 'index.css', 'index.js', 'sts.mjs'):
        file = os.path.join(www_dir, fn)
        tpl = env.get_template(fn)
        render_on_demand(file, tpl, env)

    # compile dicts
    maker = StsMaker()

    config_dir = os.path.join(data_dir, 'config')
    dicts_dir = os.path.join(www_dir, 'dicts', 'sts')
    os.makedirs(dicts_dir, exist_ok=True)
    make_from_configs(config_dir, dicts_dir, maker)

    config_dir = os.path.join(data_dir, 'external', 'opencc+', 'config')
    dicts_dir = os.path.join(www_dir, 'dicts', 'opencc+')
    os.makedirs(dicts_dir, exist_ok=True)
    make_from_configs(config_dir, dicts_dir, maker)

    config_dir = os.path.join(data_dir, 'external', 'mw+', 'config')
    dicts_dir = os.path.join(www_dir, 'dicts', 'mw+')
    os.makedirs(dicts_dir, exist_ok=True)
    make_from_configs(config_dir, dicts_dir, maker)

    config_dir = os.path.join(data_dir, 'external', 'tongwen+', 'config')
    dicts_dir = os.path.join(www_dir, 'dicts', 'tongwen+')
    os.makedirs(dicts_dir, exist_ok=True)
    make_from_configs(config_dir, dicts_dir, maker)

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


def build(entities=None, verbosity=logging.INFO):
    root_dir = os.path.normpath(os.path.join(__file__, '..', '..'))
    data_dir = os.path.normpath(os.path.join(root_dir, 'sts', 'data'))
    tpl_dir = os.path.normpath(os.path.join(data_dir, 'htmlpage'))

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(tpl_dir),
    )

    logger.setLevel(verbosity)
    logging.getLogger('sts').setLevel(logging.WARNING)

    if not entities or 'templates' in entities:
        build_templates(data_dir, env)

    if not entities or 'site' in entities:
        build_static_site(root_dir, data_dir, env)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
        epilog=dedent(
            f"""\
            supported entities:
              - templates: template files for e.g. "htmlpage" format
              - site: build an AJAX-powered static site at "{PUBLIC_DIR}" directory
            """
        ),
    )
    parser.add_argument(
        'entity', metavar='entity', nargs='*',
        choices=['templates', 'site'],
        help="""what to build (default: all)""",
    )
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
    build(args.entity, args.verbosity)


if __name__ == '__main__':
    main()
