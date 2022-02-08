"""LEP Downloader."""
from pathlib import Path

from single_source import get_version

from .lep import init_lep_log


path_to_project_dir = Path(__file__).parent.parent.parent
__version__ = get_version(__name__, path_to_project_dir)

init_lep_log()
