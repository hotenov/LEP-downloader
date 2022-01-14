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

import pytest
from pytest import CaptureFixture
from requests_mock.mocker import Mocker as rm_Mocker

from lep_downloader import config as conf
from lep_downloader import downloader
from lep_downloader.downloader import Audio
from lep_downloader.downloader import Downloader
from lep_downloader.downloader import LepFile
from lep_downloader.downloader import LepFileList
from lep_downloader.downloader import PagePDF
from lep_downloader.exceptions import EmptyDownloadsBunch
from lep_downloader.exceptions import NoEpisodesInDataBase
from lep_downloader.lep import Lep
from lep_downloader.lep import LepEpisode
from lep_downloader.lep import LepEpisodeList


def test_selecting_only_audio_episodes(
    only_audio_episodes: List[LepEpisode],
) -> None:
    """It returns filtered list with only audio episodes."""
    assert len(only_audio_episodes) == 14  # Withoud duplicates


def test_extracting_audio_data(
    only_audio_episodes: LepEpisodeList,
) -> None:
    """It returns list of Audio files."""
    Downloader.files = LepFileList()
    expected_audio = Audio(
        ep_id=2009101908,  # many posts in that day
        name="15. Extra Podcast – 12 Phrasal Verbs",
        short_date="2009-10-19",
        filename="[2009-10-19] # 15. Extra Podcast – 12 Phrasal Verbs",
        primary_url="http://traffic.libsyn.com/teacherluke/15-extra-podcast-12-phrasal-verbs.mp3",  # noqa: E501,B950
    )
    # expected_ep = (
    #     "2009-10-19",
    #     "15. Extra Podcast – 12 Phrasal Verbs",  # noqa: E501,B950  # dash as Unicode character here.
    #     [
    #         [
    #             "http://traffic.libsyn.com/teacherluke/15-extra-podcast-12-phrasal-verbs.mp3"  # noqa: E501,B950
    #         ]
    #     ],
    #     False,
    # )
    # audio_data = downloader.get_audios_data(only_audio_episodes)
    downloader.gather_all_files(only_audio_episodes)
    audio_files = Downloader.files.filter_by_type(Audio)
    # Downloader.files = only_audio
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
) -> None:
    """It detects when file has already been downloaded."""
    filename_1 = "[2021-08-03] # 733. A Summer Ramble.mp3"
    filename_2 = "[2017-03-11] # LEP on ZEP – My recent interview on Zdenek’s English Podcast [Part 05].mp3"  # noqa: E501,B950
    Path(tmp_path / filename_1).write_text("Here are mp3 1 bytes")
    Path(tmp_path / filename_2).write_text("Here are mp3 2 bytes")

    # existing, non_existing = downloader.detect_existing_files(
    #     only_audio_links,
    #     tmp_path,
    # )
    Lep.db_episodes = LepEpisodeList()
    Downloader.files = LepFileList()
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    downloader.use_or_get_db_episodes(conf.JSON_DB_URL)
    downloader.gather_all_files(Lep.db_episodes)
    audio_files = Downloader.files.filter_by_type(Audio)
    downloader.detect_existing_files(audio_files, tmp_path)
    assert len(Downloader.existed) == 2
    assert len(Downloader.non_existed) == 16


def test_retrieving_audios_as_none() -> None:
    """It sets None to empty list and skip it."""
    Downloader.files = LepFileList()
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
    # audio_data = downloader.get_audios_data(db_episodes)
    # Check that 'empty' files (lists) are ignored.
    downloader.gather_all_files(db_episodes)
    # assert audio_data[0][2] == []
    assert len(Downloader.files) == 1
    assert isinstance(Downloader.files[0], PagePDF)


def test_downloading_mocked_mp3_files(
    requests_mock: rm_Mocker,
    mp3_file1_mock: bytes,
    mp3_file2_mock: bytes,
    tmp_path: Path,
) -> None:
    """It downloads file on disc."""
    # test_downloads: List[Tuple[str, List[str]]] = []
    test_downloads: LepFileList = LepFileList()
    # file_1 = (
    #     "Test File #1",
    #     [
    #         "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3"  # noqa: E501,B950
    #     ],
    # )
    # file_2 = (
    #     "Test File #2",
    #     [
    #         "https://audioboom.com/posts/5678762-episode-169-luke-back-on-zep-part-4.mp3"  # noqa: E501,B950
    #     ],
    # )
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

    Downloader.downloaded = LepFileList()
    downloader.download_files(test_downloads, tmp_path)
    expected_file_1 = tmp_path / "Test File #1.mp3"
    expected_file_2 = tmp_path / "Test File #2.mp3"
    assert expected_file_1.exists()
    assert 21460 < expected_file_1.stat().st_size < 22000
    assert expected_file_2.exists()
    assert 18300 < expected_file_2.stat().st_size < 18350
    # assert len(downloader.successful_downloaded) == 2
    assert len(Downloader.downloaded) == 2


# def test_skipping_downloaded_url(
#     requests_mock: rm_Mocker,
#     mp3_file1_mock: bytes,
#     mp3_file2_mock: bytes,
#     tmp_path: Path,
# ) -> None:
#     """It skips URL if it was downloaded before."""
#     test_downloads: List[Tuple[str, List[str]]] = []
#     file_1 = (
#         "Test File #1",
#         [
#             "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3"  # noqa: E501,B950
#         ],
#     )
#     file_2 = (
#         "Test File #2",
#         [
#             "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3"  # noqa: E501,B950
#         ],
#     )
#     test_downloads.append(file_1)
#     test_downloads.append(file_2)

#     requests_mock.get(
#         "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3",  # noqa: E501,B950
#         content=mp3_file1_mock,
#     )
#     requests_mock.get(
#         "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3",  # noqa: E501,B950
#         content=mp3_file2_mock,
#     )

#     downloader.download_files(test_downloads, tmp_path)
#     expected_file_1 = tmp_path / "Test File #1.mp3"
#     assert expected_file_1.exists()
#     assert len(list(tmp_path.iterdir())) == 1
#     assert len(downloader.duplicated_links) == 1


def test_skipping_downloaded_file_on_disc(
    requests_mock: rm_Mocker,
    mp3_file1_mock: bytes,
    mp3_file2_mock: bytes,
    tmp_path: Path,
) -> None:
    """It skips (and does not override) URL if file was downloaded before."""
    Downloader.downloaded = LepFileList()  # Clear from previous tests
    Downloader.existed = LepFileList()
    # test_downloads: List[Tuple[str, List[str]]] = []
    test_downloads: LepFileList = LepFileList()
    # file_1 = (
    #     "Test File #1",
    #     [
    #         "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3"  # noqa: E501,B950
    #     ],
    # )
    # file_2 = (
    #     "Test File #2",
    #     [
    #         "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3"  # noqa: E501,B950
    #     ],
    # )
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

    existing_file_1 = tmp_path / "Test File #1.mp3"
    existing_file_1.write_text("Here are mp3 1 bytes")
    downloader.download_files(test_downloads, tmp_path)
    expected_file_2 = tmp_path / "Test File #2.mp3"
    assert existing_file_1.read_text() == "Here are mp3 1 bytes"
    assert expected_file_2.exists()
    assert len(list(tmp_path.iterdir())) == 2
    # assert len(downloader.already_on_disc) == 1
    assert len(Downloader.existed) == 1


def test_try_auxiliary_download_links(
    requests_mock: rm_Mocker,
    mp3_file1_mock: bytes,
    tmp_path: Path,
) -> None:
    """It downloads file by auxiliary link."""
    Downloader.downloaded = LepFileList()  # Clear from previous tests
    # test_downloads: List[Tuple[str, List[str]]] = []
    test_downloads: LepFileList = LepFileList()
    # file_1 = (
    #     "Test File #1",
    #     [
    #         "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
    #         "https://hotenov.com/d/lep/some_auxiliary_1.mp3",
    #         "https://hotenov.com/d/lep/some_auxiliary_2.mp3",
    #     ],
    # )
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

    downloader.download_files(test_downloads, tmp_path)
    expected_file_1 = tmp_path / "Test File #1.mp3"
    assert expected_file_1.exists()
    assert len(list(tmp_path.iterdir())) == 1
    # assert len(downloader.successful_downloaded) == 1
    assert len(Downloader.downloaded) == 1


def test_primary_link_unavailable(
    requests_mock: rm_Mocker,
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    """It records unavailable file and prints about that."""
    Downloader.downloaded = LepFileList()  # Clear from previous tests
    Downloader.not_found = LepFileList()
    # test_downloads: List[Tuple[str, List[str]]] = []
    test_downloads: LepFileList = LepFileList()
    # file_1 = (
    #     "Test File #1",
    #     [
    #         "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
    #     ],
    # )
    file_1 = LepFile(
        filename="Test File #1.mp3",
        primary_url="https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
    )
    test_downloads.append(file_1)

    requests_mock.get(
        "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
        exc=Exception("Something wrong!"),
    )

    downloader.download_files(test_downloads, tmp_path)
    captured = capsys.readouterr()
    assert len(list(tmp_path.iterdir())) == 0
    # assert len(downloader.successful_downloaded) == 0
    # assert len(downloader.unavailable_links) == 1
    assert len(Downloader.downloaded) == 0
    assert len(Downloader.not_found) == 1
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
    Downloader.downloaded = LepFileList()  # Clear from previous tests
    Downloader.not_found = LepFileList()
    # test_downloads: List[Tuple[str, List[str]]] = []
    test_downloads: LepFileList = LepFileList()
    # file_1 = (
    #     "Test File #1",
    #     [
    #         "https://traffic.libsyn.com/secure/teacherluke/733._A_Summer_Ramble.mp3",  # noqa: E501,B950
    #         "https://hotenov.com/d/lep/some_auxiliary_1.mp3",
    #     ],
    # )
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

    downloader.download_files(test_downloads, tmp_path)
    captured = capsys.readouterr()
    assert len(list(tmp_path.iterdir())) == 0
    # assert len(downloader.successful_downloaded) == 0
    # assert len(downloader.unavailable_links) == 1
    assert len(Downloader.downloaded) == 0
    assert len(Downloader.not_found) == 1
    assert "[INFO]: Can't download:" in captured.out
    assert "Test File #1.mp3" in captured.out


def test_gathering_audio_files(
    requests_mock: rm_Mocker,
    json_db_mock: str,
) -> None:
    """It gets all audio files from mocked episodes."""
    Lep.db_episodes = LepEpisodeList()
    Downloader.files = LepFileList()
    requests_mock.get(
        conf.JSON_DB_URL,
        text=json_db_mock,
    )
    downloader.use_or_get_db_episodes(conf.JSON_DB_URL)
    # downloader.construct_audio_links_bunch()
    downloader.gather_all_files(Lep.db_episodes)
    audio_files = Downloader.files.filter_by_type(Audio)
    # got_files = Downloader.files
    assert len(audio_files) == 18


def test_collecting_auxiliary_audio_links() -> None:
    """It collects secondary and tertiary links as well."""
    Downloader.files = LepFileList()
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
    downloader.gather_all_files(db_episodes)
    assert len(Downloader.files) == 3
    assert Downloader.files[0].secondary_url == "https://someurl2.local"
    assert Downloader.files[0].tertiary_url == "https://someurl3.local"
    assert Downloader.files[1].secondary_url == "https://part2-someurl2.local"


def test_using_db_episodes_after_parsing() -> None:
    """It uses database episodes retrieved during parsing stage."""
    Lep.db_episodes = LepEpisodeList()
    Downloader.files = LepFileList()
    ep_1 = LepEpisode()
    ep_1.index = 2022011101
    ep_1.episode = 888
    ep_1.post_title = "888. Some title."
    ep_1._short_date = "2022-01-11"
    ep_1.post_type = "AUDIO"
    ep_1.files = {
        "audios": [
            [
                "https://someurl1.local",
                "https://someurl2.local",
                "https://someurl3.local",
            ]
        ],
        "page_pdf": [],
    }
    Lep.db_episodes.append(ep_1)
    downloader.use_or_get_db_episodes(conf.JSON_DB_URL)
    downloader.gather_all_files(Lep.db_episodes)
    # audio_files = Downloader.files.filter_by_type(Audio)
    assert len(Downloader.files) == 2  # + 1 PDF file
    assert Downloader.files[0].primary_url == "https://someurl1.local"
    assert Downloader.files[0].filename == "[2022-01-11] # 888. Some title..mp3"


def test_no_valid_episodes_in_database(requests_mock: rm_Mocker) -> None:
    """It raises exception if there are no valid episodes in JSON file."""
    Lep.db_episodes = LepEpisodeList()
    Downloader.files = LepFileList()
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
    downloader.use_or_get_db_episodes(conf.JSON_DB_URL)
    with pytest.raises(NoEpisodesInDataBase) as ex:
        downloader.gather_all_files(Lep.db_episodes)
    assert "No episodes for gathering files. Exit." in ex.value.args[0]


def test_processing_empty_downloads_bunch(
    requests_mock: rm_Mocker,
    json_db_mock: str,
) -> None:
    """It raises EmptyDownloadsBunch when nothing to download."""
    Lep.db_episodes = LepEpisodeList()
    Downloader.files = LepFileList()
    with pytest.raises(EmptyDownloadsBunch) as ex:
        downloader.download_files(
            Downloader.files,
            Path(),
        )
    assert "Nothing to download in downloads bunch." in ex.value.message


def test_populating_secondary_url() -> None:
    """It populates secondary links for empty values."""
    Downloader.files = LepFileList()
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
    downloader.gather_all_files(db_episodes)
    downloader.populate_default_url()
    assert len(Downloader.files) == 5
    assert (
        Downloader.files[0].secondary_url
        == "https://hotenov.com/d/lep/%5B2013-06-17%5D%20%23%20135.%20Raining%C2%A0Animals.mp3"  # noqa: E501,B950
    )
    assert (
        Downloader.files[2].secondary_url
        == "https://hotenov.com/d/lep/%5B2000-01-01%5D%20%23%203.%20Music/The%20Beatles%20%5BPart%2001%5D.mp3"  # noqa: E501,B950
    )
    assert Downloader.files[2].tertiary_url == "https://someurl3.local"
    assert Downloader.files[3].secondary_url == "https://part2-someurl2.local"


def test_gathering_page_pdf_urls() -> None:
    """It gatheres pdf links if they are provided in JSON."""
    Downloader.files = LepFileList()
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
    downloader.gather_all_files(db_episodes)

    assert len(Downloader.files) == 3

    assert Downloader.files[0].primary_url == "https://someurl553.local1"
    assert Downloader.files[0].secondary_url == "https://someurl553.local2"
    assert Downloader.files[0].tertiary_url == "https://someurl553.local3"

    assert Downloader.files[1].primary_url == "https://someurl554.local1"
    assert Downloader.files[1].secondary_url == "https://someurl554.local2"

    assert Downloader.files[2].primary_url == "https://someurl555.local"
    assert Downloader.files[2].secondary_url == ""
