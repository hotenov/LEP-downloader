"""Test cases for the parser module."""
import json
import tempfile
import typing as t
from datetime import datetime
from pathlib import Path

import pytest
import requests
import requests_mock as req_mock
from bs4 import BeautifulSoup
from pytest import CaptureFixture
from requests_mock.mocker import Mocker as rm_Mocker
from requests_mock.response import _Context as rm_Context

from lep_downloader import config as conf
from lep_downloader import lep
from lep_downloader import parser
from lep_downloader.lep import LepEpisode


OFFLINE_HTML_DIR = Path(
    Path(__file__).resolve().parent,
    "fixtures",
)

LINK_FILE_MAPPING = {
    "https://teacherluke.co.uk/2009/04/12/episode-1-introduction/": "2021-09-13_05-37-36 teacherluke.co.uk _2009_04_12_episode-1-introduction_.html",
    "https://teacherluke.co.uk/2009/10/19/extra-podcast-12-phrasal-verbs/": "2021-09-07_09-14-02 teacherluke.co.uk _2009_10_19_extra-podcast-12-phrasal-verbs_.html",
    "https://teacherluke.co.uk/2009/10/19/episode-11-michael-jackson/": "2021-09-07_09-14-02 teacherluke.co.uk _2009_10_19_episode-11-michael-jackson_.html",
    "https://teacherluke.co.uk/2010/03/25/london-video-interviews-pt-1/": "2021-09-07_09-14-02 teacherluke.co.uk _2010_03_25_london-video-interviews-pt-1_.html",
    "http://teacherluke.wordpress.com/2012/09/27/113-setting-the-world-to-rights/": "2021-09-07_09-14-02 teacherluke.wordpress.com _2012_09_27_113-setting-the-world-to-rights_.html",
    "https://teacherluke.co.uk/2014/06/30/193-culture-shock-life-in-london-pt-2/": "2021-09-07_09-14-02 teacherluke.co.uk _2014_06_30_193-culture-shock-life-in-london-pt-2_.html",
    "https://teacherluke.co.uk/2015/10/21/304-back-to-the-future-part-1/": "2021-09-07_09-14-02 teacherluke.co.uk _2015_10_07_300-episode-300-part-1_.html",
    "https://teacherluke.co.uk/2015/10/22/305-back-to-the-future-part-2/": "2021-09-07_09-14-02 teacherluke.co.uk _2015_10_07_300-episode-300-part-2_.html",
    "https://teacherluke.co.uk/2016/08/07/370-in-conversation-with-rob-ager-from-liverpool-part-1-life-in-liverpool-interest-in-film-analysis/": "2021-09-07_09-14-02 teacherluke.co.uk _2016_08_07_370-in-conversation-with-rob-ager-from.html",
    "https://teacherluke.co.uk/2017/03/11/lep-on-zep-my-recent-interview-on-zdeneks-english-podcast/": "2021-09-07_09-14-02 teacherluke.co.uk _2017_03_11_lep-on-zep-my-recent-interview-on-zden.html",
    "https://teacherluke.co.uk/2017/05/26/i-was-invited-onto-the-english-across-the-pond-podcast/": "2021-09-07_09-14-02 teacherluke.co.uk _2017_05_26_i-was-invited-onto-the-english-across-.html",
    "https://teacherluke.co.uk/2017/08/26/website-only-a-history-of-british-pop-a-musical-tour-through-james-vinyl-collection/": "2021-09-07_09-14-02 teacherluke.co.uk _2017_08_26_website-only-a-history-of-british-pop-.html",
    "https://teacherluke.co.uk/2021/02/03/703-walaa-from-syria-wisbolep-competition-winner-%f0%9f%8f%86/": "2021-08-11_lep-e703-page-content-pretty.html",
    "https://teacherluke.co.uk/2021/03/26/711-william-from-france-%f0%9f%87%ab%f0%9f%87%b7-wisbolep-runner-up/": "2021-08-11_lep-e711-page-content-pretty.html",
    "https://teacherluke.co.uk/2021/04/11/714-robin-from-hamburg-%f0%9f%87%a9%f0%9f%87%aa-wisbolep-runner-up/": "2021-09-07_09-14-02 teacherluke.co.uk _2021_04_11_714-robin-from-hamburg-🇩🇪-wisbolep-run.html",
    "https://teacherluke.co.uk/2021/08/03/733-a-summer-ramble/": "2021-08-11_lep-e733-page-content-pretty.html",
    "https://teacherluke.co.uk/premium/archive-comment-section/": "2021-09-28_10-44-00 Archive & Comment Section _ (premium archive).html",  # None-episode link
}

MAPPING_KEYS: t.List[str] = [*LINK_FILE_MAPPING]

s = requests.Session()


def test_getting_success_page_response(requests_mock: rm_Mocker) -> None:
    """It gets HTML content as text."""
    requests_mock.get(req_mock.ANY, text="Response OK")
    resp = parser.get_web_page_html_text(conf.ARCHIVE_URL, s)[0]
    assert resp == "Response OK"


def test_getting_404_page_response(requests_mock: rm_Mocker) -> None:
    """It handles HTTPError if page is not found."""
    requests_mock.get(req_mock.ANY, text="Response OK", status_code=404)
    resp = parser.get_web_page_html_text("http://example.com", s)[0]
    assert "[ERROR]" in resp
    assert "404" in resp


def test_getting_503_page_response(requests_mock: rm_Mocker) -> None:
    """It handle HTTPError if service is unavailable."""
    requests_mock.get(req_mock.ANY, text="Response OK", status_code=503)
    resp = parser.get_web_page_html_text("http://example.com", s)[0]
    assert "[ERROR]" in resp
    assert "503" in resp


def test_timeout_error(requests_mock: rm_Mocker) -> None:
    """It handle any Timeout exception for page."""
    requests_mock.get(req_mock.ANY, exc=requests.exceptions.Timeout)
    resp = parser.get_web_page_html_text("http://example.com", s)[0]
    assert "[ERROR]" in resp
    assert "Timeout" in resp


def test_connection_error(requests_mock: rm_Mocker) -> None:
    """It handles ConnectionError exception for bad request."""
    requests_mock.get(req_mock.ANY, exc=requests.exceptions.ConnectionError)
    resp = parser.get_web_page_html_text("http://example.com", s)[0]
    assert "[ERROR]" in resp
    assert "Bad request" in resp


def test_unknown_error(requests_mock: rm_Mocker) -> None:
    """It handles any other exceptions during attempt to get response from URL."""
    requests_mock.get(req_mock.ANY, exc=Exception("Something Bad"))
    resp = parser.get_web_page_html_text("http://example.com", s)[0]
    assert "[ERROR]" in resp
    assert "Unhandled error" in resp


def test_final_location_for_good_redirect(requests_mock: rm_Mocker) -> None:
    """It retrieves final location during redirect."""
    requests_mock.get(
        "https://re.direct",
        text="Rederecting to...",
        status_code=301,
        headers={"Location": "https://final.location/"},
    )
    requests_mock.get("https://final.location", text="Final location")
    text, final_location, is_url_ok = parser.get_web_page_html_text(
        "https://re.direct",
        s,
    )
    assert is_url_ok
    assert text == "Final location"
    assert final_location == "https://final.location/"


def test_final_location_for_bad_redirect(requests_mock: rm_Mocker) -> None:
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
    text, final_location, is_url_ok = parser.get_web_page_html_text(
        "https://re.direct",
        s,
    )
    assert not is_url_ok
    assert "[ERROR]" in text
    assert "bad.final.location" in text
    assert final_location == "https://bad.final.location/"


def test_retrieve_all_episode_links_from_soup() -> None:
    """It returns only <a> tags from soup object."""
    html_doc = """<html><head><title>The Dormouse's story</title></head>
        <article>
            <p class="title"><b>The Dormouse's story</b></p>
            <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="https://teacherluke.co.uk/2017/09/24/website-content-luke-on-the-real-life-english-podcast/" class="sister" id="link1">Elsie</a>,
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                <a class="title" href="https://teacherluke.co.uk/2021/06/04/723-bahar-from-iran-wisbolep-runner-up/">
                    723. Bahar from Iran&nbsp;
                    <img class="emoji" role="img" draggable="false" src="https://s.w.org/images/core/emoji/13.0.1/svg/1f1ee-1f1f7.svg" alt="🇮🇷">
                    &nbsp;(WISBOLEP Runner-Up)
                </a>
                and they lived at the bottom of a well.
            </p>
            <p class="story">...</p>
    """
    soup = BeautifulSoup(html_doc, "lxml")
    only_links, only_strings = parser.get_all_episode_links_from_soup(soup)
    assert len(only_links) == 2
    assert len(only_strings) == 2


def test_replacing_misspelled_link() -> None:
    """It replaces misspelled link and returns modified soup object."""
    html_doc = """<html><head><title>The Dormouse's story</title></head>
        <body>
            <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
                <a href="https://teacherluke.co.ukm/2012/08/06/london-olympics-2012/" class="sister" id="link2">Sara</a> and
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                and they lived at the bottom of a well.
            </p>
    """
    soup = BeautifulSoup(html_doc, "lxml")
    modified_soup = parser.replace_misspelled_link(soup)
    new_href = modified_soup("a")[1]["href"]
    assert new_href == "https://teacherluke.co.uk/2012/08/06/london-olympics-2012/"


def test_replacing_nothing_when_no_misspelled_link() -> None:
    """It replaces nothing when there is no misspelled link and returns the same soup object."""
    html_doc = """<html><head><title>The Dormouse's story</title></head>
        <body>
            <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
                <a href="https://teacherluke.co.uktest/2012/08/06/london-olympics-2012/" class="sister" id="link2">Sara</a> and
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                and they lived at the bottom of a well.
            </p>
    """
    soup = BeautifulSoup(html_doc, "lxml")
    modified_soup = parser.replace_misspelled_link(soup)
    assert soup == modified_soup


def test_removing_irrelevant_links() -> None:
    """It removes known (from config list) irrelevant links."""
    test_list: t.List[str] = [
        "https://teacherluke.co.uk/2020/11/23/wisbolep/",
        "https://wp.me/P4IuUx-82H",  # <- Link to app
        "https://teacherluke.co.uk/2014/04/01/177-what-londoners-say-vs-what-they-mean/",
        "https://teacherluke.co.uk/2021/03/26/711-william-from-france-%f0%9f%87%ab%f0%9f%87%b7-wisbolep-runner-up/",
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
        "https://teacherluke.co.uk/2014/04/01/177-what-londoners-say-vs-what-they-mean/",
        "https://wp.me/p4IuUx-29",
    ]
    replaced: t.List[str] = parser.substitute_short_links(test_list)
    expected: t.List[str] = [
        "https://teacherluke.co.uk/2017/01/10/415-with-the-family-part-3-more-encounters-with-famous-people/",
        "https://wp.me/P4IuUx-82H",
        "https://teacherluke.co.uk/2014/04/01/177-what-londoners-say-vs-what-they-mean/",
        "https://teacherluke.co.uk/2011/10/11/notting-hill-carnival-video-frustration-out-takes/",
    ]
    assert replaced == expected


def mock_archive_page(request: requests.Request, context: rm_Context) -> t.IO[bytes]:
    """Callback for creating mocked Response of archive page."""
    context.status_code = 200
    # resp = io.StringIO()
    resp = OFFLINE_HTML_DIR / conf.LOCAL_ARCHIVE_HTML
    return open(resp, "rb")


def test_parsing_result(requests_mock: rm_Mocker) -> None:
    """It parses mocked archived page."""
    requests_mock.get(conf.ARCHIVE_URL, body=mock_archive_page)
    parsing_result = parser.get_archive_parsing_results(conf.ARCHIVE_URL)
    all_links = parsing_result[0]
    all_texts = parsing_result[2]
    assert len(all_links) == len(all_texts)
    assert len(all_links) > 781
    assert "/2009/04/12/episode-1-introduction" in all_links[-1]
    # Intersection of mocked pages and all links
    intersection = set(MAPPING_KEYS) & set(all_links)
    assert len(intersection) > 15

    link_strings = parsing_result[2]
    assert len(link_strings) > 781


def test_parsing_invalid_html(requests_mock: rm_Mocker) -> None:
    """It returns None if page does not comply with the parsing rules."""
    markup: str = '<a class="entry" id="post">'
    requests_mock.get(conf.ARCHIVE_URL, text=markup)
    parsing_result = parser.get_archive_parsing_results(conf.ARCHIVE_URL)
    assert parsing_result == (None, None, None)


def test_parsing_archive_without_episodes() -> None:
    """It collects links only matched by episode link pattern."""
    markup = """<html><head><title>The Dormouse's story</title></head>
        <article>
            <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                and they lived at the bottom of a well.
            </p>
            <p class="story">...</p>
    """
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
    """
    soup = BeautifulSoup(markup, "lxml")
    links, texts = parser.get_all_episode_links_from_soup(soup)
    assert len(links) == 0
    assert len(texts) == 0


def mocked_single_page_matcher(
    request: requests.Request,
) -> t.Optional[requests.Response]:
    """Return OK response if URL has mocked (pre-saved) local file."""
    url = request.url.lower()
    if url in MAPPING_KEYS:
        resp = requests.Response()
        resp.status_code = 200
        return resp
    return None


def mock_single_page(request: requests.Request, context: rm_Context) -> t.IO[bytes]:
    """Callback for creating mocked Response of episode page."""
    # context.status_code = 200
    url = request.url.lower()
    local_path = OFFLINE_HTML_DIR / "ep_htmls" / LINK_FILE_MAPPING[url]
    return open(local_path, "rb")


def test_mocking_single_page(requests_mock: rm_Mocker) -> None:
    """It parses mocked episode page."""
    requests_mock.get(conf.ARCHIVE_URL, body=mock_archive_page)
    parsing_result: t.Tuple[t.List[str], ...] = parser.get_archive_parsing_results(
        conf.ARCHIVE_URL
    )
    all_links: t.List[str] = parsing_result[0]
    all_texts: t.List[str] = parsing_result[2]
    session = requests.Session()
    parsed_episodes = []

    requests_mock.get(
        req_mock.ANY,
        additional_matcher=mocked_single_page_matcher,
        body=mock_single_page,
    )

    parsed_episodes = parser.get_parsed_episodes(all_links, session, all_texts)

    non_episode_list = parser.get_parsed_episodes(
        ["https://teacherluke.co.uk/premium/archive-comment-section/"],
        session,
        ["Non-episode link"],
    )
    assert len(non_episode_list) == 0

    assert len(parsed_episodes) > 781

    min_date = datetime.strptime("2009-03-03T03:03:03+02:00", "%Y-%m-%dT%H:%M:%S%z")
    mocked_episodes = [
        ep
        for ep in parsed_episodes
        if datetime.strptime(ep.__dict__["date"], "%Y-%m-%dT%H:%M:%S%z") > min_date
    ]
    assert len(mocked_episodes) > 15

    sorted_episodes = parser.sort_episodes_by_post_date(parsed_episodes)
    assert (
        sorted_episodes[0].__dict__["url"]
        == "https://teacherluke.co.uk/2021/08/03/733-a-summer-ramble/"
    )


def test_parsing_post_datetime() -> None:
    """It gets post datetime."""
    html_doc = """<a href="https://teacherluke.co.uk/2009/04/12/episode-1-introduction/" title="3:23 pm" rel="bookmark">
            <time class="entry-date" datetime="2009-04-12T15:23:33+02:00">April 12, 2009</time>
        </a>
    """
    soup = BeautifulSoup(html_doc, "lxml")
    post_date = parser.parse_post_publish_datetime(soup)
    excepted = "2009-04-12T15:23:33+02:00"
    assert post_date == excepted


def test_parsing_post_datetime_without_element() -> None:
    """It returns default post datetime."""
    html_doc = """<a href="https://teacherluke.co.uk/2009/04/12/episode-1-introduction/" title="3:23 pm" rel="bookmark">
            <time>April 12, 2009</time>
        </a>
    """
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


def test_parsing_non_episode_link(requests_mock: rm_Mocker) -> None:
    """It returns None (empty episode) for non-episode link."""
    non_episode_url = "https://teacherluke.co.uk/premium/archive-comment-section/"
    requests_mock.get(
        non_episode_url,
        text="No need to parse this page",
        status_code=200,
    )
    link_title = "Some title"
    episode = parser.parse_single_page(non_episode_url, s, link_title)
    assert episode is None


def test_parsing_links_to_audio_for_mocked_episodes(requests_mock: rm_Mocker) -> None:
    """It parses links to audio (if they exist)."""
    # TODO: Complete test (now it's simple copy-paste)
    requests_mock.get(conf.ARCHIVE_URL, body=mock_archive_page)
    parsing_result: t.Tuple[t.List[str], ...] = parser.get_archive_parsing_results(
        conf.ARCHIVE_URL
    )
    all_links: t.List[str] = parsing_result[0]
    all_texts: t.List[str] = parsing_result[2]
    session = requests.Session()
    parsed_episodes = []

    requests_mock.get(
        req_mock.ANY,
        additional_matcher=mocked_single_page_matcher,
        body=mock_single_page,
    )

    parsed_episodes = parser.get_parsed_episodes(all_links, session, all_texts)

    assert len(parsed_episodes) > 781

    min_date = datetime.strptime("2009-03-03T03:03:03+02:00", "%Y-%m-%dT%H:%M:%S%z")
    mocked_episodes = [
        ep
        for ep in parsed_episodes
        if datetime.strptime(ep.__dict__["date"], "%Y-%m-%dT%H:%M:%S%z") > min_date
    ]
    assert len(mocked_episodes) > 15


def test_no_appropriate_mp3_links_by_title() -> None:
    """It returns empty list if there are no appropriate links."""
    markup = """\
        <!DOCTYPE html>
        <a href="http://traffic.libsyn.com/teacherluke/600._Episode_600_Livestream_Ask_Me_Anything_Audio.mp3" rel="noopener" target="_blank">
            Get Episode
        </a>
        """
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
        """
    soup = BeautifulSoup(markup, "lxml")
    list_of_audio = parser.parse_post_audio(soup)
    assert len(list_of_audio) == 2
    assert list_of_audio[0] == [
        "http://traffic.libsyn.com/teacherluke/600._Episode_600_Livestream_Ask_Me_Anything_Audio.mp3",
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
        """
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


def test_writing_lep_episodes_to_json() -> None:
    """It creates JSON file from list of LepEpisode objects."""
    lep_ep_1 = LepEpisode(
        702,
        url="https://teacherluke.co.uk/2021/01/25/702-emergency-questions-with-james/",
        index=2021012501,
    )
    # lep_ep_2_dict = {"episode": 2, "post_title": "2. Test episode #2"}  # type: t.Dict[str, object]
    # lep_ep_2 = LepEpisode(**lep_ep_2_dict)
    lep_ep_2 = LepEpisode(episode=2, post_title="2. Test episode #2")
    episodes = [
        lep_ep_1,
        lep_ep_2,
    ]
    file = Path()
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        json_file = Path(temp_file.name)
        parser.write_parsed_episodes_to_json(episodes, json_file)
        py_from_json = json.load(temp_file)
        assert len(py_from_json) == 2
        assert (
            py_from_json[0]["url"]
            == "https://teacherluke.co.uk/2021/01/25/702-emergency-questions-with-james/"
        )
        file = Path(temp_file.name)
    file.unlink()


def mock_json_db(request: requests.Request, context: rm_Context) -> t.IO[bytes]:
    """Callback for creating mocked Response of episode page."""
    # context.status_code = 200
    local_path = OFFLINE_HTML_DIR / "mocked-db-json-equal-786-objects.json"
    return open(local_path, "rb")


def test_no_new_episodes_on_archive_vs_json_db(
    requests_mock: rm_Mocker,
    capsys: CaptureFixture[str],
) -> None:
    """It prints when no new episodes on archive page."""
    requests_mock.get(conf.ARCHIVE_URL, body=mock_archive_page)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=mocked_single_page_matcher,
        body=mock_single_page,
    )
    requests_mock.get(
        conf.JSON_DB_URL,
        body=mock_json_db,
    )

    parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL)
    captured = capsys.readouterr()
    assert "There are no new episodes. Exit." in captured.out


def test_no_valid_episode_objects_in_json_db(
    requests_mock: rm_Mocker,
    capsys: CaptureFixture[str],
) -> None:
    """It prints warning when there are no valid episode objects."""
    requests_mock.get(conf.ARCHIVE_URL, body=mock_archive_page)

    requests_mock.get(
        req_mock.ANY,
        additional_matcher=mocked_single_page_matcher,
        body=mock_single_page,
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
    capsys: CaptureFixture[str],
) -> None:
    """It prints error for invalid JSON document."""
    requests_mock.get(conf.ARCHIVE_URL, body=mock_archive_page)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=mocked_single_page_matcher,
        body=mock_single_page,
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
    capsys: CaptureFixture[str],
) -> None:
    """It prints error for unavailable JSON database."""
    requests_mock.get(conf.ARCHIVE_URL, body=mock_archive_page)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=mocked_single_page_matcher,
        body=mock_single_page,
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
    capsys: CaptureFixture[str],
) -> None:
    """It prints warning for JSON as str."""
    requests_mock.get(conf.ARCHIVE_URL, body=mock_archive_page)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=mocked_single_page_matcher,
        body=mock_single_page,
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
    capsys: CaptureFixture[str],
) -> None:
    """It skips invalid objects in JSON database."""
    requests_mock.get(conf.ARCHIVE_URL, body=mock_archive_page)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=mocked_single_page_matcher,
        body=mock_single_page,
    )
    requests_mock.get(
        conf.JSON_DB_URL,
        text='[{"episode": 1, "fake_key": "Skip me"}]',
    )

    parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL)
    captured = capsys.readouterr()
    assert "[WARNING]" in captured.out
    assert "no valid episode objects" in captured.out


def modified_json_db(request: requests.Request, context: rm_Context) -> str:
    """Callback for creating mocked JSON database with less episodes."""
    # context.status_code = 200
    local_path = OFFLINE_HTML_DIR / "mocked-db-json-equal-786-objects.json"
    mocked_json = local_path.read_text(encoding="utf-8")
    db_episodes = json.loads(mocked_json, object_hook=parser.as_lep_episode_obj)
    # Delete three episodes
    del db_episodes[0]
    del db_episodes[1]
    del db_episodes[6]
    modified_json = json.dumps(db_episodes, cls=lep.LepJsonEncoder)
    return modified_json


def test_updating_json_database_with_new_episodes(
    requests_mock: rm_Mocker,
) -> None:
    """It retrives and saves new episodes from archive."""
    requests_mock.get(conf.ARCHIVE_URL, body=mock_archive_page)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=mocked_single_page_matcher,
        body=mock_single_page,
    )
    requests_mock.get(
        conf.JSON_DB_URL,
        text=modified_json_db,
    )

    with tempfile.NamedTemporaryFile(prefix="LEP_tmp_", delete=False) as temp_file:
        json_file = Path(temp_file.name)
        parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL, json_file)
        py_from_json = json.load(temp_file, object_hook=parser.as_lep_episode_obj)
    json_file.unlink()

    assert len(py_from_json) == 786


def modified_json_with_extra_episode(
    request: requests.Request,
    context: rm_Context,
) -> str:
    """Callback for creating mocked JSON database with more episodes."""
    local_path = OFFLINE_HTML_DIR / "mocked-db-json-equal-786-objects.json"
    mocked_json = local_path.read_text(encoding="utf-8")
    db_episodes = json.loads(mocked_json, object_hook=parser.as_lep_episode_obj)
    # Add extra episode
    lep_ep = LepEpisode(episode=999, post_title="Extra episode")
    db_episodes.append(lep_ep)
    modified_json = json.dumps(db_episodes, cls=lep.LepJsonEncoder)
    return modified_json


def test_updating_json_database_with_extra_episodes(
    requests_mock: rm_Mocker,
    capsys: CaptureFixture[str],
) -> None:
    """It prints warning if database contains more episodes than archive."""
    requests_mock.get(conf.ARCHIVE_URL, body=mock_archive_page)
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=mocked_single_page_matcher,
        body=mock_single_page,
    )
    requests_mock.get(
        conf.JSON_DB_URL,
        text=modified_json_with_extra_episode,
    )

    parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL)
    captured = capsys.readouterr()
    assert "[WARNING]" in captured.out
    assert "Database contains more episodes than current archive!" in captured.out


def test_parsing_invalid_html_in_main_actions(
    requests_mock: rm_Mocker,
    capsys: CaptureFixture[str],
) -> None:
    """It prints error when no episode links on archive page."""
    markup: str = '<a class="entry" id="post">'
    requests_mock.get(conf.ARCHIVE_URL, text=markup)
    parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL)
    captured = capsys.readouterr()
    assert "[ERROR]" in captured.out
    assert "Can't parse any episodes from archive page." in captured.out


def test_encoding_non_serializable_json_object() -> None:
    """It raises exception TypeError for non-serializable types."""
    obj = [complex(2 + 1)]
    with pytest.raises(TypeError):
        _ = json.dumps(obj, cls=lep.LepJsonEncoder)
