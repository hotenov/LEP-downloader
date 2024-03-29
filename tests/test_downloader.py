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

from lep_downloader import config as conf
from lep_downloader import downloader
from lep_downloader.downloader import ATrack
from lep_downloader.downloader import Audio
from lep_downloader.downloader import LepDL
from lep_downloader.downloader import LepFile
from lep_downloader.downloader import LepFileList
from lep_downloader.downloader import PagePDF
from lep_downloader.lep import Lep
from lep_downloader.lep import LepEpisode
from lep_downloader.lep import LepEpisodeList


def test_selecting_only_audio_episodes(
    only_audio_episodes: List[LepEpisode],
) -> None:
    """It returns filtered list with only audio episodes."""
    assert len(only_audio_episodes) == 14  # Without duplicates


def test_extracting_audio_data(
    only_audio_episodes: LepEpisodeList,
    lep_dl: LepDL,
) -> None:
    """It returns list of Audio files."""
    expected_audio = Audio(
        ep_id=2009101908,  # many posts in that day
        name="15. Extra Podcast – 12 Phrasal Verbs",
        short_date="2009-10-19",
        filename="[2009-10-19] # 15. Extra Podcast – 12 Phrasal Verbs",
        primary_url="http://traffic.libsyn.com/teacherluke/15-extra-podcast-12-phrasal-verbs.mp3",  # noqa: E501,B950
    )
    lep_dl.files = downloader.gather_all_files(only_audio_episodes)
    audio_files = lep_dl.files.filter_by_type(Audio)
    assert audio_files[1] == expected_audio


def test_forming_multipart_download_links(
    only_audio_links: List[Tuple[str, str]],
) -> None:
    """It returns list of URLs with titles for multipart episode."""
    excepted_link = (
        "[2017-03-11] # LEP on ZEP – My recent interview on Zdenek’s English Podcast [Part 02].mp3",  # noqa: E501,B950
        "https://audioboom.com/posts/5621870-episode-167-luke-back-on-zep-part-2.mp3",  # noqa: E501,B950
    )
    assert only_audio_links[10] == excepted_link


def test_forming_numbered_download_link(
    only_audio_links: List[Tuple[str, str]],
) -> None:
    """It returns list of URLs with titles for files."""
    excepted_link = (
        "[2021-02-03] # 703. Walaa from Syria – WISBOLEP Competition Winner.mp3",
        "https://traffic.libsyn.com/secure/teacherluke/703._Walaa_from_Syria_-_WISBOLEP_Competition_Winner_.mp3",  # noqa: E501,B950
    )
    assert only_audio_links[14] == excepted_link


def test_forming_safe_filename_for_downloading(
    only_audio_links: List[Tuple[str, str]],
) -> None:
    """It replaces invalid path characters with '_'."""
    excepted_link = (
        "[2016-08-07] # 370. In Conversation with Rob Ager from Liverpool (PART 1_ Life in Liverpool _ Interest in Film Analysis).mp3",  # noqa: E501,B950
        "http://traffic.libsyn.com/teacherluke/370-in-conversation-with-rob-ager-from-liverpool-part-1-life-in-liverpool-interest-in-film-analysis.mp3",  # noqa: E501,B950
    )
    assert only_audio_links[8] == excepted_link


def test_separating_existing_and_non_existing_mp3(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    tmp_path: Path,
    lep_dl: LepDL,
) -> None:
    """It detects when file has already been downloaded."""
    filename_1 = "[2021-08-03] # 733. A Summer Ramble.mp3"
    filename_2 = "[2017-03-11] # LEP on ZEP – My recent interview on Zdenek’s English Podcast [Part 05].mp3"  # noqa: E501,B950
    Path(tmp_path / filename_1).write_text("Here are mp3 1 bytes")
    Path(tmp_path / filename_2).write_text("Here are mp3 2 bytes")

    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    lep_dl.get_remote_episodes()
    lep_dl.files = downloader.gather_all_files(lep_dl.db_episodes)
    audio_files = lep_dl.files.filter_by_type(Audio)
    lep_dl.detach_existed_files(tmp_path, audio_files)
    assert len(lep_dl.existed) == 2
    assert len(lep_dl.non_existed) == 16


def test_retrieving_audios_as_none(
    lep_dl: LepDL,
) -> None:
    """It sets None to empty list and skip it."""
    json_test = """\
        [
            {
                "episode": 3,
                "date": "2000-01-01T00:00:00+00:00",
                "url": "https://teacherluke.co.uk/2009/04/15/episode-3-musicthe-beatles/",
                "post_title": "3. Music/The Beatles",
                "post_type": "",
                "files": {
                    "audios": null,
                    "page_pdf": []
                },
                "parsed_at": "2021-10-14T07:35:24.575575Z",
                "index": 2009041501,
                "admin_note": "Edge case - null in 'audios'"
            }
        ]
    """  # noqa: E501,B950
    db_episodes = Lep.extract_only_valid_episodes(json_test)
    db_episodes[0].files["audios"] = None
    # Check that 'empty' files (lists) are ignored.
    lep_dl.files = downloader.gather_all_files(db_episodes)
    assert len(lep_dl.files) == 1
    assert isinstance(lep_dl.files[0], PagePDF)


def test_downloading_mocked_mp3_files(
    requests_mock: rm_Mocker,
    mp3_file1_mock: bytes,
    mp3_file2_mock: bytes,
    tmp_path: Path,
    lep_dl: LepDL,
) -> None:
    """It downloads file on disc."""
    test_downloads: LepFileList = LepFileList()
    file_1 = LepFile(
        filename="Test File #1.mp3",
        primary_url="https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
    )
    file_2 = LepFile(
        filename="Test File #2.mp3",
        primary_url="https://audioboom.com/posts/5678762-episode-169-luke-back-on-zep-part-4.mp3",  # noqa: E501,B950
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

    lep_dl.non_existed = test_downloads
    lep_dl.download_files(tmp_path)
    expected_file_1 = tmp_path / "Test File #1.mp3"
    expected_file_2 = tmp_path / "Test File #2.mp3"
    assert expected_file_1.exists()
    assert 21460 < expected_file_1.stat().st_size < 22000
    assert expected_file_2.exists()
    assert 18300 < expected_file_2.stat().st_size < 18350
    assert len(lep_dl.downloaded) == 2


def test_skipping_downloaded_file_on_disc(
    requests_mock: rm_Mocker,
    mp3_file1_mock: bytes,
    mp3_file2_mock: bytes,
    tmp_path: Path,
    lep_dl: LepDL,
) -> None:
    """It skips (and does not override) URL if file was downloaded before."""
    test_downloads: LepFileList = LepFileList()
    file_1 = LepFile(
        filename="Test File #1.mp3",
        primary_url="http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3",  # noqa: E501,B950
    )
    file_2 = LepFile(
        filename="Test File #2.mp3",
        primary_url="https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
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

    lep_dl.files = test_downloads
    lep_dl.detach_existed_files(tmp_path)
    existing_file_1 = tmp_path / "Test File #1.mp3"
    existing_file_1.write_text("Here are mp3 1 bytes")
    lep_dl.download_files(tmp_path)
    expected_file_2 = tmp_path / "Test File #2.mp3"
    assert existing_file_1.read_text() == "Here are mp3 1 bytes"
    assert expected_file_2.exists()
    assert len(list(tmp_path.iterdir())) == 2
    assert len(lep_dl.existed) == 1


def test_try_auxiliary_download_links(
    requests_mock: rm_Mocker,
    mp3_file1_mock: bytes,
    tmp_path: Path,
    lep_dl: LepDL,
) -> None:
    """It downloads file by auxiliary link."""
    test_downloads: LepFileList = LepFileList()
    file_1 = LepFile(
        filename="Test File #1.mp3",
        primary_url="https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
        secondary_url="https://hotenov.com/d/lep/some_auxiliary_1.mp3",
        tertiary_url="https://hotenov.com/d/lep/some_auxiliary_2.mp3",
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

    lep_dl.files = test_downloads
    lep_dl.detach_existed_files(tmp_path)
    lep_dl.download_files(tmp_path)
    expected_file_1 = tmp_path / "Test File #1.mp3"
    assert expected_file_1.exists()
    assert len(list(tmp_path.iterdir())) == 1
    assert len(lep_dl.downloaded) == 1


def test_primary_link_unavailable(
    requests_mock: rm_Mocker,
    tmp_path: Path,
    capsys: CaptureFixture[str],
    lep_dl: LepDL,
) -> None:
    """It records unavailable file and prints about that."""
    test_downloads: LepFileList = LepFileList()
    file_1 = LepFile(
        filename="Test File #1.mp3",
        primary_url="https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
    )
    test_downloads.append(file_1)

    requests_mock.get(
        "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
        exc=Exception("Something wrong!"),
    )

    lep_dl.files = test_downloads
    lep_dl.detach_existed_files(tmp_path)
    lep_dl.download_files(tmp_path)
    # captured = capsys.readouterr()  # ONLY IN LOG NOW
    assert len(list(tmp_path.iterdir())) == 0
    assert len(lep_dl.downloaded) == 0
    assert len(lep_dl.not_found) == 1
    # assert "[ERROR]: Unknown error:" in captured.out
    # assert "Something wrong!" in captured.out
    # assert "[INFO]: Can't download:" in captured.out
    # assert " - [2021-08-03] # 733. A Summer Ramble.mp3" in captured.out
    # assert "Test File #1.mp3" in captured.out


def test_both_primary_and_auxiliary_links_404(
    requests_mock: rm_Mocker,
    tmp_path: Path,
    capsys: CaptureFixture[str],
    lep_dl: LepDL,
) -> None:
    """It records unavailable files and prints about that."""
    test_downloads: LepFileList = LepFileList()
    file_1 = LepFile(
        filename="Test File #1.mp3",
        primary_url="https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
        secondary_url="https://hotenov.com/d/lep/some_auxiliary_1.mp3",
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

    lep_dl.files = test_downloads
    lep_dl.detach_existed_files(tmp_path, lep_dl.files)
    lep_dl.download_files(tmp_path)
    # captured = capsys.readouterr()  # ONLY IN LOG NOW
    assert len(list(tmp_path.iterdir())) == 0
    assert len(lep_dl.downloaded) == 0
    assert len(lep_dl.not_found) == 1
    # assert "[INFO]: Can't download:" in captured.out
    # assert "Test File #1.mp3" in captured.out


def test_gathering_audio_files(
    requests_mock: rm_Mocker,
    json_db_mock: str,
    lep_dl: LepDL,
) -> None:
    """It gets all audio files from mocked episodes."""
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    lep_dl.get_remote_episodes()
    lep_dl.files = downloader.gather_all_files(lep_dl.db_episodes)
    audio_files = lep_dl.files.filter_by_type(Audio)
    assert len(audio_files) == 18


def test_collecting_auxiliary_audio_links(
    lep_dl: LepDL,
) -> None:
    """It collects secondary and tertiary links as well."""
    json_test = """\
        [
            {
                "episode": 3,
                "date": "2000-01-01T00:00:00+00:00",
                "url": "https://teacherluke.co.uk/2009/04/15/episode-3-musicthe-beatles/",
                "post_title": "3. Music/The Beatles",
                "post_type": "",
                "files": {
                    "audios": [
                        [
                            "https://someurl1.local", "https://someurl2.local", "https://someurl3.local"
                        ],
                        [
                            "https://part2-someurl1.local", "https://part2-someurl2.local"
                        ]
                    ],
                    "page_pdf": []
                },
                "parsed_at": "2021-10-14T07:35:24.575575Z",
                "index": 2009041501,
                "admin_note": "Edge case - null in 'audios'"
            }
        ]
    """  # noqa: E501,B950
    db_episodes = Lep.extract_only_valid_episodes(json_test)
    lep_dl.files = downloader.gather_all_files(db_episodes)
    assert len(lep_dl.files) == 3
    assert lep_dl.files[0].secondary_url == "https://someurl2.local"
    assert lep_dl.files[0].tertiary_url == "https://someurl3.local"
    assert lep_dl.files[1].secondary_url == "https://part2-someurl2.local"


def test_no_valid_episodes_in_database(
    requests_mock: rm_Mocker,
    lep_dl: LepDL,
) -> None:
    """It raises exception if there are no valid episodes in JSON file."""
    json_test = """\
        [
            {
                "episode_number": 666,
                "date": "2000-01-01T00:00:00+00:00",
                "url": "https://teacherluke.co.uk/2009/04/15/episode-3-musicthe-beatles/",
            }
        ]
    """  # noqa: E501,B950
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_test,
    )
    lep_dl.get_remote_episodes()
    lep_dl.files = downloader.gather_all_files(lep_dl.db_episodes)
    assert len(lep_dl.files) == 0
    # assert "No episodes for gathering files. Exit." in ex.value.args[0]


def test_populating_secondary_url(
    lep_dl: LepDL,
) -> None:
    """It populates secondary links for empty values."""
    json_test = """\
        [
            {
                "episode": 3,
                "date": "2000-01-01T00:00:00+00:00",
                "url": "https://teacherluke.co.uk/2009/04/15/episode-3-musicthe-beatles/",
                "post_title": "3. Music/The Beatles",
                "post_type": "",
                "files": {
                    "audios": [
                        [
                            "https://someurl1.local", "", "https://someurl3.local"
                        ],
                        [
                            "https://part2-someurl1.local", "https://part2-someurl2.local"
                        ]
                    ],
                    "page_pdf": []
                },
                "parsed_at": "2021-10-14T07:35:24.575575Z",
                "index": 2009041501,
                "admin_note": ""
            },
            {
                "episode": 135,
                "date": "2013-06-17T00:00:00+00:00",
                "url": "https://teacherluke.co.uk/2013/06/17/episode-3-musicthe-beatles/",
                "post_title": "135. Raining Animals",
                "post_type": "",
                "files": {
                    "audios": [
                        [
                            "https://someurl1.local135"
                        ]
                    ],
                    "page_pdf": []
                },
                "parsed_at": "2022-01-12T13:50:24.575575Z",
                "index": 2009041501,
                "admin_note": "default url for PDF"
            }
        ]
    """  # noqa: E501,B950
    db_episodes = Lep.extract_only_valid_episodes(json_test)
    lep_dl.files = downloader.gather_all_files(db_episodes)
    lep_dl.populate_default_url()
    assert len(lep_dl.files) == 5
    assert (
        lep_dl.files[0].secondary_url
        == "https://hotenov.com/d/lep/%5B2013-06-17%5D%20%23%20135.%20Raining%C2%A0Animals.mp3"  # noqa: E501,B950
    )
    assert (
        lep_dl.files[2].secondary_url
        == "https://hotenov.com/d/lep/%5B2000-01-01%5D%20%23%203.%20Music/The%20Beatles%20%5BPart%2001%5D.mp3"  # noqa: E501,B950
    )
    assert lep_dl.files[2].tertiary_url == "https://someurl3.local"
    assert lep_dl.files[3].secondary_url == "https://part2-someurl2.local"


def test_gathering_page_pdf_urls(
    lep_dl: LepDL,
) -> None:
    """It gatheres pdf links if they are provided in JSON."""
    json_test = """\
        [
            {
                "episode": 555,
                "files": {
                    "audios": [],
                    "page_pdf": ["https://someurl555.local"]
                },
                "index": 2022011303
            },
            {
                "episode": 554,
                "files": {
                    "audios": [],
                    "page_pdf": ["https://someurl554.local1", "https://someurl554.local2"]
                },
                "index": 2022011302
            },
            {
                "episode": 553,
                "files": {
                    "audios": [],
                    "page_pdf": [
                        "https://someurl553.local1",
                        "https://someurl553.local2",
                        "https://someurl553.local3"
                    ]
                },
                "index": 2022011302
            }
        ]
    """  # noqa: E501,B950
    db_episodes = Lep.extract_only_valid_episodes(json_test)
    lep_dl.files = downloader.gather_all_files(db_episodes)

    assert len(lep_dl.files) == 3

    assert lep_dl.files[0].primary_url == "https://someurl553.local1"
    assert lep_dl.files[0].secondary_url == "https://someurl553.local2"
    assert lep_dl.files[0].tertiary_url == "https://someurl553.local3"

    assert lep_dl.files[1].primary_url == "https://someurl554.local1"
    assert lep_dl.files[1].secondary_url == "https://someurl554.local2"

    assert lep_dl.files[2].primary_url == "https://someurl555.local"
    assert lep_dl.files[2].secondary_url == ""


def test_gathering_links_for_audio_track(
    lep_dl: LepDL,
) -> None:
    """It collects URLs for audio track."""
    json_test = """\
        [
            {
                "episode": 3,
                "date": "2000-01-01T00:00:00+00:00",
                "url": "https://teacherluke.co.uk/2009/04/15/episode-3-musicthe-beatles/",
                "post_title": "3. Music/The Beatles",
                "post_type": "",
                "files": {
                    "audios": [],
                    "atrack": [
                        [
                            "https://someurl1.local", "https://someurl2.local", "https://someurl3.local"
                        ]
                    ]
                },
                "parsed_at": "2021-10-14T07:35:24.575575Z",
                "index": 2009041501,
                "admin_note": "Check audio track."
            }
        ]
    """  # noqa: E501,B950
    db_episodes = Lep.extract_only_valid_episodes(json_test)
    lep_dl.files = downloader.gather_all_files(db_episodes)
    assert len(lep_dl.files) == 2
    assert lep_dl.files[0].primary_url == "https://someurl1.local"
    assert lep_dl.files[0].secondary_url == "https://someurl2.local"
    assert lep_dl.files[0].tertiary_url == "https://someurl3.local"
    assert isinstance(lep_dl.files[0], ATrack)
    assert (
        lep_dl.files[0].filename == "[2000-01-01] # 3. Music/The Beatles _aTrack_.mp3"
    )


def test_gathering_multi_part_audio_track(
    lep_dl: LepDL,
) -> None:
    """It collects multi-part audio track."""
    json_test = """\
        [
            {
                "episode": 3,
                "date": "2000-01-01T00:00:00+00:00",
                "url": "https://teacherluke.co.uk/2009/04/15/episode-3-musicthe-beatles/",
                "post_title": "3. Music/The Beatles",
                "post_type": "",
                "files": {
                    "audios": [],
                    "atrack": [
                        [
                            "https://someurl1.local", "https://someurl2.local", "https://someurl3.local"
                        ],
                        [
                            "https://part2-someurl1.local", "https://part2-someurl2.local"
                        ]
                    ]
                },
                "parsed_at": "2021-10-14T07:35:24.575575Z",
                "index": 2009041501,
                "admin_note": "Check audio track."
            }
        ]
    """  # noqa: E501,B950
    db_episodes = Lep.extract_only_valid_episodes(json_test)
    lep_dl.files = downloader.gather_all_files(db_episodes)
    assert len(lep_dl.files) == 3
    assert lep_dl.files[0].secondary_url == "https://someurl2.local"
    assert lep_dl.files[0].tertiary_url == "https://someurl3.local"
    assert lep_dl.files[1].secondary_url == "https://part2-someurl2.local"
    assert isinstance(lep_dl.files[0], ATrack)
    assert isinstance(lep_dl.files[1], ATrack)
    assert (
        lep_dl.files[0].filename
        == "[2000-01-01] # 3. Music/The Beatles [Part 01] _aTrack_.mp3"
    )
    assert (
        lep_dl.files[1].filename
        == "[2000-01-01] # 3. Music/The Beatles [Part 02] _aTrack_.mp3"
    )
