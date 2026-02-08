__version__ = '0.38.0'

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

from .common import (  # noqa: E402, F401  # re-exporting as public API
    StsConverter,
    StsConvExclude,
    StsDictConv,
    StsDictMatch,
    StsMaker,
    Table,
    Trie,
    Unicode,
)
