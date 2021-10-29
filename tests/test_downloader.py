"""Test cases for the downloader module."""
from pathlib import Path
import tempfile

from lep_downloader.data_getter import get_list_of_valid_episodes
from lep_downloader import downloader as downloader


# TODO: Duplicated code (move to conftest.py)
OFFLINE_HTML_DIR = Path(
    Path(__file__).resolve().parent,
    "fixtures",
)

local_path = OFFLINE_HTML_DIR / "mocked-db-json-equal-786-objects.json"
MOCKED_JSON_DB = local_path.read_text(encoding="utf-8")
MOCKED_DB_EPISODES = get_list_of_valid_episodes(MOCKED_JSON_DB)


def test_selecting_only_audio_episodes() -> None:
    """It returns filtered list with only audio episodes."""
    audio_episodes = downloader.select_all_audio_episodes(MOCKED_DB_EPISODES)
    assert len(audio_episodes) == 15


def test_extracting_audio_data() -> None:
    """It returns list of tuples with audio data."""
    audio_episodes = downloader.select_all_audio_episodes(MOCKED_DB_EPISODES)
    # expected_ep_1 = [
    #     "2009-04-12",
    #     1,
    #     "1. Introduction",
    #     [["http://traffic.libsyn.com/teacherluke/1-introduction.mp3"]],
    #     False,
    # ]
    expected_ep = [
        "2009-10-19",
        "15. Extra Podcast – 12 Phrasal Verbs",  # dash as Unicode character here.
        [
            [
                "http://traffic.libsyn.com/teacherluke/15-extra-podcast-12-phrasal-verbs.mp3"
            ]
        ],
        False,
    ]
    audio_data = downloader.get_audios_data(audio_episodes)
    # assert audio_data[0] == expected_ep_1
    assert audio_data[1] == expected_ep


def test_forming_multipart_download_links() -> None:
    """It returns list of URLs with titles for files."""
    audio_episodes = downloader.select_all_audio_episodes(MOCKED_DB_EPISODES)
    audio_data = downloader.get_audios_data(audio_episodes)
    audio_links = downloader.bind_name_and_file_url(audio_data)
    excepted_link = (
        "[2017-03-11] # LEP on ZEP – My recent interview on Zdenek’s English Podcast [Part 02]",
        [
            "https://audioboom.com/posts/5621870-episode-167-luke-back-on-zep-part-2.mp3",
        ],
    )
    assert audio_links[11] == excepted_link


def test_forming_numbered_download_link() -> None:
    """It returns list of URLs with titles for files."""
    audio_episodes = downloader.select_all_audio_episodes(MOCKED_DB_EPISODES)
    audio_data = downloader.get_audios_data(audio_episodes)
    audio_links = downloader.bind_name_and_file_url(audio_data)
    excepted_link = (
        "[2021-02-03] # 703. Walaa from Syria – WISBOLEP Competition Winner",
        [
            "https://traffic.libsyn.com/secure/teacherluke/703._Walaa_from_Syria_-_WISBOLEP_Competition_Winner_.mp3",
        ],
    )
    assert audio_links[15] == excepted_link


def test_forming_safe_filename_for_downloading() -> None:
    """It replaces invalid path characters with '_'."""
    audio_episodes = downloader.select_all_audio_episodes(MOCKED_DB_EPISODES)
    audio_data = downloader.get_audios_data(audio_episodes)
    audio_links = downloader.bind_name_and_file_url(audio_data)
    excepted_link = (
        "[2016-08-07] # 370. In Conversation with Rob Ager from Liverpool (PART 1_ Life in Liverpool _ Interest in Film Analysis)",
        [
            "http://traffic.libsyn.com/teacherluke/370-in-conversation-with-rob-ager-from-liverpool-part-1-life-in-liverpool-interest-in-film-analysis.mp3",
        ],
    )
    assert audio_links[9] == excepted_link


def test_separating_existing_and_non_existing_mp3() -> None:
    """It detects when file has already been downloaded."""
    audio_episodes = downloader.select_all_audio_episodes(MOCKED_DB_EPISODES)
    audio_data = downloader.get_audios_data(audio_episodes)
    audio_links = downloader.bind_name_and_file_url(audio_data)

    filename_1 = "[2021-08-03] # 733. A Summer Ramble.mp3"
    filename_2 = "[2017-03-11] # LEP on ZEP – My recent interview on Zdenek’s English Podcast [Part 05].mp3"
    with tempfile.TemporaryDirectory(prefix="LEP_save_") as temp_dir:
        save_tmp_dir = Path(temp_dir)
        Path(save_tmp_dir / filename_1).write_text("Here are mp3 1 bytes")
        Path(save_tmp_dir / filename_2).write_text("Here are mp3 2 bytes")

        existing, non_existing = downloader.detect_existing_files(
            audio_links,
            save_tmp_dir,
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
    """
    db_episodes = get_list_of_valid_episodes(json_test)
    audio_data = downloader.get_audios_data(db_episodes)
    assert audio_data[0][2] == []
