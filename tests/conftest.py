# MIT License
#
# Copyright (c) 2021 Artem Hotenov
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Package-wide test fixtures."""
from pathlib import Path

import pytest

from lep_downloader import config as conf


@pytest.fixture(scope="session")
def mocks_dir_path() -> Path:
    """Returns path to 'fixtures' direcory."""
    fixtures_dir = Path(
        Path(__file__).resolve().parent,
        "fixtures",
    )
    return fixtures_dir


@pytest.fixture(scope="module")
def html_mocks_path(mocks_dir_path: Path) -> Path:
    """Returns path to 'ep_htmls' sub-direcory of mocks."""
    html_dir = mocks_dir_path / "ep_htmls"
    return html_dir


@pytest.fixture(scope="module")
def archive_page_mock(mocks_dir_path: Path) -> str:
    """Returns str object of archive HTML mocked page."""
    page_path = mocks_dir_path / conf.LOCAL_ARCHIVE_HTML
    return page_path.read_text(encoding="utf-8")
