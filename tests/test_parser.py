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
"""Test cases for the parser module."""
import json
import typing as t
from pathlib import Path
from typing import Callable
from typing import List
from typing import Optional
from typing import Tuple

import pytest
import requests
import requests_mock as req_mock
from bs4 import BeautifulSoup
from pytest import CaptureFixture
from requests_mock.mocker import Mocker as rm_Mocker
from requests_mock.request import _RequestObjectProxy

from lep_downloader import config as conf
from lep_downloader import lep
from lep_downloader import parser
from lep_downloader.data_getter import get_web_page_html_text
from lep_downloader.lep import as_lep_episode_obj
from lep_downloader.lep import LepEpisode


lep_date_format = "%Y-%m-%dT%H:%M:%S%z"


def test_getting_success_page_response(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
) -> None:
    """It gets HTML content as text."""
    requests_mock.get(req_mock.ANY, text="Response OK")
    resp = get_web_page_html_text(conf.ARCHIVE_URL, req_ses)[0]
    assert resp == "Response OK"


def test_getting_404_page_response(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
) -> None:
    """It handles HTTPError if page is not found."""
    requests_mock.get(req_mock.ANY, text="Response OK", status_code=404)
    resp = get_web_page_html_text("http://example.com", req_ses)[0]
    assert "[ERROR]" in resp
    assert "404" in resp


def test_getting_503_page_response(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
) -> None:
    """It handle HTTPError if service is unavailable."""
    requests_mock.get(req_mock.ANY, text="Response OK", status_code=503)
    resp = get_web_page_html_text("http://example.com", req_ses)[0]
    assert "[ERROR]" in resp
    assert "503" in resp


def test_timeout_error(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
) -> None:
    """It handle any Timeout exception for page."""
    requests_mock.get(req_mock.ANY, exc=requests.exceptions.Timeout)
    resp = get_web_page_html_text("http://example.com", req_ses)[0]
    assert "[ERROR]" in resp
    assert "Timeout" in resp


def test_connection_error(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
) -> None:
    """It handles ConnectionError exception for bad request."""
    requests_mock.get(req_mock.ANY, exc=requests.exceptions.ConnectionError)
    resp = get_web_page_html_text("http://example.com", req_ses)[0]
    assert "[ERROR]" in resp
    assert "Bad request" in resp


def test_unknown_error(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
) -> None:
    """It handles any other exceptions during getting response from URL."""
    requests_mock.get(req_mock.ANY, exc=Exception("Something Bad"))
    resp = get_web_page_html_text("http://example.com", req_ses)[0]
    assert "[ERROR]" in resp
    assert "Unhandled error" in resp


def test_final_location_for_good_redirect(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
) -> None:
    """It retrieves final location during redirect."""
    requests_mock.get(
        "https://re.direct",
        text="Rederecting to...",
        status_code=301,
        headers={"Location": "https://final.location/"},
    )
    requests_mock.get("https://final.location", text="Final location")
    text, final_location, is_url_ok = get_web_page_html_text(
        "https://re.direct",
        req_ses,
    )
    assert is_url_ok
    assert text == "Final location"
    assert final_location == "https://final.location/"


def test_final_location_for_bad_redirect(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
) -> None:
    """It retrieves final location during redirect."""
    requests_mock.get(
        "https://re.direct",
        text="Rederecting to...",
        status_code=301,
        headers={"Location": "https://bad.final.location/"},
    )
    requests_mock.get(
        "https://bad.final.location/",
        text="Final location",
        status_code=404,
    )
    text, final_location, is_url_ok = get_web_page_html_text(
        "https://re.direct",
        req_ses,
    )
    assert not is_url_ok
    assert "[ERROR]" in text
    assert "bad.final.location" in text
    assert final_location == "https://bad.final.location/"


def test_retrieve_all_episode_links_from_soup() -> None:
    """It returns only <a> tags from soup object."""
    html_doc = """<html><head><title>The Dormouse'req_ses story</title></head>
        <article>
            <p class="title"><b>The Dormouse'req_ses story</b></p>
            <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="https://teacherluke.co.uk/2017/09/24/website-content-luke-on-the-real-life-english-podcast/" class="sister" id="link1">Elsie</a>,
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                <a class="title" href="https://teacherluke.co.uk/2021/06/04/723-bahar-from-iran-wisbolep-runner-up/">
                    723. Bahar from Iran&nbsp;
                    <img class="emoji" role="img" draggable="false" src="https://req_ses.w.org/images/core/emoji/13.0.1/svg/1f1ee-1f1f7.svg" alt="🇮🇷">
                    &nbsp;(WISBOLEP Runner-Up)
                </a>
                and they lived at the bottom of a well.
            </p>
            <p class="story">...</p>
    """  # noqa: E501,B950
    soup = BeautifulSoup(html_doc, "lxml")
    only_links, only_strings = parser.get_all_episode_links_from_soup(soup)
    assert len(only_links) == 2
    assert len(only_strings) == 2


def test_replacing_misspelled_link() -> None:
    """It replaces misspelled link and returns modified soup object."""
    html_doc = """<html><head><title>The Dormouse'req_ses story</title></head>
        <body>
            <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
                <a href="https://teacherluke.co.ukm/2012/08/06/london-olympics-2012/" class="sister" id="link2">Sara</a> and
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                and they lived at the bottom of a well.
            </p>
    """  # noqa: E501,B950
    soup = BeautifulSoup(html_doc, "lxml")
    modified_soup = parser.replace_misspelled_link(soup)
    new_href = modified_soup("a")[1]["href"]
    expected = "https://teacherluke.co.uk/2012/08/06/london-olympics-2012/"
    assert new_href == expected


def test_replacing_nothing_when_no_misspelled_link() -> None:
    """It replaces nothing when there is no misspelled link."""
    html_doc = """<html><head><title>The Dormouse'req_ses story</title></head>
        <body>
            <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
                <a href="https://teacherluke.co.uktest/2012/08/06/london-olympics-2012/" class="sister" id="link2">Sara</a> and
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                and they lived at the bottom of a well.
            </p>
    """  # noqa: E501,B950
    soup = BeautifulSoup(html_doc, "lxml")
    modified_soup = parser.replace_misspelled_link(soup)
    assert soup == modified_soup


def test_removing_irrelevant_links() -> None:
    """It removes known (from config list) irrelevant links."""
    test_list: t.List[str] = [
        "https://teacherluke.co.uk/2020/11/23/wisbolep/",
        "https://wp.me/P4IuUx-82H",  # <- Link to app
        "https://teacherluke.co.uk/2014/04/01/177-what-londoners-say-vs-what-they-mean/",  # noqa: E501,B950
        "https://teacherluke.co.uk/2021/03/26/711-william-from-france-%f0%9f%87%ab%f0%9f%87%b7-wisbolep-runner-up/",  # noqa: E501,B950
    ]
    test_texts: t.List[str] = [
        "1. Link",
        "Link to App (irrelevant)",
        "2. Link",
        "3. Link",
    ]
    new_list, new_texts = parser.remove_irrelevant_links(test_list, test_texts)
    assert len(new_list) == len(new_texts)
    assert "Link to App (irrelevant)" not in new_texts


def test_short_links_substitution() -> None:
    """It replaces short links with links from config dictionary."""
    test_list: t.List[str] = [
        "http://wp.me/p4IuUx-7sg",
        "https://wp.me/P4IuUx-82H",  # <- Link to app (no replacing)
        "https://teacherluke.co.uk/2014/04/01/177-what-londoners-say-vs-what-they-mean/",  # noqa: E501,B950
        "https://wp.me/p4IuUx-29",
    ]
    replaced: t.List[str] = parser.substitute_short_links(test_list)
    expected: t.List[str] = [
        "https://teacherluke.co.uk/2017/01/10/415-with-the-family-part-3-more-encounters-with-famous-people/",  # noqa: E501,B950
        "https://wp.me/P4IuUx-82H",
        "https://teacherluke.co.uk/2014/04/01/177-what-londoners-say-vs-what-they-mean/",  # noqa: E501,B950
        "https://teacherluke.co.uk/2011/10/11/notting-hill-carnival-video-frustration-out-takes/",  # noqa: E501,B950
    ]
    assert replaced == expected


def test_parsing_posts_from_archive_page(
    archive_parsing_results_mock: Tuple[List[str], List[str]],
    mocked_urls: List[str],
) -> None:
    """It parses links and texts from mocked archived page."""
    all_links, all_texts = archive_parsing_results_mock
    assert len(all_links) == len(all_texts)
    assert len(all_links) > 781
    assert "/2009/04/12/episode-1-introduction" in all_links[-1]
    # Intersection of mocked pages and all links
    intersection = set(mocked_urls) & set(all_links)
    assert len(intersection) > 15


def test_parsing_invalid_html(requests_mock: rm_Mocker) -> None:
    """It returns None if page does not comply with the parsing rules."""
    markup: str = '<a class="entry" id="post">'
    requests_mock.get(conf.ARCHIVE_URL, text=markup)
    parsing_result = parser.get_archive_parsing_results(conf.ARCHIVE_URL)
    assert parsing_result == (None, None, None)


def test_parsing_archive_without_episodes() -> None:
    """It collects links only matched by episode link pattern."""
    markup = """<html><head><title>The Dormouse'req_ses story</title></head>
        <article>
            <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                and they lived at the bottom of a well.
            </p>
            <p class="story">...</p>
    """  # noqa: E501,B950
    soup = BeautifulSoup(markup, "lxml")
    links, texts = parser.get_all_episode_links_from_soup(soup)
    assert len(links) == 0
    assert len(texts) == 0


def test_parsing_archive_with_known_duplicates() -> None:
    """It ignores several links by their texts."""
    markup = """<html><head><title>Known Duplicates</title></head>
            <a href="https://teacherluke.co.uk/2016/03/20/i-was-invited-onto-craig-wealands-weekly-blab-and-we-talked-about-comedy-video/">[VIDEO]</a>;
            <a href="https://teacherluke.co.uk/2018/04/18/522-learning-english-at-summer-school-in-the-uk-a-rambling-chat-with-raphael-miller/">episode 522</a>;
            <a href="https://teacherluke.co.uk/2017/08/14/website-content-lukes-criminal-past-zep-episode-185/">[Website content]</a>;
    """  # noqa: E501,B950
    soup = BeautifulSoup(markup, "lxml")
    links, texts = parser.get_all_episode_links_from_soup(soup)
    assert len(links) == 0
    assert len(texts) == 0


def test_parsing_all_episodes_from_mocked_archive(
    parsed_episodes_mock: List[lep.LepEpisode],
) -> None:
    """It parses all episodes from mocked archive HTML."""
    assert len(parsed_episodes_mock) == 786


def test_parsing_post_datetime() -> None:
    """It gets post datetime."""
    html_doc = """<a href="https://teacherluke.co.uk/2009/04/12/episode-1-introduction/" title="3:23 pm" rel="bookmark">
            <time class="entry-date" datetime="2009-04-12T15:23:33+02:00">April 12, 2009</time>
        </a>
    """  # noqa: E501,B950
    soup = BeautifulSoup(html_doc, "lxml")
    post_date = parser.parse_post_publish_datetime(soup)
    excepted = "2009-04-12T15:23:33+02:00"
    assert post_date == excepted


def test_parsing_post_datetime_without_element() -> None:
    """It returns default post datetime."""
    html_doc = """<a href="https://teacherluke.co.uk/2009/04/12/episode-1-introduction/" title="3:23 pm" rel="bookmark">
            <time>April 12, 2009</time>
        </a>
    """  # noqa: E501,B950
    soup = BeautifulSoup(html_doc, "lxml")
    post_date = parser.parse_post_publish_datetime(soup)
    excepted = "1999-01-01T01:01:01+02:00"
    assert post_date == excepted


def test_generating_new_post_index() -> None:
    """It generates index from URL."""
    indexes: t.List[int] = []
    test_url = "https://teacherluke.co.uk/2009/04/12/episode-1-introduction/"
    index = parser.generate_post_index(test_url, indexes)
    expected_index = int("2009041201")
    assert index == expected_index


def test_generating_new_post_index_on_same_day() -> None:
    """It generates index from URL if posts are on the same day."""
    indexes: t.List[int] = [2009041201]
    test_url = "https://teacherluke.co.uk/2009/04/12/episode-1-introduction/"
    index = parser.generate_post_index(test_url, indexes)
    expected_index = int("2009041202")
    assert index == expected_index
    index2 = parser.generate_post_index(test_url, indexes)
    assert index2 == expected_index + 1


def test_parsing_non_episode_link(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
) -> None:
    """It returns None (empty episode) for non-episode link."""
    non_episode_url = (
        "https://teacherluke.co.uk/premium/archive-comment-section/"  # noqa: E501,B950
    )
    requests_mock.get(
        non_episode_url,
        text="No need to parse this page",
        status_code=200,
    )
    link_title = "Some title"
    episode = parser.parse_single_page(non_episode_url, req_ses, link_title)
    assert episode is None


def test_parsing_links_to_audio_for_mocked_episodes(
    mocked_episodes: List[lep.LepEpisode],
) -> None:
    """It parses links to audio (if they exist)."""
    assert len(mocked_episodes) == 17
    assert mocked_episodes[3].episode == 35
    assert mocked_episodes[3].audios == [
        [
            "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3"  # noqa: E501,B950
        ]
    ]
    assert mocked_episodes[12].audios == []
    if mocked_episodes[10].audios is not None:
        assert len(mocked_episodes[10].audios) == 5


def test_no_appropriate_mp3_links_by_title() -> None:
    """It returns empty list if there are no appropriate links."""
    markup = """\
        <!DOCTYPE html>
        <a href="http://traffic.libsyn.com/teacherluke/600._Episode_600_Livestream_Ask_Me_Anything_Audio.mp3" rel="noopener" target="_blank">
            Get Episode
        </a>
        """  # noqa: E501,B950
    soup = BeautifulSoup(markup, "lxml")
    list_of_audio = parser.parse_post_audio(soup)
    assert len(list_of_audio) == 0


def test_selecting_appropriate_mp3_links_by_href() -> None:
    """It returns list with only appropriate mp3 links."""
    markup = """\
        <!DOCTYPE html>
        <a href="http://traffic.libsyn.com/teacherluke/600._Episode_600_Livestream_Ask_Me_Anything_Audio.mp3">
            Download episode
        </a>
        <!DOCTYPE html>
        <a href="https://audioboom.com/boos/3727124-how-to-use-the-lying-game-in-your-class-luke-thompson-teacherluke-co-uk.mp3">
            Download episode
        </a>
        <a href="https://teacherluke.co.uk/wp-content/uploads/2015/09/Chelsea-Loft-Short-copy.mp3">
            Download episode
        </a>
        <a href="https://audioboom.com/boos/2794795-the-mystery-story.mp3">
            Download episode
        </a>
        <a href="https://audioboom.com/boos/2550583-101-a-note-from-luke.mp3">
            Download episode
        </a>
        """  # noqa: E501,B950
    soup = BeautifulSoup(markup, "lxml")
    list_of_audio = parser.parse_post_audio(soup)
    assert len(list_of_audio) == 2
    assert list_of_audio[0] == [
        "http://traffic.libsyn.com/teacherluke/600._Episode_600_Livestream_Ask_Me_Anything_Audio.mp3",  # noqa: E501,B950
    ]
    assert list_of_audio[1] == [
        "https://audioboom.com/boos/2550583-101-a-note-from-luke.mp3",
    ]


def test_appropriate_mp3_link_with_word_audio() -> None:
    """It returns list of one appropriate mp3 link (without duplicate)."""
    markup = """\
        <!DOCTYPE html>
        <a href="http://traffic.libsyn.com/teacherluke/600._Episode_600_Livestream_Ask_Me_Anything_Audio.mp3">
            DOWNLOAD AUDIO
        </a>
        """  # noqa: E501,B950
    soup = BeautifulSoup(markup, "lxml")
    list_of_audio = parser.parse_post_audio(soup)
    assert len(list_of_audio) == 1


def test_episodes_sorting_by_date() -> None:
    """It sorts LepEpisodes by datetime then by episode number."""
    test_lep_ep_1 = LepEpisode(
        episode=35,
        date="2010-03-25T22:59:36+01:00",
        index=2010032501,
    )
    test_lep_ep_2 = LepEpisode(
        episode=0,
        date="2010-03-25T22:59:36+01:00",
        index=2010032502,
    )
    test_lep_ep_3 = LepEpisode(episode=100)
    episodes = [
        test_lep_ep_1,
        test_lep_ep_2,
        test_lep_ep_3,
    ]
    expected_sorted = [
        test_lep_ep_2,
        test_lep_ep_1,
        test_lep_ep_3,
    ]
    sorted_episodes = parser.sort_episodes_by_post_date(episodes)
    assert sorted_episodes == expected_sorted


def test_writing_lep_episodes_to_json(lep_temp_path: Path) -> None:
    """It creates JSON file from list of LepEpisode objects."""
    lep_ep_1 = LepEpisode(
        702,
        url="https://teacherluke.co.uk/2021/01/25/702-emergency-questions-with-james/",  # noqa: E501,B950
        index=2021012501,
    )
    lep_ep_2 = LepEpisode(episode=2, post_title="2. Test episode #2")
    episodes = [
        lep_ep_1,
        lep_ep_2,
    ]

    json_file = lep_temp_path / "json_db_tmp.json"
    parser.write_parsed_episodes_to_json(episodes, json_file)
    with open(json_file, "rb") as f:
        py_from_json = json.load(f)
    assert len(py_from_json) == 2
    assert (
        py_from_json[0]["url"]
        == "https://teacherluke.co.uk/2021/01/25/702-emergency-questions-with-james/"  # noqa: E501,B950
    )


def test_no_new_episodes_on_archive_vs_json_db(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    json_db_mock: str,
    capsys: CaptureFixture[str],
) -> None:
    """It prints when no new episodes on archive page."""
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

    parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL)
    captured = capsys.readouterr()
    assert "There are no new episodes. Exit." in captured.out


def test_no_valid_episode_objects_in_json_db(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    capsys: CaptureFixture[str],
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

    parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL)

    captured = capsys.readouterr()

    assert "[WARNING]" in captured.out
    assert "no valid episode objects" in captured.out


def test_json_db_not_valid(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    capsys: CaptureFixture[str],
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

    parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL)
    captured = capsys.readouterr()
    assert "[ERROR]" in captured.out
    assert "Data is not a valid JSON document." in captured.out


def test_json_db_not_available(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    capsys: CaptureFixture[str],
) -> None:
    """It prints error for unavailable JSON database."""
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

    parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL)
    captured = capsys.readouterr()
    assert "JSON database is not available. Exit." in captured.out


def test_json_db_contains_only_string(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    capsys: CaptureFixture[str],
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

    parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL)
    captured = capsys.readouterr()
    assert "[WARNING]" in captured.out
    assert "no valid episode objects" in captured.out


def test_invalid_objects_in_json_not_included(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    capsys: CaptureFixture[str],
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

    parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL)
    captured = capsys.readouterr()
    assert "[WARNING]" in captured.out
    assert "no valid episode objects" in captured.out


def test_updating_json_database_with_new_episodes(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    modified_json_less_db_mock: str,
    lep_temp_path: Path,
) -> None:
    """It retrives and saves new episodes from archive."""
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

    json_file = lep_temp_path / "json_db_tmp.json"
    parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL, json_file)
    with open(json_file, "rb") as f:
        py_from_json = json.load(f, object_hook=as_lep_episode_obj)

    assert len(py_from_json) == 786


def test_updating_json_database_with_extra_episodes(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    modified_json_extra_db_mock: str,
    capsys: CaptureFixture[str],
) -> None:
    """It prints warning if database contains more episodes than archive."""
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

    parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL)
    captured = capsys.readouterr()
    expected_message = "Database contains more episodes than current archive!"
    assert "[WARNING]" in captured.out
    assert expected_message in captured.out


def test_parsing_invalid_html_in_main_actions(
    requests_mock: rm_Mocker,
    capsys: CaptureFixture[str],
) -> None:
    """It prints error when no episode links on archive page."""
    markup: str = '<a class="entry" id="post">'
    requests_mock.get(conf.ARCHIVE_URL, text=markup)
    parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL)
    captured = capsys.readouterr()
    expected_message = "Can't parse any episodes from archive page."
    assert "[ERROR]" in captured.out
    assert expected_message in captured.out


def test_encoding_non_serializable_json_object() -> None:
    """It raises exception TypeError for non-serializable types."""
    obj = [complex(2 + 1)]
    with pytest.raises(TypeError):
        _ = json.dumps(obj, cls=lep.LepJsonEncoder)
