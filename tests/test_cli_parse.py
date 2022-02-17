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
import json
from pathlib import Path
from typing import Callable
from typing import List
from typing import Optional

import requests_mock as req_mock
from click.testing import Result
from pytest import MonkeyPatch
from pytest_mock import MockFixture
from requests_mock.mocker import Mocker as rm_Mocker
from requests_mock.request import _RequestObjectProxy

from lep_downloader import config as conf
from lep_downloader.lep import as_lep_episode_obj


def test_parse_incorrect_archive_url(
    requests_mock: rm_Mocker,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints error text and exits for incorrect archive page."""
    requests_mock.get(conf.ARCHIVE_URL, text="Invalid archive page")
    result = run_cli_with_args(["parse"])
    assert "ERROR:" in result.output
    assert "Can't parse this page: 'article' tag was not found." in result.output
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
    assert "ERROR: No episode links on archive page" in result.output
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
    assert "WARNING:" in result.output
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
    assert "ERROR:" in result.output
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
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
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

    monkeypatch.chdir(tmp_path)

    result = run_cli_with_args(["parse"])

    expected_message = "Database contains more episodes than current archive!"
    assert "WARNING:" in result.output
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


def test_saving_html_in_pull_mode(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    modified_json_less_db_mock: str,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It pulls all episodes which are not in database.

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

    expected_subfolder = tmp_path / "data_dump"

    run_cli_with_args(["parse", "--with-html", "--mode", "pull"])

    file_1 = "[2017-03-11] # LEP on ZEP – My recent interview on Zdenek’s English Podcast.html"  # noqa: E501,B950
    file_2 = "[2021-04-11] # 714. Robin from Hamburg (WISBOLEP Runner-Up).html"
    file_3 = "[2021-08-03] # 733. A Summer Ramble.html"
    expected_file_1 = expected_subfolder / file_1
    expected_file_2 = expected_subfolder / file_2
    expected_file_3 = expected_subfolder / file_3
    assert len(list(expected_subfolder.iterdir())) == 3
    assert expected_file_1.exists()
    assert expected_file_2.exists()
    assert expected_file_3.exists()


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


def test_parsing_archive_in_raw_mode(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    json_db_mock: str,
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

    monkeypatch.chdir(tmp_path)

    run_cli_with_args(["parse", "--mode=raw"])

    expected_folder = tmp_path
    parsed_json = (expected_folder / conf.DEFAULT_JSON_NAME).read_text()
    raw_episodes = json.loads(parsed_json, object_hook=as_lep_episode_obj)
    db_episodes = json.loads(json_db_mock, object_hook=as_lep_episode_obj)
    assert len(list(expected_folder.iterdir())) == 1
    assert len(raw_episodes) == len(db_episodes) == 782


def test_cannot_write_parsing_result_json_before_execution(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
    mocker: MockFixture,
) -> None:
    """It parses anything if current folder has no permission."""
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)

    monkeypatch.chdir(tmp_path)

    # mock = mocker.patch("json.dump")
    mock = mocker.patch("pathlib.Path.write_text")
    mock.side_effect = PermissionError()

    result = run_cli_with_args(["parse", "--mode=raw"])

    expected_folder = tmp_path
    assert "Error: Invalid value for '--dest' / '-d':" in result.output
    assert "folder has no 'write' permission" in result.output
    assert len(list(expected_folder.iterdir())) == 0


def test_saving_parsing_json_to_custom_relative_path(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    modified_json_less_db_mock: str,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It saves JSON result file into custom relative folder."""
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

    run_cli_with_args(["parse", "-m", "fetch", "--dest", "sub/sub2"])

    expected_subfolder = tmp_path / "sub/sub2"

    expected_file = expected_subfolder / conf.DEFAULT_JSON_NAME
    assert len(list(expected_subfolder.iterdir())) == 1
    assert expected_file.exists()
    with open(expected_file, "rb") as f:
        py_from_json = json.load(f, object_hook=as_lep_episode_obj)
    assert len(py_from_json) == 803


def test_incorrect_passing_option_value_to_mode_short_option(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It parses anything if current folder has no permission."""
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)

    monkeypatch.chdir(tmp_path)

    result = run_cli_with_args(["parse", "-m=raw"])  # Only works with space.

    expected_folder = tmp_path
    assert "Error: Invalid value for '--mode' / '-m':" in result.output
    assert "'=raw' is not one of 'raw', 'fetch', 'pull'" in result.output
    assert len(list(expected_folder.iterdir())) == 0


def test_json_db_not_valid(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    # capsys: CaptureFixture[str],
    # archive: Archive,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints error for invalid JSON document."""
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
    # with pytest.raises(NoEpisodesInDataBase) as ex:
    #     archive.do_parsing_actions(conf.JSON_DB_URL)
    # assert "there are NO episodes" in ex.value.args[0]
    # captured = capsys.readouterr()
    assert "ERROR:" in result.output
    assert "Data is not a valid JSON document." in result.output


def test_no_valid_episode_objects_in_json_db(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    # capsys: CaptureFixture[str],
    # archive: Archive,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints warning when there are no valid episode objects."""
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)

    requests_mock.get(
        req_mock.ANY,
        additional_matcher=single_page_matcher,
        text=single_page_mock,
    )

    requests_mock.get(
        conf.JSON_DB_URL,
        text="[]",
    )

    # with pytest.raises(NoEpisodesInDataBase) as ex:
    #     archive.do_parsing_actions(conf.JSON_DB_URL)
    # assert "there are NO episodes" in ex.value.args[0]

    # captured = capsys.readouterr()
    result = run_cli_with_args(["parse"])
    assert "WARNING:" in result.output
    assert "no valid episode objects" in result.output


def test_json_db_contains_only_string(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints warning for JSON as str."""
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
    assert "WARNING:" in result.output
    assert "no valid episode objects" in result.output


def test_invalid_objects_in_json_not_included(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It skips invalid objects in JSON database."""
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=single_page_matcher,
        text=single_page_mock,
    )
    requests_mock.get(
        conf.JSON_DB_URL,
        text='[{"episode": 1, "fake_key": "Skip me"}]',
    )

    result = run_cli_with_args(["parse"])
    assert "WARNING:" in result.output
    assert "no valid episode objects" in result.output


def test_write_log_error_when_non_episode_url(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    modified_json_less_db_mock: str,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It saves HTML files into custom absolute folder."""
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)
    origin_url = "https://teacherluke.co.uk/2021/04/11/714-robin-from-hamburg-%f0%9f%87%a9%f0%9f%87%aa-wisbolep-runner-up/"  # noqa: E501,B950
    final_url = "https://teacherluke.co.uk/premium/archive-comment-section/"
    requests_mock.get(
        origin_url,
        text="Rederecting to non episode URL",
        status_code=301,
        headers={"Location": final_url},
    )
    requests_mock.get(
        final_url,
        text="Non-episode page",
    )

    requests_mock.get(
        conf.JSON_DB_URL,
        text=modified_json_less_db_mock,
    )

    monkeypatch.chdir(tmp_path)

    run_cli_with_args(["--debug", "parse", "-html", "-hd", f"{tmp_path}"])

    expected_folder = tmp_path

    log = Path(tmp_path / "_lep_debug_.log").read_text(encoding="utf-8")

    assert len(list(expected_folder.iterdir())) == 2  # JSON file + debug log
    record = (
        "Non-episode URL: "
        + origin_url
        + " | Location: "
        + final_url
        + " | err: "
        + "Can't parse episode number"
    )
    assert "WARNING" in log
    assert record in log


def test_write_invalid_objects_of_json_to_logfile(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    run_cli_with_args: Callable[[List[str]], Result],
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    """It writes invalid objects into logfile."""
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=single_page_matcher,
        text=single_page_mock,
    )
    requests_mock.get(
        conf.JSON_DB_URL,
        text='[{"episode": 1, "fake_key": "Skip me"}]',
    )

    monkeypatch.chdir(tmp_path)

    result = run_cli_with_args(["--debug", "parse"])
    assert "WARNING:" in result.output
    assert "no valid episode objects" in result.output
    log = Path(tmp_path / "_lep_debug_.log").read_text(encoding="utf-8")
    assert "WARNING" in log
    assert "Invalid object in JSON:" in log


def test_write_critical_logrecord_for_archive_without_episodes(
    requests_mock: rm_Mocker,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It records CRITICAL message into logfile for archive without episodes."""
    markup = """<!DOCTYPE html><head><title>The Dormouse'req_ses story</title></head>
        <article>
            <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                and they lived at the bottom of a well.
            </p>
            <p class="story">...</p>
    """  # noqa: E501,B950
    requests_mock.get(conf.ARCHIVE_URL, text=markup)
    monkeypatch.chdir(tmp_path)

    result = run_cli_with_args(["--debug", "parse"])

    logfile = tmp_path / "_lep_debug_.log"
    log_text = logfile.read_text(encoding="utf-8")
    assert "ERROR: No episode links on archive page" in result.output
    assert "| CRITICAL | No episode links on archive page" in log_text


def test_write_critical_logrecord_for_invalid_archive_page(
    requests_mock: rm_Mocker,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It records CRITICAL message into logfile for invalid archive html."""
    # NOTE: No !DOCTYPE for html tag, but there is <article>
    markup = """<html><head><title>The Dormouse'req_ses story</title></head>
        <article>
            <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                and they lived at the bottom of a well.
            </p>
            <p class="story">...</p>
    """  # noqa: E501,B950
    requests_mock.get(conf.ARCHIVE_URL, text=markup)
    monkeypatch.chdir(tmp_path)

    result = run_cli_with_args(["--debug", "parse"])

    logfile = tmp_path / "_lep_debug_.log"
    log_text = logfile.read_text(encoding="utf-8")
    assert "ERROR: Can't parse this page: 'article' tag was not found." in result.output
    assert "| CRITICAL | No 'DOCTYPE' or 'article' tag" in log_text


def test_updating_with_custom_json_url(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    modified_json_less_db_mock: str,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It parses new episodes comparing with custom DB URL."""
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=single_page_matcher,
        text=single_page_mock,
    )
    requests_mock.get(
        "https://hotenov.com/some_json_url.json",
        text=modified_json_less_db_mock,
    )

    monkeypatch.chdir(tmp_path)

    expected_subfolder = tmp_path / "data_dump"

    run_cli_with_args(
        [
            "parse",
            "-html",
            "--mode",
            "pull",
            "--db-url",
            "https://hotenov.com/some_json_url.json",
        ]
    )

    file_1 = "[2017-03-11] # LEP on ZEP – My recent interview on Zdenek’s English Podcast.html"  # noqa: E501,B950
    file_2 = "[2021-04-11] # 714. Robin from Hamburg (WISBOLEP Runner-Up).html"
    file_3 = "[2021-08-03] # 733. A Summer Ramble.html"
    expected_file_1 = expected_subfolder / file_1
    expected_file_2 = expected_subfolder / file_2
    expected_file_3 = expected_subfolder / file_3
    assert len(list(expected_subfolder.iterdir())) == 3
    assert expected_file_1.exists()
    assert expected_file_2.exists()
    assert expected_file_3.exists()


def test_handling_unknown_exception_in_debug_mode(
    requests_mock: rm_Mocker,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    archive_page_mock: str,
    run_cli_with_args: Callable[[List[str]], Result],
    mocker: MockFixture,
) -> None:
    """It prints short message to user.

    And records CRITICAL message into logfile for unhandled exception.
    """
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)
    monkeypatch.chdir(tmp_path)

    mock = mocker.patch("lep_downloader.parser.Archive.do_parsing_actions")
    mock.side_effect = Exception("Unknown Exception!")

    result = run_cli_with_args(["--debug", "parse"])

    logfile = tmp_path / "_lep_debug_.log"
    log_text = logfile.read_text(encoding="utf-8")
    assert f"See details in log file: {str(logfile)}" in result.output
    assert "| CRITICAL | Unhandled: Unknown Exception!" in log_text


def test_handling_unknown_exception_during_parsing(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    run_cli_with_args: Callable[[List[str]], Result],
    mocker: MockFixture,
) -> None:
    """It prints short message to user with exception details."""
    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)

    mock = mocker.patch("lep_downloader.parser.Archive.do_parsing_actions")
    mock.side_effect = Exception("Unknown Exception!")

    result = run_cli_with_args(["parse"])

    assert "Oops.. Unhandled error.\n" in result.output
    assert "\tUnknown Exception!" in result.output


def test_writing_log_for_permission_error_during_saving_html(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    modified_json_less_db_mock: str,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It writes errors during writing HTML files to logfile."""
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

    # Make dir with the same name of one HTML
    Path(tmp_path / "[2021-08-03] # 733. A Summer Ramble.html").mkdir()

    run_cli_with_args(["--debug", "parse", "-html", "-hd", f"{tmp_path}"])

    logfile = tmp_path / "_lep_debug_.log"
    log_text = logfile.read_text(encoding="utf-8")
    expected_file = tmp_path / "[2021-08-03] # 733. A Summer Ramble.html"

    assert f"| WARNING  | Permission Error for HTML: {expected_file}" in log_text
