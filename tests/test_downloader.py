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
"""Test cases for the downloader module."""
from pathlib import Path
from typing import List
from typing import Tuple

from pytest import CaptureFixture
from requests_mock.mocker import Mocker as rm_Mocker

from lep_downloader import data_getter
from lep_downloader import downloader
from lep_downloader.lep import LepEpisode


def test_selecting_only_audio_episodes(
    only_audio_episodes: List[LepEpisode],
) -> None:
    """It returns filtered list with only audio episodes."""
    assert len(only_audio_episodes) == 15


def test_extracting_audio_data(
    only_audio_episodes: List[LepEpisode],
) -> None:
    """It returns list of tuples with audio data."""
    expected_ep = (
        "2009-10-19",
        "15. Extra Podcast – 12 Phrasal Verbs",  # noqa: E501,B950  # dash as Unicode character here.
        [
            [
                "http://traffic.libsyn.com/teacherluke/15-extra-podcast-12-phrasal-verbs.mp3"  # noqa: E501,B950
            ]
        ],
        False,
    )
    audio_data = downloader.get_audios_data(only_audio_episodes)
    assert audio_data[1] == expected_ep


def test_forming_multipart_download_links(
    only_audio_links: downloader.NamesWithAudios,
) -> None:
    """It returns list of URLs with titles for files."""
    excepted_link = (
        "[2017-03-11] # LEP on ZEP – My recent interview on Zdenek’s English Podcast [Part 02]",  # noqa: E501,B950
        [
            "https://audioboom.com/posts/5621870-episode-167-luke-back-on-zep-part-2.mp3",  # noqa: E501,B950
        ],
    )
    assert only_audio_links[11] == excepted_link


def test_forming_numbered_download_link(
    only_audio_links: downloader.NamesWithAudios,
) -> None:
    """It returns list of URLs with titles for files."""
    excepted_link = (
        "[2021-02-03] # 703. Walaa from Syria – WISBOLEP Competition Winner",
        [
            "https://traffic.libsyn.com/secure/teacherluke/703._Walaa_from_Syria_-_WISBOLEP_Competition_Winner_.mp3",  # noqa: E501,B950
        ],
    )
    assert only_audio_links[15] == excepted_link


def test_forming_safe_filename_for_downloading(
    only_audio_links: downloader.NamesWithAudios,
) -> None:
    """It replaces invalid path characters with '_'."""
    excepted_link = (
        "[2016-08-07] # 370. In Conversation with Rob Ager from Liverpool (PART 1_ Life in Liverpool _ Interest in Film Analysis)",  # noqa: E501,B950
        [
            "http://traffic.libsyn.com/teacherluke/370-in-conversation-with-rob-ager-from-liverpool-part-1-life-in-liverpool-interest-in-film-analysis.mp3",  # noqa: E501,B950
        ],
    )
    assert only_audio_links[9] == excepted_link


def test_separating_existing_and_non_existing_mp3(
    only_audio_links: downloader.NamesWithAudios,
    tmp_path: Path,
) -> None:
    """It detects when file has already been downloaded."""
    filename_1 = "[2021-08-03] # 733. A Summer Ramble.mp3"
    filename_2 = "[2017-03-11] # LEP on ZEP – My recent interview on Zdenek’s English Podcast [Part 05].mp3"  # noqa: E501,B950
    Path(tmp_path / filename_1).write_text("Here are mp3 1 bytes")
    Path(tmp_path / filename_2).write_text("Here are mp3 2 bytes")

    existing, non_existing = downloader.detect_existing_files(
        only_audio_links,
        tmp_path,
    )
    assert len(existing) == 2
    assert len(non_existing) == 17


def test_retrieving_audios_as_none() -> None:
    """It replaces None to empty list."""
    json_test = """\
        [
            {
                "episode": 3,
                "date": "2000-01-01T00:00:00+00:00",
                "url": "https://teacherluke.co.uk/2009/04/15/episode-3-musicthe-beatles/",
                "post_title": "3. Music/The Beatles",
                "post_type": "",
                "audios": null,
                "parsing_utc": "2021-10-14T07:35:24.575575Z",
                "index": 2009041501,
                "admin_note": "Edge case - null in 'audios'"
            }
        ]
    """  # noqa: E501,B950
    db_episodes = data_getter.get_list_of_valid_episodes(json_test)
    audio_data = downloader.get_audios_data(db_episodes)
    assert audio_data[0][2] == []


def test_downloading_mocked_mp3_files(
    requests_mock: rm_Mocker,
    mp3_file1_mock: bytes,
    mp3_file2_mock: bytes,
    tmp_path: Path,
) -> None:
    """It downloads file on disc."""
    test_downloads: List[Tuple[str, List[str]]] = []
    file_1 = (
        "Test File #1",
        [
            "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3"  # noqa: E501,B950
        ],
    )
    file_2 = (
        "Test File #2",
        [
            "https://audioboom.com/posts/5678762-episode-169-luke-back-on-zep-part-4.mp3"  # noqa: E501,B950
        ],
    )
    test_downloads.append(file_1)
    test_downloads.append(file_2)

    requests_mock.get(
        "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )
    requests_mock.get(
        "https://audioboom.com/posts/5678762-episode-169-luke-back-on-zep-part-4.mp3",  # noqa: E501,B950
        content=mp3_file2_mock,
    )

    downloader.download_files(test_downloads, tmp_path)
    expected_file_1 = tmp_path / "Test File #1.mp3"
    expected_file_2 = tmp_path / "Test File #2.mp3"
    assert expected_file_1.exists()
    assert 21460 < expected_file_1.stat().st_size < 22000
    assert expected_file_2.exists()
    assert 18300 < expected_file_2.stat().st_size < 18350
    assert len(downloader.successful_downloaded) == 2


def test_skipping_downloaded_url(
    requests_mock: rm_Mocker,
    mp3_file1_mock: bytes,
    mp3_file2_mock: bytes,
    tmp_path: Path,
) -> None:
    """It skips URL if it was downloaded before."""
    test_downloads: List[Tuple[str, List[str]]] = []
    file_1 = (
        "Test File #1",
        [
            "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3"  # noqa: E501,B950
        ],
    )
    file_2 = (
        "Test File #2",
        [
            "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3"  # noqa: E501,B950
        ],
    )
    test_downloads.append(file_1)
    test_downloads.append(file_2)

    requests_mock.get(
        "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )
    requests_mock.get(
        "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3",  # noqa: E501,B950
        content=mp3_file2_mock,
    )

    downloader.download_files(test_downloads, tmp_path)
    expected_file_1 = tmp_path / "Test File #1.mp3"
    assert expected_file_1.exists()
    assert len(list(tmp_path.iterdir())) == 1
    assert len(downloader.duplicated_links) == 1


def test_skipping_downloaded_file_on_disc(
    requests_mock: rm_Mocker,
    mp3_file1_mock: bytes,
    mp3_file2_mock: bytes,
    tmp_path: Path,
) -> None:
    """It skips (and does not override) URL if file was downloaded before."""
    downloader.successful_downloaded = {}  # Clear from previous tests
    test_downloads: List[Tuple[str, List[str]]] = []
    file_1 = (
        "Test File #1",
        [
            "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3"  # noqa: E501,B950
        ],
    )
    file_2 = (
        "Test File #2",
        [
            "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3"  # noqa: E501,B950
        ],
    )
    test_downloads.append(file_1)
    test_downloads.append(file_2)

    requests_mock.get(
        "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3",  # noqa: E501,B950
        content=mp3_file1_mock,
    )
    requests_mock.get(
        "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
        content=mp3_file2_mock,
    )

    existing_file_1 = tmp_path / "Test File #1.mp3"
    existing_file_1.write_text("Here are mp3 1 bytes")
    downloader.download_files(test_downloads, tmp_path)
    expected_file_2 = tmp_path / "Test File #2.mp3"
    assert existing_file_1.read_text() == "Here are mp3 1 bytes"
    assert expected_file_2.exists()
    assert len(list(tmp_path.iterdir())) == 2
    assert len(downloader.already_on_disc) == 1


def test_try_auxiliary_download_links(
    requests_mock: rm_Mocker,
    mp3_file1_mock: bytes,
    tmp_path: Path,
) -> None:
    """It downloads file by auxiliary link."""
    downloader.successful_downloaded = {}  # Clear from previous tests
    test_downloads: List[Tuple[str, List[str]]] = []
    file_1 = (
        "Test File #1",
        [
            "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
            "https://hotenov.com/d/lep/some_auxiliary_1.mp3",
            "https://hotenov.com/d/lep/some_auxiliary_2.mp3",
        ],
    )
    test_downloads.append(file_1)

    requests_mock.get(
        "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
        text="Response not OK",
        status_code=404,
    )
    requests_mock.get(
        "https://hotenov.com/d/lep/some_auxiliary_1.mp3",
        text="Response not OK",
        status_code=404,
    )
    requests_mock.get(
        "https://hotenov.com/d/lep/some_auxiliary_2.mp3",
        content=mp3_file1_mock,
    )

    downloader.download_files(test_downloads, tmp_path)
    expected_file_1 = tmp_path / "Test File #1.mp3"
    assert expected_file_1.exists()
    assert len(list(tmp_path.iterdir())) == 1
    assert len(downloader.successful_downloaded) == 1


def test_primary_link_unavailable(
    requests_mock: rm_Mocker,
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    """It records unavailable file and prints about that."""
    downloader.successful_downloaded = {}  # Clear from previous tests
    downloader.unavailable_links = {}
    test_downloads: List[Tuple[str, List[str]]] = []
    file_1 = (
        "Test File #1",
        [
            "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
        ],
    )
    test_downloads.append(file_1)

    requests_mock.get(
        "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
        exc=Exception("Something wrong!"),
    )

    downloader.download_files(test_downloads, tmp_path)
    captured = capsys.readouterr()
    assert len(list(tmp_path.iterdir())) == 0
    assert len(downloader.successful_downloaded) == 0
    assert len(downloader.unavailable_links) == 1
    assert "[ERROR]: Unknown error:" in captured.out
    assert "Something wrong!" in captured.out
    assert "[INFO]: Can't download:" in captured.out
    assert "Test File #1.mp3" in captured.out


def test_both_primary_and_auxiliary_links_404(
    requests_mock: rm_Mocker,
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    """It records unavailable files and prints about that."""
    downloader.successful_downloaded = {}  # Clear from previous tests
    downloader.unavailable_links = {}
    test_downloads: List[Tuple[str, List[str]]] = []
    file_1 = (
        "Test File #1",
        [
            "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
            "https://hotenov.com/d/lep/some_auxiliary_1.mp3",
        ],
    )
    test_downloads.append(file_1)

    requests_mock.get(
        "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
        text="Response not OK",
        status_code=404,
    )
    requests_mock.get(
        "https://hotenov.com/d/lep/some_auxiliary_1.mp3",
        text="Response not OK",
        status_code=404,
    )

    downloader.download_files(test_downloads, tmp_path)
    captured = capsys.readouterr()
    assert len(list(tmp_path.iterdir())) == 0
    assert len(downloader.successful_downloaded) == 0
    assert len(downloader.unavailable_links) == 1
    assert "[INFO]: Can't download:" in captured.out
    assert "Test File #1.mp3" in captured.out
