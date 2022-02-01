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
from pathlib import Path
from typing import Callable
from typing import List
from typing import Optional

import requests_mock as req_mock
from click.testing import Result
from pytest import MonkeyPatch
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
    assert "[ERROR]:" in result.output
    assert "Can't parse this page: <article> tag was not found." in result.output
    assert f"\t{conf.ARCHIVE_URL}" in result.output
    assert "Archive page has invalid HTML content. Exit." in result.output
    assert result.exit_code == 0


def test_parse_archive_without_episodes(
    requests_mock: rm_Mocker,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints error text and exits for 'empty'archive."""
    fake_html = """
    <!DOCTYPE html>
    <html>
        <article id="post-1043" class="post-1043 page type-page status-publish has-post-thumbnail hentry">
            <header class="entry-header">
                <img width="624" height="277" src="" />
                <h1 class="entry-title">EPISODES</h1>
            </header>
            <div class="entry-content">
                <h2><strong>THE ARCHIVE OF ALL EPISODES OF THE PODCAST + some extra content</strong></h2>
            </div>
        </article>
    </html>
    """  # noqa: E501,B950
    requests_mock.get(conf.ARCHIVE_URL, text=fake_html)
    result = run_cli_with_args(["parse"])
    # assert "[ERROR]:" in result.output
    assert "[ERROR]: No episode links on archive page" in result.output
    assert f"\t{conf.ARCHIVE_URL}" in result.output
    assert "Can't parse any episodes. Exit." in result.output
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
    assert "\tJSON is available, but" in result.output
    assert "there are NO episodes in this file. Exit." in result.output
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
    assert "\tJSON is available, but" in result.output
    assert "there are NO episodes in this file. Exit." in result.output
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

    If database contains the same number of episodes as on archive page.
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


def test_saving_html_to_default_path(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    modified_json_less_db_mock: str,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It saves HTML files into default folder.

    Default folder is subfolder 'data_dump' of script location path.
    """
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=single_page_matcher,
        text=single_page_mock,
    )
    requests_mock.get(
        conf.JSON_DB_URL,
        text=modified_json_less_db_mock,
    )

    monkeypatch.chdir(tmp_path)

    expected_subfolder = tmp_path / conf.PATH_TO_HTML_FILES

    run_cli_with_args(["parse", "--with-html"])

    file_1 = "[2021-04-11] # 714. Robin from Hamburg (WISBOLEP Runner-Up).html"
    file_2 = "[2021-08-03] # 733. A Summer Ramble.html"
    expected_file_1 = expected_subfolder / file_1
    expected_file_2 = expected_subfolder / file_2
    assert len(list(expected_subfolder.iterdir())) == 2
    assert expected_file_1.exists()
    assert expected_file_2.exists()


def test_saving_html_to_custom_relative_path(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    modified_json_less_db_mock: str,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It saves HTML files into custom relative folder."""
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=single_page_matcher,
        text=single_page_mock,
    )
    requests_mock.get(
        conf.JSON_DB_URL,
        text=modified_json_less_db_mock,
    )

    monkeypatch.chdir(tmp_path)

    run_cli_with_args(["parse", "-html", "--html-dir", "sub/sub2"])

    expected_subfolder = tmp_path / "sub/sub2"

    file_1 = "[2021-04-11] # 714. Robin from Hamburg (WISBOLEP Runner-Up).html"
    file_2 = "[2021-08-03] # 733. A Summer Ramble.html"
    expected_file_1 = expected_subfolder / file_1
    expected_file_2 = expected_subfolder / file_2
    assert len(list(expected_subfolder.iterdir())) == 2
    assert expected_file_1.exists()
    assert expected_file_2.exists()


def test_saving_html_to_custom_absolute_path(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    modified_json_less_db_mock: str,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It saves HTML files into custom absolute folder."""
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=single_page_matcher,
        text=single_page_mock,
    )
    requests_mock.get(
        conf.JSON_DB_URL,
        text=modified_json_less_db_mock,
    )

    monkeypatch.chdir(tmp_path)

    run_cli_with_args(["parse", "-html", "-hd", f"{tmp_path}"])

    expected_folder = tmp_path

    file_1 = "[2021-04-11] # 714. Robin from Hamburg (WISBOLEP Runner-Up).html"
    file_2 = "[2021-08-03] # 733. A Summer Ramble.html"
    expected_file_1 = expected_folder / file_1
    expected_file_2 = expected_folder / file_2
    assert len(list(expected_folder.iterdir())) == 3  # +1 JSON file
    assert expected_file_1.exists()
    assert expected_file_2.exists()


def test_not_saving_html_without_flag_option(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    modified_json_less_db_mock: str,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It doesn't save any HTML files into folder withot '-html' option."""
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=single_page_matcher,
        text=single_page_mock,
    )
    requests_mock.get(
        conf.JSON_DB_URL,
        text=modified_json_less_db_mock,
    )

    monkeypatch.chdir(tmp_path)

    run_cli_with_args(["parse", "-hd", f"{tmp_path}"])

    expected_folder = tmp_path

    file_1 = "[2021-04-11] # 714. Robin from Hamburg (WISBOLEP Runner-Up).html"
    file_2 = "[2021-08-03] # 733. A Summer Ramble.html"
    expected_file_1 = expected_folder / file_1
    expected_file_2 = expected_folder / file_2
    assert len(list(expected_folder.iterdir())) == 1  # JSON file only
    assert not expected_file_1.exists()
    assert not expected_file_2.exists()
