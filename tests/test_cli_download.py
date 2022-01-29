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
"""Test cases for the download command module."""
from pathlib import Path
from typing import Callable
from typing import List

from click.testing import CliRunner
from click.testing import Result
from pytest_mock import MockFixture
from requests_mock.mocker import Mocker as rm_Mocker

from lep_downloader import config as conf


def test_json_database_not_available(
    requests_mock: rm_Mocker,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints message and exits when JSON is unavailable."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text="JSON not found",
        status_code=404,
    )
    result = run_cli_with_args(["download"])
    assert "JSON database is not available now.\n" in result.output
    assert "Try again later." in result.output
    assert result.exit_code == 0


def test_json_database_not_available_in_quite_mode(
    requests_mock: rm_Mocker,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It aborts following execution when JSON is unavailable.

    Even in 'quiet' mode.
    """
    requests_mock.get(
        conf.JSON_DB_URL,
        text="JSON not found",
        status_code=404,
    )
    result = run_cli_with_args(["download", "--quiet"])
    assert "JSON database is not available now.\n" in result.output
    assert "Try again later." in result.output
    assert result.exit_code == 0


def test_download_without_options(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    runner: CliRunner,
) -> None:
    """It downloads all audio files for parsed episodes."""
    from lep_downloader import cli

    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    result = runner.invoke(
        cli.cli,
        ["download"],
        prog_name="lep-downloader",
        input="n\n",
    )
    assert "18 non-existing file(s) will be downloaded" in result.output
    assert "Do you want to continue? [y/N]: n\n" in result.output
    assert "Your answer is 'NO'. Exit." in result.output


def test_continue_prompt_yes(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    mp3_file1_mock: bytes,
    tmp_path: Path,
    runner: CliRunner,
) -> None:
    """It downloads files if user answers 'Yes'."""
    from lep_downloader import cli

    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    requests_mock.get(
        "https://traffic.libsyn.com/secure/teacherluke/703._Walaa_from_Syria_-_WISBOLEP_Competition_Winner_.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )

    result = runner.invoke(
        cli.cli,
        ["download", "-ep", "703", "-pdf", "-d", f"{tmp_path}"],
        prog_name="lep-downloader",
        input="y\n",
    )

    expected_filename = "[2021-02-03] # 703. Walaa from Syria – WISBOLEP Competition Winner.mp3"  # noqa: E501,B950
    expected_file = tmp_path / expected_filename
    assert "Do you want to continue? [y/N]: y\n" in result.output
    assert len(list(tmp_path.iterdir())) == 1
    # assert len(LepDL.downloaded) == 1
    # assert len(LepDL.not_found) == 1  # Page PDF file
    assert expected_file.exists()


def test_continue_prompt_no(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    tmp_path: Path,
    runner: CliRunner,
) -> None:
    """It exists if user answers 'No'."""
    from lep_downloader import cli

    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )

    result = runner.invoke(
        cli.cli,
        ["download", "-ep", "714"],
        prog_name="lep-downloader",
        input="No",
    )
    assert "Do you want to continue? [y/N]: No\n" in result.output
    assert "Your answer is 'NO'. Exit." in result.output
    assert len(list(tmp_path.iterdir())) == 0

    result = runner.invoke(
        cli.cli,
        ["download", "-ep", "714"],
        prog_name="lep-downloader",
        input="\n",  # Pressed 'Enter' key (empty input)
    )

    assert "Your answer is 'NO'. Exit." in result.output
    assert len(list(tmp_path.iterdir())) == 0


def test_no_valid_episodes_in_database(
    requests_mock: rm_Mocker,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints message and exits if no episodes in JSON database."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text="[]",
    )
    result = run_cli_with_args(["download"])
    assert (
        f"[WARNING]: JSON file ({conf.JSON_DB_URL}) has no valid episode objects."
        in result.output
    )
    assert result.exit_code == 0


def test_no_valid_episodes_quiet_mode(
    requests_mock: rm_Mocker,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It aborts following execution if no episodes in JSON database.

    Even in 'quiet' mode
    """
    requests_mock.get(
        conf.JSON_DB_URL,
        text="[]",
    )
    result = run_cli_with_args(["download", "--quiet"])
    assert (
        f"[WARNING]: JSON file ({conf.JSON_DB_URL}) has no valid episode objects."
        in result.output
    )
    assert result.exit_code == 0


def test_last_option(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    mp3_file1_mock: bytes,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It downloads the last episode when '--last' option is provided."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    requests_mock.get(
        "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )

    run_cli_with_args(["download", "-ep", "113", "--last", "-q", "-d", f"{tmp_path}"])

    expected_filename = "[2021-08-03] # 733. A Summer Ramble.mp3"
    expected_file = tmp_path / expected_filename
    # assert len(Lep.db_episodes) == 782  # Total in mocked JSON
    assert len(list(tmp_path.iterdir())) == 1
    # assert len(LepDL.downloaded) == 1
    # assert len(LepDL.not_found) == 0
    assert expected_file.exists()


def test_filtering_for_one_day(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    mp3_file1_mock: bytes,
    mp3_file2_mock: bytes,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It downloads all episodes for certain day."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    requests_mock.get(
        "http://traffic.libsyn.com/teacherluke/15-extra-podcast-12-phrasal-verbs.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )
    requests_mock.get(
        "http://traffic.libsyn.com/teacherluke/16-michael-jackson.mp3",  # noqa: E501,B950
        content=mp3_file2_mock,
    )

    run_cli_with_args(
        ["download", "-S", "2009-10-19", "-E", "2009-10-19", "-q", "-d", f"{tmp_path}"]
    )

    expected_filename_1 = "[2009-10-19] # 15. Extra Podcast – 12 Phrasal Verbs.mp3"
    expected_file_1 = tmp_path / expected_filename_1
    expected_filename_2 = "[2009-10-19] # 16. Michael Jackson.mp3"
    expected_file_2 = tmp_path / expected_filename_2
    assert len(list(tmp_path.iterdir())) == 2
    # assert len(LepDL.downloaded) == 2
    # assert len(LepDL.not_found) == 0
    assert expected_file_1.exists()
    assert expected_file_2.exists()


def test_filtering_by_start_date(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    mp3_file1_mock: bytes,
    mp3_file2_mock: bytes,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It downloads all episodes from start date to last."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    requests_mock.get(
        "https://audioboom.com/posts/5602875-episode-166-luke-back-on-zep-part-1.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )
    requests_mock.get(
        "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
        content=mp3_file2_mock,
    )

    run_cli_with_args(["download", "-S", "2017-03-11", "-q", "-d", f"{tmp_path}"])

    expected_filename_1 = "[2017-03-11] # LEP on ZEP – My recent interview on Zdenek’s English Podcast [Part 01].mp3"  # noqa: E501,B950
    expected_file_1 = tmp_path / expected_filename_1
    expected_filename_2 = "[2021-08-03] # 733. A Summer Ramble.mp3"  # noqa: E501,B950
    expected_file_2 = tmp_path / expected_filename_2
    assert len(list(tmp_path.iterdir())) == 2
    # assert len(LepDL.downloaded) == 2
    # assert len(LepDL.not_found) == 7
    assert expected_file_1.exists()
    assert expected_file_2.exists()


def test_filtering_by_end_date(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    mp3_file1_mock: bytes,
    mp3_file2_mock: bytes,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It downloads all episodes from first to end date."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    requests_mock.get(
        "http://traffic.libsyn.com/teacherluke/1-introduction.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )
    requests_mock.get(
        "http://traffic.libsyn.com/teacherluke/370-in-conversation-with-rob-ager-from-liverpool-part-1-life-in-liverpool-interest-in-film-analysis.mp3",  # noqa: E501,B950
        content=mp3_file2_mock,
    )

    run_cli_with_args(["download", "-E", "2016-08-07", "-q", "-d", f"{tmp_path}"])

    expected_filename_1 = "[2009-04-12] # 1. Introduction.mp3"
    expected_file_1 = tmp_path / expected_filename_1
    expected_filename_2 = "[2016-08-07] # 370. In Conversation with Rob Ager from Liverpool (PART 1_ Life in Liverpool _ Interest in Film Analysis).mp3"  # noqa: E501,B950
    expected_file_2 = tmp_path / expected_filename_2
    assert len(list(tmp_path.iterdir())) == 2
    # assert len(LepDL.downloaded) == 2
    # assert len(LepDL.not_found) == 7
    assert expected_file_1.exists()
    assert expected_file_2.exists()


def test_invalid_start_date_inputs(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It validates and exits with error (2) when invalid start date is provided."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )

    result = run_cli_with_args(["download", "-q", "-S"])
    assert "Error: Option '-S' requires an argument." in result.output
    assert result.exit_code == 2

    result = run_cli_with_args(["download", "-S", " ", "-q"])
    assert (
        "Error: Invalid value for '-S': date format must be 'YYYY-MM-DD'"
        in result.output
    )
    assert result.exit_code == 2

    result = run_cli_with_args(["download", "-S", "2022-01-xx", "-q"])
    assert (
        "Error: Invalid value for '-S': date format must be 'YYYY-MM-DD'"
        in result.output
    )
    assert result.exit_code == 2

    result = run_cli_with_args(["download", "-S", "2022/01/23", "-q"])
    assert (
        "Error: Invalid value for '-S': date format must be 'YYYY-MM-DD'"
        in result.output
    )
    assert result.exit_code == 2

    result = run_cli_with_args(["download", "-S", "2022-13-23", "-q"])
    assert (
        "Error: Invalid value for '-S': date format must be 'YYYY-MM-DD'"
        in result.output
    )
    assert result.exit_code == 2

    result = run_cli_with_args(
        ["download", "-S", "2022-xx-23", "-E", "2022-01-01" "-q"]
    )
    assert (
        "Error: Invalid value for '-S': date format must be 'YYYY-MM-DD'"
        in result.output
    )
    assert result.exit_code == 2


def test_invalid_end_date_inputs(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It validates and exits with error (2) when invalid end date is provided."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )

    result = run_cli_with_args(["download", "-q", "-E"])
    assert "Error: Option '-E' requires an argument." in result.output
    assert result.exit_code == 2

    result = run_cli_with_args(["download", "-E", " ", "-q"])
    assert (
        "Error: Invalid value for '-E': date format must be 'YYYY-MM-DD'"
        in result.output
    )
    assert result.exit_code == 2

    result = run_cli_with_args(["download", "-E", "2022-01-xx", "-q"])
    assert (
        "Error: Invalid value for '-E': date format must be 'YYYY-MM-DD'"
        in result.output
    )
    assert result.exit_code == 2

    result = run_cli_with_args(["download", "-E", "2022/01/23", "-q"])
    assert (
        "Error: Invalid value for '-E': date format must be 'YYYY-MM-DD'"
        in result.output
    )
    assert result.exit_code == 2

    result = run_cli_with_args(["download", "-E", "2022-13-23", "-q"])
    assert (
        "Error: Invalid value for '-E': date format must be 'YYYY-MM-DD'"
        in result.output
    )
    assert result.exit_code == 2

    result = run_cli_with_args(
        ["download", "-E", "2022-xx-23", "-S", "2022-01-01" "-q"]
    )
    assert (
        "Error: Invalid value for '-E': date format must be 'YYYY-MM-DD'"
        in result.output
    )
    assert result.exit_code == 2


def test_populating_default_url_for_page_pdf(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    mp3_file1_mock: bytes,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It populates URL and downloads page PDF."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    requests_mock.get(
        "https://hotenov.com/d/lep/%5B2017-08-26%5D%20%23%20%5BWebsite%20only%5D%20A%20History%20of%20British%20Pop%20%E2%80%93%20A%20Musical%20Tour%20through%20James%E2%80%99%20Vinyl%20Collection.pdf",  # noqa: E501,B950
        content=mp3_file1_mock,
    )

    run_cli_with_args(
        [
            "download",
            "-pdf",
            "-S",
            "2017-08-26",
            "-E",
            "2017-08-26",
            "-q",
            "-d",
            f"{tmp_path}",
        ]
    )

    expected_filename_1 = "[2017-08-26] # [Website only] A History of British Pop – A Musical Tour through James’ Vinyl Collection.pdf"  # noqa: E501,B950
    expected_file_1 = tmp_path / expected_filename_1
    assert len(list(tmp_path.iterdir())) == 1
    # assert len(LepDL.downloaded) == 1
    # assert len(LepDL.not_found) == 0
    assert expected_file_1.exists()


def test_filtering_by_one_episode_number(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    mp3_file1_mock: bytes,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It downloads one episode by its number."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    # Note: URL for #36 not for #35 (because it is 'duplicated' episode)
    requests_mock.get(
        "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )

    run_cli_with_args(["download", "-ep", "35", "-q", "-d", f"{tmp_path}"])

    expected_filename_1 = "[2010-03-25] # 35. London Video Interviews – Part 1 (Video).mp3"  # noqa: E501,B950
    expected_file_1 = tmp_path / expected_filename_1
    assert len(list(tmp_path.iterdir())) == 1
    # assert len(LepDL.downloaded) == 1
    # assert len(LepDL.not_found) == 0
    assert expected_file_1.exists()


def test_filtering_not_numbered_episodes(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    mp3_file1_mock: bytes,
    mp3_file2_mock: bytes,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It downloads all episodes with number = 0."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    requests_mock.get(
        "https://audioboom.com/posts/5678762-episode-169-luke-back-on-zep-part-4.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )
    requests_mock.get(
        "https://hotenov.com/d/lep/%5B2017-05-26%5D%20%23%20I%20was%20invited%20onto%20the%20%E2%80%9CEnglish%20Across%20The%20Pond%E2%80%9D%20Podcast.pdf",  # noqa: E501,B950
        content=mp3_file2_mock,
    )

    run_cli_with_args(
        ["download", "-ep", "0-0", "--with-pdf", "-q", "-d", f"{tmp_path}"]
    )

    expected_filename_1 = "[2017-03-11] # LEP on ZEP – My recent interview on Zdenek’s English Podcast [Part 04].mp3"  # noqa: E501,B950
    expected_file_1 = tmp_path / expected_filename_1
    expected_filename_2 = "[2017-05-26] # I was invited onto the “English Across The Pond” Podcast.pdf"  # noqa: E501,B950
    expected_file_2 = tmp_path / expected_filename_2
    assert len(list(tmp_path.iterdir())) == 2
    # assert len(LepDL.downloaded) == 2
    # assert len(LepDL.not_found) == 6
    assert expected_file_1.exists()
    assert expected_file_2.exists()


def test_filtering_by_number_with_default_start(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    mp3_file1_mock: bytes,
    mp3_file2_mock: bytes,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It downloads all episodes from 0 to provided number."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    requests_mock.get(
        "https://audioboom.com/posts/5695159-episode-170-luke-back-on-zep-part-5-analysis.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )
    requests_mock.get(
        "http://traffic.libsyn.com/teacherluke/16-michael-jackson.mp3",  # noqa: E501,B950
        content=mp3_file2_mock,
    )

    run_cli_with_args(["download", "-ep", "-16", "-q", "-d", f"{tmp_path}"])

    expected_filename_1 = "[2017-03-11] # LEP on ZEP – My recent interview on Zdenek’s English Podcast [Part 05].mp3"  # noqa: E501,B950
    expected_file_1 = tmp_path / expected_filename_1
    expected_filename_2 = "[2009-10-19] # 16. Michael Jackson.mp3"  # noqa: E501,B950
    expected_file_2 = tmp_path / expected_filename_2
    assert len(list(tmp_path.iterdir())) == 2
    # assert len(LepDL.downloaded) == 2
    # assert len(LepDL.not_found) == 6
    assert expected_file_1.exists()
    assert expected_file_2.exists()


def test_filtering_by_number_with_default_end(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    mp3_file1_mock: bytes,
    mp3_file2_mock: bytes,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It downloads all episodes from provided number to last."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    requests_mock.get(
        "https://traffic.libsyn.com/secure/teacherluke/703._Walaa_from_Syria_-_WISBOLEP_Competition_Winner_.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )
    requests_mock.get(
        "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
        content=mp3_file2_mock,
    )

    run_cli_with_args(["download", "-ep", "703-", "-q", "-d", f"{tmp_path}"])

    expected_filename_1 = "[2021-02-03] # 703. Walaa from Syria – WISBOLEP Competition Winner.mp3"  # noqa: E501,B950
    expected_file_1 = tmp_path / expected_filename_1
    expected_filename_2 = "[2021-08-03] # 733. A Summer Ramble.mp3"  # noqa: E501,B950
    expected_file_2 = tmp_path / expected_filename_2
    assert len(list(tmp_path.iterdir())) == 2
    # assert len(LepDL.downloaded) == 2
    # assert len(LepDL.not_found) == 2
    assert expected_file_1.exists()
    assert expected_file_2.exists()


def test_invalid_number_inputs(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It validates and exits with error (2) when invalid episode number is provided."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )

    result = run_cli_with_args(["download", "-q", "-ep"])
    assert "Error: Option '-ep' requires an argument." in result.output
    assert result.exit_code == 2

    result = run_cli_with_args(["download", "-ep", " ", "-q"])
    assert (
        "Invalid value for '--episode' / '-ep': ' ' is not a valid integer range."
        in result.output
    )
    assert result.exit_code == 2

    result = run_cli_with_args(["download", "-ep", "xxx", "-q"])
    assert (
        "Invalid value for '--episode' / '-ep': 'xxx' is not a valid integer range."
        in result.output
    )
    assert result.exit_code == 2

    result = run_cli_with_args(["download", "-ep", "1-xxx", "-q"])
    assert (
        "Invalid value for '--episode' / '-ep': 'xxx' is not a valid integer range."
        in result.output
    )
    assert result.exit_code == 2

    result = run_cli_with_args(["download", "-ep", "xxx-2", "-q"])
    assert (
        "Invalid value for '--episode' / '-ep': 'xxx' is not a valid integer range."
        in result.output
    )
    assert result.exit_code == 2

    result = run_cli_with_args(["download", "-ep", "0-None", "-q"])
    assert (
        "Invalid value for '--episode' / '-ep': 'None' is not a valid integer range."
        in result.output
    )
    assert result.exit_code == 2


def test_custom_db_url(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    mp3_file1_mock: bytes,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It uses provided JSON URL instead of default."""
    requests_mock.get(
        "https://hotenov.com/d/lep/3rd-version-test-mocked-db-782-objects.json",
        text=json_db_mock,
    )
    requests_mock.get(
        "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )

    run_cli_with_args(
        [
            "download",
            "--last",
            "-q",
            "-d",
            f"{tmp_path}",
            "-db",
            "https://hotenov.com/d/lep/3rd-version-test-mocked-db-782-objects.json",
        ]
    )

    expected_filename = "[2021-08-03] # 733. A Summer Ramble.mp3"
    expected_file = tmp_path / expected_filename
    # assert len(Lep.db_episodes) == 782  # Total in mocked JSON
    assert len(list(tmp_path.iterdir())) == 1
    # assert len(LepDL.downloaded) == 1
    # assert len(LepDL.not_found) == 0
    assert expected_file.exists()


def test_no_files_for_downloading(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    mp3_file1_mock: bytes,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints and exits when nothing to download."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    requests_mock.get(
        "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )

    existing_file_1 = tmp_path / "[2021-08-03] # 733. A Summer Ramble.mp3"
    existing_file_1.write_text("Fake episode #733")
    result = run_cli_with_args(
        ["download", "-S", "2020-01-20", "--last", "-q", "-d", f"{tmp_path}"]
    )

    assert len(list(tmp_path.iterdir())) == 1
    # assert len(LepDL.existed) == 1
    # assert len(LepDL.downloaded) == 0
    # assert len(LepDL.not_found) == 0
    assert "Nothing to download for now." in result.output


def test_no_permission_for_folder_destination(
    mocker: MockFixture,
    requests_mock: rm_Mocker,
    json_db_mock: str,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It validates destination folder before downloading files.

    And exists with error (2) if folder has no 'write' permission.
    """
    mock = mocker.patch("pathlib.Path.write_text")
    mock.side_effect = PermissionError

    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )

    result = run_cli_with_args(["download", "--last", "-q", "-d", f"{tmp_path}"])

    assert (
        "Invalid value for '--dest' / '-d': folder has no 'write' permission."
        in result.output
    )
    assert result.exit_code == 2


def test_os_error_for_folder_destination(
    mocker: MockFixture,
    requests_mock: rm_Mocker,
    json_db_mock: str,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It validates destination folder before downloading files.

    And exists with error (2) if OSError exception is raised.
    """
    mock = mocker.patch("pathlib.Path.write_text")
    mock.side_effect = OSError(666, "Some message about exception.")

    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )

    result = run_cli_with_args(["download", "--last", "-q", "-d", f"{tmp_path}"])

    assert (
        "Invalid value for '--dest' / '-d': Some message about exception."
        in result.output
    )
    assert result.exit_code == 2


def test_passing_options_from_group_to_command(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    mp3_file1_mock: bytes,
    tmp_path: Path,
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It passes options to 'download' command from command group (script itself)."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    # Note: URL for #36 not for #35 (because it is 'duplicated' episode)
    requests_mock.get(
        "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )

    run_cli_with_args(["-ep", "35", "-q", "-d", f"{tmp_path}"])

    expected_filename_1 = "[2010-03-25] # 35. London Video Interviews – Part 1 (Video).mp3"  # noqa: E501,B950
    expected_file_1 = tmp_path / expected_filename_1
    assert len(list(tmp_path.iterdir())) == 1
    # assert len(LepDL.downloaded) == 1
    # assert len(LepDL.not_found) == 0
    assert expected_file_1.exists()


def test_final_prompt_to_press_enter(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    mp3_file1_mock: bytes,
    tmp_path: Path,
    runner: CliRunner,
) -> None:
    """It requires to press enter at the end of script execution."""
    from lep_downloader import cli

    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )

    requests_mock.get(
        "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )

    result = runner.invoke(
        cli.cli,
        ["-ep", "35", "-d", f"{tmp_path}"],
        prog_name="lep-downloader",
        input="\n",  # Two inputs in this case.
    )
    assert "Do you want to continue? [y/N]: \n" in result.output
    # assert len(LepDL.downloaded) == 0
    # assert len(LepDL.not_found) == 0
    assert "Press 'Enter' key to close 'LEP-downloader':" in result.output
    assert result.exit_code == 0
