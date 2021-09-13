"""Test cases for the parser module."""
from pathlib import Path

import pytest

from lep_downloader import config as conf
from lep_downloader import parser

OFFLINE_HTML_DIR = Path(
    Path(__file__).resolve().parent,
    "fixtures",
)


def mock_archive_page(request, context):
    """"Callback for creating mocked Response."""
    context.status_code = 200
    # resp = io.StringIO()
    resp = OFFLINE_HTML_DIR / conf.LOCAL_ARCHIVE_HTML
    return open(resp, "rb")


def test_parsing_result(requests_mock) -> None:
    """It parses mocked archived page."""
    requests_mock.get(conf.ARCHIVE_URL, body=mock_archive_page)
    parsing_result = parser.get_archive_parsing_results(conf.ARCHIVE_URL)
    all_links = parsing_result[0]
    assert all_links is not None
    assert len(all_links) > 781
    assert "/2009/04/12/episode-1-introduction" in all_links[-1]