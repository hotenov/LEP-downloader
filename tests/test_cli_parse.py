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
"""Test cases for the parse command module."""
from typing import Callable
from typing import List
from typing import Optional

import requests_mock as req_mock
from click.testing import Result
from requests_mock.mocker import Mocker as rm_Mocker
from requests_mock.request import _RequestObjectProxy

from lep_downloader import config as conf


def test_parse_incorrect_archive_url(
    requests_mock: rm_Mocker,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints error text and exits for incorrect archive page."""
    requests_mock.get(conf.ARCHIVE_URL, text="Invalid archive page")
    result = run_cli_with_args(["parse"])
    assert "[ERROR]" in result.output
    assert "Can't parse any episodes from archive page" in result.output
    assert result.exit_code == 0


def test_parse_json_db_not_available(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints message and exits for unavailable JSON database."""
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=single_page_matcher,
        text=single_page_mock,
    )
    requests_mock.get(
        conf.JSON_DB_URL,
        text="JSON not found",
        status_code=404,
    )

    result = run_cli_with_args(["parse"])
    # assert "[ERROR]" in result.output
    assert "JSON database is not available. Exit." in result.output
    assert result.exit_code == 0


def test_parse_json_db_does_not_contain_episodes_in_plain_str(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints message and exits for JSON as plain str."""
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=single_page_matcher,
        text=single_page_mock,
    )
    requests_mock.get(
        conf.JSON_DB_URL,
        text='"episode"',
    )

    result = run_cli_with_args(["parse"])
    assert "[WARNING]" in result.output
    assert f"({conf.JSON_DB_URL})" in result.output
    assert "has no valid episode objects" in result.output
    assert "JSON is available, but" in result.output
    assert "there are NO episode in this file. Exit." in result.output
    assert result.exit_code == 0


def test_parse_json_db_invalid_document(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints message and exits for invalid JSON document."""
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=single_page_matcher,
        text=single_page_mock,
    )
    requests_mock.get(
        conf.JSON_DB_URL,
        text="",
    )

    result = run_cli_with_args(["parse"])
    assert "[ERROR]" in result.output
    assert "Data is not a valid JSON document" in result.output
    assert f"URL: {conf.JSON_DB_URL}" in result.output
    assert "JSON is available, but " in result.output
    assert "there are NO episode in this file. Exit." in result.output
    assert result.exit_code == 0


def test_parse_json_db_with_extra_episode(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    modified_json_extra_db_mock: str,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints message and exits.

    If database contains more episodes than archive page.
    """
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=single_page_matcher,
        text=single_page_mock,
    )
    requests_mock.get(
        conf.JSON_DB_URL,
        text=modified_json_extra_db_mock,
    )

    result = run_cli_with_args(["parse"])

    expected_message = "Database contains more episodes than current archive!"
    assert "[WARNING]" in result.output
    assert expected_message in result.output
    assert result.exit_code == 0


def test_parse_json_db_with_no_new_episode(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    json_db_mock: str,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints message and exits.

    If database contains more episodes than archive page.
    """
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=single_page_matcher,
        text=single_page_mock,
    )
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )

    result = run_cli_with_args(["parse"])

    expected_message = "There are no new episodes. Exit."
    assert expected_message in result.output
    assert result.exit_code == 0
