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
import copy
import json
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

import pytest
import requests
import requests_mock as req_mock
from bs4 import BeautifulSoup
from pytest import CaptureFixture
from pytest import MonkeyPatch
from pytest_mock import MockFixture
from requests_mock.mocker import Mocker as rm_Mocker
from requests_mock.request import _RequestObjectProxy

from lep_downloader import config as conf
from lep_downloader import lep
from lep_downloader import parser
from lep_downloader.exceptions import DataBaseUnavailableError
from lep_downloader.exceptions import NoEpisodeLinksError
from lep_downloader.exceptions import NoEpisodesInDataBaseError
from lep_downloader.exceptions import NotEpisodeURLError
from lep_downloader.lep import as_lep_episode_obj
from lep_downloader.lep import Lep
from lep_downloader.lep import LepEpisode
from lep_downloader.lep import LepEpisodeList
from lep_downloader.parser import Archive


lep_date_format = "%Y-%m-%dT%H:%M:%S%z"


def test_getting_success_page_response(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
) -> None:
    """It gets HTML content as text."""
    requests_mock.get(req_mock.ANY, text="Response OK")
    resp = Lep.get_web_document(conf.ARCHIVE_URL, req_ses)[0]
    assert resp == "Response OK"


def test_getting_404_page_response(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
) -> None:
    """It handles HTTPError if page is not found."""
    requests_mock.get(req_mock.ANY, text="Response OK", status_code=404)
    resp = Lep.get_web_document("http://example.com", req_ses)[0]
    assert "[ERROR]" in resp
    assert "404" in resp


def test_getting_503_page_response(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
) -> None:
    """It handle HTTPError if service is unavailable."""
    requests_mock.get(req_mock.ANY, text="Response OK", status_code=503)
    resp = Lep.get_web_document("http://example.com", req_ses)[0]
    assert "[ERROR]" in resp
    assert "503" in resp


def test_timeout_error(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
) -> None:
    """It handle any Timeout exception for page."""
    requests_mock.get(req_mock.ANY, exc=requests.exceptions.Timeout)
    resp = Lep.get_web_document("http://example.com", req_ses)[0]
    assert "[ERROR]" in resp
    assert "Timeout" in resp


def test_connection_error(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
) -> None:
    """It handles ConnectionError exception for bad request."""
    requests_mock.get(req_mock.ANY, exc=requests.exceptions.ConnectionError)
    resp = Lep.get_web_document("http://example.com", req_ses)[0]
    assert "[ERROR]" in resp
    assert "Bad request" in resp


def test_unknown_error(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
) -> None:
    """It handles any other exceptions during getting response from URL."""
    requests_mock.get(req_mock.ANY, exc=Exception("Something Bad"))
    resp = Lep.get_web_document("http://example.com", req_ses)[0]
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
    text, final_location, is_url_ok = Lep.get_web_document(
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
    text, final_location, is_url_ok = Lep.get_web_document(
        "https://re.direct",
        req_ses,
    )
    assert not is_url_ok
    assert "[ERROR]" in text
    assert "bad.final.location" in text
    assert final_location == "https://bad.final.location/"


def test_retrieve_all_episode_links_from_soup(
    archive: Archive,
) -> None:
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
    archive_parser = archive.parser
    archive_parser.soup = soup
    archive_parser.collect_links()
    assert len(archive.collected_links) == 2
    assert (
        list(archive.collected_links.values())[1]
        == "723. Bahar from Iran (WISBOLEP Runner-Up)"
    )


def test_replacing_misspelled_link(
    archive: Archive,
) -> None:
    """It replaces misspelled link in archive HTML content."""
    html_doc = """<html><head><title>The Dormouse'req_ses story</title></head>
        <body>
            <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
                <a href="https://teacherluke.co.ukm/2012/08/06/london-olympics-2012/" class="sister" id="link2">Sara</a> and
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                and they lived at the bottom of a well.
            </p>
    """  # noqa: E501,B950

    archive_parser = archive.parser
    archive_parser.content = html_doc
    content_before = copy.copy(archive_parser.content)
    archive_parser.do_pre_parsing()
    content_after = archive_parser.content
    soup = BeautifulSoup(content_after, "lxml")
    new_href = soup("a")[1]["href"]
    expected = "https://teacherluke.co.uk/2012/08/06/london-olympics-2012/"
    assert new_href == expected
    assert content_before != content_after


def test_replacing_nothing_when_no_misspelled_link(
    archive: Archive,
) -> None:
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
    archive_parser = archive.parser
    archive_parser.content = html_doc
    content_before = copy.copy(archive_parser.content)
    archive_parser.do_pre_parsing()
    content_after = archive_parser.content
    assert content_before == content_after


def test_removing_irrelevant_links(
    archive: Archive,
) -> None:
    """It removes known (from config list) irrelevant links."""
    test_links: List[str] = [
        "https://teacherluke.co.uk/2020/11/23/wisbolep/",
        "https://wp.me/P4IuUx-82H",  # <- Link to app
        "https://teacherluke.co.uk/2014/04/01/177-what-londoners-say-vs-what-they-mean/",  # noqa: E501,B950
        "https://teacherluke.co.uk/2021/03/26/711-william-from-france-%f0%9f%87%ab%f0%9f%87%b7-wisbolep-runner-up/",  # noqa: E501,B950
    ]
    test_texts: List[str] = [
        "1. Link",
        "Link to App (irrelevant)",
        "2. Link",
        "3. Link",
    ]
    test_dct = dict(zip(test_links, test_texts))
    archive_parser = archive.parser
    archive.collected_links = test_dct
    archive_parser.remove_irrelevant_links()
    assert len(archive.collected_links) == 3
    assert len(archive.deleted_links) == 1
    assert "https://wp.me/P4IuUx-82H" in archive.deleted_links
    assert list(archive.collected_links.values())[1] == "2. Link"


def test_short_links_substitution(
    archive: Archive,
) -> None:
    """It replaces short links with links from config dictionary."""
    test_links: List[str] = [
        "http://wp.me/p4IuUx-7sg",  # <- Short link (replacing)
        "https://wp.me/P4IuUx-82H",  # <- Link to app (NO replacing)
        "https://teacherluke.co.uk/2014/04/01/177-what-londoners-say-vs-what-they-mean/",  # noqa: E501,B950
        "https://wp.me/p4IuUx-29",  # <- Short link (replacing)
    ]
    test_texts: List[str] = [
        "1. Substitution 1",
        "Link to App (irrelevant)",
        "2. Link",
        "3. Substitution 2",
    ]
    test_dct = dict(zip(test_links, test_texts))
    archive_parser = archive.parser
    archive.collected_links = test_dct
    archive_parser.substitute_short_links()
    assert len(archive.collected_links) == 4
    assert len(archive.deleted_links) == 0
    assert "https://wp.me/P4IuUx-82H" in archive.collected_links
    assert (
        list(archive.collected_links)[0]
        == "https://teacherluke.co.uk/2017/01/10/415-with-the-family-part-3-more-encounters-with-famous-people/"  # noqa: E501,B950
    )
    assert list(archive.collected_links.values())[0] == "1. Substitution 1"
    assert (
        list(archive.collected_links)[3]
        == "https://teacherluke.co.uk/2011/10/11/notting-hill-carnival-video-frustration-out-takes/"  # noqa: E501,B950
    )
    assert list(archive.collected_links.values())[3] == "3. Substitution 2"


def test_parsing_posts_from_archive_page(
    archive_parsing_results_mock: Dict[str, str],
) -> None:
    """It parses links and texts from mocked archived page."""
    assert len(archive_parsing_results_mock) == 782
    assert (
        "/2009/04/12/episode-1-introduction" in list(archive_parsing_results_mock)[-1]
    )
    # Intersection of mocked pages and all links
    # intersection = set(mocked_urls) & set(all_links)
    # assert len(intersection) > 15


def test_parsing_invalid_html(
    requests_mock: rm_Mocker,
    archive: Archive,
) -> None:
    """It returns None if page does not comply with the parsing rules."""
    markup: str = '<a class="entry" id="post">'
    requests_mock.get(conf.ARCHIVE_URL, text=markup)
    with pytest.raises(NotEpisodeURLError) as ex:
        archive.parser.parse_url()
    assert conf.ARCHIVE_URL in ex.value.args[0]  # Trailing slash for domain URL
    assert (
        ex.value.args[1] == "ERROR: Can't parse this page: 'article' tag was not found."
    )


def test_parsing_archive_without_episodes(archive: Archive) -> None:
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
    archive_parser = archive.parser
    archive_parser.soup = soup
    with pytest.raises(NoEpisodeLinksError) as ex:
        archive_parser.collect_links()
    assert len(archive.collected_links) == 0
    assert ex.value.args[0] == conf.ARCHIVE_URL
    assert ex.value.args[1] == "ERROR: No episode links on archive page"


def test_parsing_archive_with_known_duplicates(
    archive: Archive,
) -> None:
    """It ignores several links by their texts."""
    markup = """<html><head><title>Known Duplicates</title></head>
            <a href="https://teacherluke.co.uk/2016/03/20/i-was-invited-onto-craig-wealands-weekly-blab-and-we-talked-about-comedy-video/">[VIDEO]</a>;
            <a href="https://teacherluke.co.uk/2018/04/18/522-learning-english-at-summer-school-in-the-uk-a-rambling-chat-with-raphael-miller/">episode 522</a>;
            <a class="title" href="https://teacherluke.co.uk/2018/04/18/522-learning-english-at-summer-school-in-the-uk-a-rambling-chat-with-raphael-miller/"><strong>522. Learning English at Summer School in the UK (A Rambling Chat with Raphael Miller)</strong></a>
            <a href="https://teacherluke.co.uk/2017/08/14/website-content-lukes-criminal-past-zep-episode-185/">[Website content]</a>;
    """  # noqa: E501,B950
    soup = BeautifulSoup(markup, "lxml")
    archive_parser = archive.parser
    archive_parser.soup = soup
    archive_parser.collect_links()
    assert len(archive.collected_links) == 1
    assert (
        list(archive.collected_links.values())[0]
        == "522. Learning English at Summer School in the UK (A Rambling Chat with Raphael Miller)"  # noqa: E501,B950
    )


def test_parsing_archive_with_only_duplicates(
    archive: Archive,
) -> None:
    """It does not fail when there are only duplicated links on page."""
    markup = """<html><head><title>Known Duplicates</title></head>
            <a href="https://teacherluke.co.uk/2016/03/20/i-was-invited-onto-craig-wealands-weekly-blab-and-we-talked-about-comedy-video/">[VIDEO]</a>;
            <a href="https://teacherluke.co.uk/2018/04/18/522-learning-english-at-summer-school-in-the-uk-a-rambling-chat-with-raphael-miller/">episode 522</a>;
            <a href="https://teacherluke.co.uk/2017/08/14/website-content-lukes-criminal-past-zep-episode-185/">[Website content]</a>;
    """  # noqa: E501,B950
    soup = BeautifulSoup(markup, "lxml")
    archive_parser = archive.parser
    archive_parser.soup = soup
    archive_parser.collect_links()
    assert len(archive.collected_links) == 0
    archive_parser.remove_irrelevant_links()
    assert len(archive.collected_links) == 0
    archive_parser.substitute_short_links()
    assert len(archive.collected_links) == 0


def test_parsing_all_episodes_from_mocked_archive(
    parsed_episodes_mock: LepEpisodeList,
) -> None:
    """It parses all episodes from mocked archive HTML."""
    # SAVING MOCKED JSON DB # #
    # sorted_eps = parsed_episodes_mock.desc_sort_by_date_and_index()
    # parser.write_parsed_episodes_to_json(sorted_eps)
    # SAVING MOCKED JSON DB # #

    # assert len(parsed_episodes_mock) == 786
    assert len(parsed_episodes_mock) == 782  # Without duplicates


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


def test_generating_new_post_index(
    archive: Archive,
) -> None:
    """It generates index from URL."""
    test_url = "https://teacherluke.co.uk/2009/04/12/episode-1-introduction/"
    index = parser.generate_post_index(test_url, archive.used_indexes)
    expected_index = 2009041201
    assert index == expected_index


def test_generating_new_post_index_on_same_day(
    archive: Archive,
) -> None:
    """It generates index from URL if posts are on the same day."""
    archive.used_indexes.add(2009041201)
    test_url = "https://teacherluke.co.uk/2009/04/12/episode-1-introduction/"
    index = parser.generate_post_index(test_url, archive.used_indexes)
    expected_index = 2009041202
    assert index == expected_index
    index2 = parser.generate_post_index(test_url, archive.used_indexes)
    assert index2 == expected_index + 1


def test_parsing_non_episode_link(
    requests_mock: rm_Mocker,
    req_ses: requests.Session,
    archive: Archive,
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
    with pytest.raises(NotEpisodeURLError) as ex:
        parser.EpisodeParser(archive, non_episode_url, req_ses, link_title).parse_url()
    assert len(archive.collected_links) == 0
    assert ex.value.args[0] == non_episode_url


def test_skipping_non_episode_link(
    requests_mock: rm_Mocker,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    archive: Archive,
) -> None:
    """It skips non-episode link."""
    test_urls = [
        "https://teacherluke.co.uk/2009/04/12/episode-1-introduction/",
        "https://teacherluke.co.uk/premium/archive-comment-section/",  # noqa: E501,B950
    ]
    test_texts = [
        "Episode 1 Link",
        "Non Episode Title Link",
    ]
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=single_page_matcher,
        text=single_page_mock,
    )
    requests_mock.get(
        "https://teacherluke.co.uk/premium/archive-comment-section/",
        text="No need to parse this page",
        status_code=200,
    )
    test_dct = dict(zip(test_urls, test_texts))
    archive.parse_each_episode(test_dct)
    assert len(archive.episodes) == 1
    assert archive.episodes[0].post_title == "Episode 1 Link"


def test_parsing_links_to_audio_for_mocked_episodes(
    mocked_episodes: LepEpisodeList,
) -> None:
    """It parses links to audio (if they exist)."""
    # assert len(mocked_episodes) == 17
    assert len(mocked_episodes) == 16  # Now without duplicates
    assert mocked_episodes[3].episode == 35
    assert mocked_episodes[3].files["audios"] == [
        [
            "http://traffic.libsyn.com/teacherluke/36-london-video-interviews-pt-1-audio-only.mp3"  # noqa: E501,B950
        ]
    ]
    assert mocked_episodes[11].files["audios"] == []
    if mocked_episodes[9].files["audios"] is not None:
        assert len(mocked_episodes[9].files["audios"]) == 5


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
    """It sorts LepEpisodes by datetime first."""
    test_lep_ep_1 = LepEpisode(episode=0, index=2010032502)
    test_lep_ep_1.date = "2010-03-25T22:59:36+02:00"
    test_lep_ep_2 = LepEpisode(episode=35, index=2010032501)
    test_lep_ep_2.date = "2010-03-25T22:59:36+01:00"
    assert test_lep_ep_1 < test_lep_ep_2

    test_lep_ep_3 = LepEpisode(episode=100)

    episodes = LepEpisodeList([test_lep_ep_1, test_lep_ep_2, test_lep_ep_3])
    expected_sorted = [
        test_lep_ep_2,
        test_lep_ep_1,
        test_lep_ep_3,
    ]
    sorted_episodes = episodes.desc_sort_by_date_and_index()
    assert sorted_episodes == expected_sorted


def test_episodes_sorting_by_date_and_index() -> None:
    """It sorts LepEpisodes by datetime then by index number."""
    test_lep_ep_1 = LepEpisode(episode=35, index=2010032501)
    test_lep_ep_1.date = "2021-12-24T22:22:22+02:00"
    test_lep_ep_2 = LepEpisode(episode=0, index=2010032502)
    test_lep_ep_2.date = "2021-12-24T22:22:22+02:00"
    assert test_lep_ep_1 < test_lep_ep_2

    test_lep_ep_3 = LepEpisode(episode=13, index=2010032503)
    test_lep_ep_3.date = "2021-12-24T22:22:22+02:00"

    episodes = LepEpisodeList([test_lep_ep_1, test_lep_ep_2, test_lep_ep_3])
    expected_sorted = [
        test_lep_ep_3,
        test_lep_ep_2,
        test_lep_ep_1,
    ]
    sorted_episodes = episodes.desc_sort_by_date_and_index()
    assert sorted_episodes == expected_sorted


def test_writing_lep_episodes_to_json(tmp_path: Path) -> None:
    """It creates JSON file from list of LepEpisode objects."""
    lep_ep_1 = LepEpisode(
        702,
        url="https://teacherluke.co.uk/2021/01/25/702-emergency-questions-with-james/",  # noqa: E501,B950
        index=2021012501,
    )
    lep_ep_2 = LepEpisode(episode=2, post_title="2. Test episode #2")
    episodes = LepEpisodeList([lep_ep_1, lep_ep_2])

    json_file = str(Path(tmp_path / "json_db_tmp.json").absolute())
    parser.write_parsed_episodes_to_json(episodes, json_file)
    with open(json_file, "rb") as f:
        py_from_json = json.load(f)
    assert len(py_from_json) == 2
    assert (
        py_from_json[0]["url"]
        == "https://teacherluke.co.uk/2021/01/25/702-emergency-questions-with-james/"  # noqa: E501,B950
    )


def test_no_valid_episode_objects_in_json_db(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    archive: Archive,
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

    with pytest.raises(NoEpisodesInDataBaseError) as ex:
        archive.do_parsing_actions(conf.JSON_DB_URL)
    assert "there are NO episodes" in ex.value.args[0]


def test_json_db_not_valid(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    archive: Archive,
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

    with pytest.raises(NoEpisodesInDataBaseError) as ex:
        archive.do_parsing_actions(conf.JSON_DB_URL)
    assert "there are NO episodes" in ex.value.args[0]


def test_json_db_not_available(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    archive: Archive,
    # capsys: CaptureFixture[str],
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

    with pytest.raises(DataBaseUnavailableError):
        archive.do_parsing_actions(conf.JSON_DB_URL)
    # assert "" in ex.value.args[0]
    # captured = capsys.readouterr()
    # assert "JSON database is not available. Exit." in captured.out


def test_json_db_contains_only_string(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    archive: Archive,
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

    with pytest.raises(NoEpisodesInDataBaseError) as ex:
        archive.do_parsing_actions(conf.JSON_DB_URL)
    assert "there are NO episodes" in ex.value.args[0]


def test_invalid_objects_in_json_not_included(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    archive: Archive,
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

    with pytest.raises(NoEpisodesInDataBaseError) as ex:
        archive.do_parsing_actions(conf.JSON_DB_URL)
    assert "there are NO episodes" in ex.value.args[0]


def test_updating_json_database_with_new_episodes(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    single_page_mock: str,
    modified_json_less_db_mock: str,
    tmp_path: Path,
    archive: Archive,
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

    json_file = str(Path(tmp_path / "json_db_tmp.json").absolute())
    archive.do_parsing_actions(conf.JSON_DB_URL, json_name=json_file)
    with open(json_file, "rb") as f:
        py_from_json: LepEpisodeList = json.load(f, object_hook=as_lep_episode_obj)

    # CALCULATION: ! (for JSON v3.0.0a2 'without duplicates in JSON db')
    # Initial total number of episodes = 782
    # In 'modified_json_less_db_mock' we deleted 3 episodes
    # Two from top (latest) and one in the middle
    # Last in db becomes # 711. In archive last # 733.
    # Between them 24 episodes (updates)
    # 24 + 782 - 3 = 803
    assert len(py_from_json) == 803
    # assert len(py_from_json) == 786


def test_parsing_invalid_html_in_main_actions(
    requests_mock: rm_Mocker,
    archive: Archive,
) -> None:
    """It raises error when ivalid DOM on archive page."""
    markup: str = '<a class="entry" id="post">'
    requests_mock.get(conf.ARCHIVE_URL, text=markup)
    with pytest.raises(NotEpisodeURLError) as ex:
        archive.do_parsing_actions(conf.JSON_DB_URL)
    assert conf.ARCHIVE_URL in ex.value.args[0]
    assert (
        ex.value.args[1] == "ERROR: Can't parse this page: 'article' tag was not found."
    )


def test_encoding_non_serializable_json_object() -> None:
    """It raises exception TypeError for non-serializable types."""
    obj = [complex(2 + 1)]
    with pytest.raises(TypeError):
        _ = json.dumps(obj, cls=lep.LepJsonEncoder)


def test_invoking_not_implemented_methods(
    archive: Archive,
) -> None:
    """It raises exceptions if someone forget to override methods."""

    class NewParser(parser.LepParser):
        """Future new subclass."""

        pass

    with pytest.raises(NotImplementedError):
        NewParser(archive, "Some URL").do_pre_parsing()
    with pytest.raises(NotImplementedError):
        NewParser(archive, "Some URL").collect_links()
    with pytest.raises(NotImplementedError):
        NewParser(archive, "Some URL").do_post_parsing()


def test_extracting_date_from_url_negative() -> None:
    """It returns empty string if URL does not contain valid date."""
    date = parser.extract_date_from_url(
        "https://teacherluke.co.uk/200904/12/episode-1-introduction/"
    )
    assert date == ""


def test_converting_invalid_date() -> None:
    """It raises ValueError for invalid date format."""
    # TODO (hotenov): Add handling this exception in other functions.
    with pytest.raises(ValueError) as ex:
        _ = parser.convert_date_from_url("")
    assert "does not match format '%Y/%m/%d'" in ex.value.args[0]


def test_replacing_chars_in_post_title() -> None:
    """It replaces invalid path characters with "_"."""
    ep = LepEpisode()
    ep.post_title = r"999. [1/2]. Asterisk * and question mark ?"
    assert ep.post_title == "999. [1_2]. Asterisk _ and question mark _"
    assert ep._origin_post_title == "999. [1/2]. Asterisk * and question mark ?"
    ep.post_title = r"Other invalid chars: [<>:\"/\\\\|?*]"
    assert ep.post_title == "Other invalid chars_ [_____________]"
    assert ep._origin_post_title == r"Other invalid chars: [<>:\"/\\\\|?*]"


def test_comparison_operators_for_episode_objects() -> None:
    """It lets to compare two episode objects."""
    ep_1 = LepEpisode()
    ep_1.date = "2021-12-24T22:22:22+02:00"
    ep_2 = LepEpisode()
    ep_2.date = "2021-12-24T20:33:22Z"
    assert ep_1 < ep_2  # Because it converts to UTC
    ep_3 = LepEpisode()
    ep_3.date = "2021-12-24T22:22:22+02:00"
    ep_3.index = 2021122401
    ep_4 = LepEpisode()
    ep_4.date = "2021-12-24T22:22:22+02:00"
    ep_4.index = 2021122401
    assert ep_3 == ep_4
    ep_4.index = 2021122402
    assert ep_3 != ep_4
    assert ep_3 < ep_4


def test_episode_object_reprisentation() -> None:
    """Check work of __repr__ method of LepEpisode object."""
    ep_1 = LepEpisode()
    ep_1.index = 2021122403
    ep_1.episode = 777
    ep_1.post_title = "777. Some / good title more than sixteen chars."
    obj_repr = repr(ep_1)
    excepted_repr = "2021122403: 777:777. Some _ good"
    assert obj_repr == excepted_repr


def test_setting_episode_date_as_datetime() -> None:
    """It lets to pass datetime as episode date."""
    t_zone = timezone(timedelta(hours=3))  # GMT+03:00
    new_date = datetime(2021, 12, 24, 17, 18, 19, tzinfo=t_zone)
    ep = LepEpisode(date=new_date)
    as_str = ep.date.strftime(r"%Y-%m-%dT%H:%M:%S%z")
    except_date = "2021-12-24T17:18:19+0300"
    assert as_str == except_date


def test_parsing_html_title_for_mocked_episodes(
    parsed_episodes_mock: LepEpisodeList,
) -> None:
    """It parses HTML tag <title> for each episode."""
    assert (
        parsed_episodes_mock[33]._title
        == "36. London Video Interviews Pt.1 | Luke’s ENGLISH Podcast"
    )
    assert parsed_episodes_mock[45]._title == "NO TITLE!"


def test_write_text_to_html_by_absolute_path(
    tmp_path: Path,
    archive: Archive,
) -> None:
    """It saves text to HTML file by passed absolute path."""
    text = """<html>
        <body>Some text</body>
    </html>
    """
    name = "Unsafe / name : \\ here"
    archive.write_text_to_html(text, name, str(tmp_path))
    expected_filename = "Unsafe _ name _ _ here.html"
    expected_file = tmp_path / expected_filename
    assert expected_file.exists()
    assert expected_file.read_text() == text


def test_write_text_to_html_by_relative_path(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    archive: Archive,
) -> None:
    """It saves text to HTML file by default (relative) path."""
    text = """<html>
        <body>Some text</body>
    </html>
    """
    name = "Unsafe / name : \\ here"
    monkeypatch.chdir(tmp_path)
    expected_subfolder = Path(conf.PATH_TO_HTML_FILES)
    # Create relative path
    # For this test only. Folder will be created during path validation
    Path(tmp_path / expected_subfolder).mkdir(parents=True, exist_ok=True)
    archive.write_text_to_html(text, name)
    expected_filename = "Unsafe _ name _ _ here.html"
    expected_file = tmp_path / expected_subfolder / expected_filename
    assert expected_file.exists()
    assert expected_file.read_text() == text


def test_skip_writing_html_when_any_error(
    mocker: MockFixture,
    tmp_path: Path,
    archive: Archive,
) -> None:
    """It ignores errors during writing HTML files."""
    text = """Some text"""
    name = "Unsafe / name : \\ here"

    expected_filename = "Unsafe _ name _ _ here.html"
    expected_file = tmp_path / expected_filename

    mock = mocker.patch("pathlib.Path.write_text")

    mock.side_effect = PermissionError
    # with pytest.raises(PermissionError):
    #     parser.write_text_to_html(text, name, tmp_path)
    archive.write_text_to_html(text, name, str(tmp_path))
    assert not expected_file.exists()

    mock.side_effect = OSError
    # with pytest.raises(PermissionError):
    #     parser.write_text_to_html(text, name, tmp_path)
    archive.write_text_to_html(text, name, str(tmp_path))
    assert not expected_file.exists()


def test_lep_log_writing_newlines_in_logfile(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    """It uses 'oneline' parameter to print newlines in logfile (if needed)."""
    monkeypatch.chdir(tmp_path)
    log_1 = lep.LepLog(True)
    log_1.msg("First raw \n Second Raw")
    logfile_1 = tmp_path / "_lep_debug_.log"
    log_text = logfile_1.read_text(encoding="utf-8")
    assert "First raw ⏎ Second Raw" in log_text

    log_2 = lep.LepLog(True, "with_lines.log")
    log_2.msg("First raw \n Second Raw", one_line=False)
    logfile_2 = tmp_path / "with_lines.log"
    log_text_2 = logfile_2.read_text(encoding="utf-8")
    assert "First raw \n Second Raw" in log_text_2


def test_lep_log_writing_several_messages_on_oneline_in_console(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    """It can print log messages on one line.

    But in logfile it will be separate message (or even files)
    """
    monkeypatch.chdir(tmp_path)
    log_1 = lep.LepLog(True, "1.log")
    log_1.msg("Msg from #1 | ", wait_input=True)
    logfile_1 = tmp_path / "1.log"
    log_text_1 = logfile_1.read_text(encoding="utf-8")

    log_2 = lep.LepLog(True, "2.log")
    log_2.msg("Msg from #2.")
    log_1.msg("Again #1")
    logfile_2 = tmp_path / "2.log"
    log_text_2 = logfile_2.read_text(encoding="utf-8")
    captured = capsys.readouterr()
    assert "Msg from #1 | Msg from #2.\nAgain #1" in captured.out
    assert ("Msg from #1 | " in log_text_1) and ("Msg from #1 | " not in log_text_2)
    assert "Msg from #2." in log_text_2
    assert "Again #1" in log_text_2  # Note: in '2.log' due to loguru design


def test_lep_log_display_messages_in_console_only(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    """It can skip logfile for certain messages in debug mode.

    And display them only in console.
    """
    monkeypatch.chdir(tmp_path)
    log_1 = lep.LepLog(True, "1.log")
    log_1.msg("Message #1")
    log_1.msg("Message #2 console", skip_file=True)
    log_1.msg("Message #3")

    logfile_1 = tmp_path / "1.log"
    log_text_1 = logfile_1.read_text(encoding="utf-8")
    captured = capsys.readouterr()
    assert "Message #1\nMessage #2 console\nMessage #3" in captured.out
    assert "Message #1" in log_text_1
    assert "Message #3" in log_text_1
    assert "Message #2 console" not in log_text_1
