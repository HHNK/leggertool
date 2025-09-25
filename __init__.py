import logging
import os
import sys
from pathlib import Path

OUR_DIR = Path(__file__).parent

EXTERNAL_DEPENDENCY_DIR = OUR_DIR / "external"


log = logging.getLogger('legger')
log.setLevel(logging.DEBUG)

def _update_path(directories):
    """update path with directories."""
    for dir_path in directories:
        dir_path = Path(dir_path)
        if dir_path.exists():
            if str(dir_path) not in sys.path:
                sys.path.append(str(dir_path))
                log.info(f"{dir_path} added to sys.path")
        else:
            log.warning(
                f"{dir_path} does not exist and is not added to sys.path"
                )

try:
    import pyqtgraph
except ImportError:
    log.info('no installation of pyqtgraph found, use one in external folder')
    _update_path([EXTERNAL_DEPENDENCY_DIR])

try:
    import sqlalchemy
except ImportError:
    log.info('no installation of sqlalchemy found, use one in external folder')
    _update_path([EXTERNAL_DEPENDENCY_DIR])

try:
    import geoalchemy2    
except ImportError:
    log.info('no installation of geoalchemy2 found, use one in external folder')
    _update_path([EXTERNAL_DEPENDENCY_DIR])


if sys.stderr is not None:
    pass
    import faulthandler
    # faulthandler.enable()

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load main tool class
    :param iface: QgsInterface. A QGIS interface instance.
    """
    from .qgistools_plugin import Legger
    from legger.utils.qlogging import setup_logging

    setup_logging()
    return Legger(iface)
