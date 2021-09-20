"""Test cases for the parser module."""
from pathlib import Path
import typing as t

from bs4 import BeautifulSoup
import pytest
import requests
import requests_mock as req_mock
from requests_mock.mocker import Mocker as rm_Mocker
from requests_mock.response import _Context as rm_Context

from lep_downloader import config as conf
from lep_downloader import parser

OFFLINE_HTML_DIR = Path(
    Path(__file__).resolve().parent,
    "fixtures",
)

LINK_FILE_MAPPING = {
    "https://teacherluke.co.uk/2009/04/12/episode-1-introduction/": \
        "2021-09-13_05-37-36 teacherluke.co.uk _2009_04_12_episode-1-introduction_.html",

    "https://teacherluke.co.uk/2009/10/19/extra-podcast-12-phrasal-verbs/": \
        "2021-09-07_09-14-02 teacherluke.co.uk _2009_10_19_extra-podcast-12-phrasal-verbs_.html",

    "https://teacherluke.co.uk/2009/10/19/episode-11-michael-jackson/": \
        "2021-09-07_09-14-02 teacherluke.co.uk _2009_10_19_episode-11-michael-jackson_.html",

    "https://teacherluke.co.uk/2010/03/25/london-video-interviews-pt-1/": \
        "2021-09-07_09-14-02 teacherluke.co.uk _2010_03_25_london-video-interviews-pt-1_.html",

    "http://teacherluke.wordpress.com/2012/09/27/113-setting-the-world-to-rights/": \
        "2021-09-07_09-14-02 teacherluke.wordpress.com _2012_09_27_113-setting-the-world-to-rights_.html",

    "https://teacherluke.co.uk/2014/06/30/193-culture-shock-life-in-london-pt-2/": \
        "2021-09-07_09-14-02 teacherluke.co.uk _2014_06_30_193-culture-shock-life-in-london-pt-2_.html",

    "https://teacherluke.co.uk/2015/10/21/304-back-to-the-future-part-1/": \
        "2021-09-07_09-14-02 teacherluke.co.uk _2015_10_07_300-episode-300-part-1_.html",

    "https://teacherluke.co.uk/2015/10/22/305-back-to-the-future-part-2/": \
        "2021-09-07_09-14-02 teacherluke.co.uk _2015_10_07_300-episode-300-part-2_.html",

    "https://teacherluke.co.uk/2016/08/07/370-in-conversation-with-rob-ager-from-liverpool-part-1-life-in-liverpool-interest-in-film-analysis/": \
        "2021-09-07_09-14-02 teacherluke.co.uk _2016_08_07_370-in-conversation-with-rob-ager-from.html",

    "https://teacherluke.co.uk/2017/03/11/lep-on-zep-my-recent-interview-on-zdeneks-english-podcast/": \
        "2021-09-07_09-14-02 teacherluke.co.uk _2017_03_11_lep-on-zep-my-recent-interview-on-zden.html",

    "https://teacherluke.co.uk/2017/05/26/i-was-invited-onto-the-english-across-the-pond-podcast/": \
        "2021-09-07_09-14-02 teacherluke.co.uk _2017_05_26_i-was-invited-onto-the-english-across-.html",

    "https://teacherluke.co.uk/2017/08/26/website-only-a-history-of-british-pop-a-musical-tour-through-james-vinyl-collection/": \
        "2021-09-07_09-14-02 teacherluke.co.uk _2017_08_26_website-only-a-history-of-british-pop-.html",

    "https://teacherluke.co.uk/2021/02/03/703-walaa-from-syria-wisbolep-competition-winner-%f0%9f%8f%86/": \
        "2021-08-11_lep-e703-page-content-pretty.html",

    "https://teacherluke.co.uk/2021/03/26/711-william-from-france-%f0%9f%87%ab%f0%9f%87%b7-wisbolep-runner-up/": \
        "2021-08-11_lep-e711-page-content-pretty.html",

    "https://teacherluke.co.uk/2021/04/11/714-robin-from-hamburg-%f0%9f%87%a9%f0%9f%87%aa-wisbolep-runner-up/": \
        "2021-09-07_09-14-02 teacherluke.co.uk _2021_04_11_714-robin-from-hamburg-🇩🇪-wisbolep-run.html",

    "https://teacherluke.co.uk/2021/08/03/733-a-summer-ramble/": \
        "2021-08-11_lep-e733-page-content-pretty.html",
}

MAPPING_KEYS: t.List[str] = [*LINK_FILE_MAPPING]

s = requests.Session()


def test_getting_success_page_response(requests_mock: rm_Mocker) -> None:
    """It gets HTML content as text."""
    requests_mock.get(req_mock.ANY, text="Response OK")
    resp = parser.get_web_page_html_text(conf.ARCHIVE_URL, s)
    assert resp == "Response OK"


def test_getting_404_page_response(requests_mock: rm_Mocker) -> None:
    """It raises HTTPError if page is not found."""
    requests_mock.get(req_mock.ANY, text="Response OK", status_code=404)
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        parser.get_web_page_html_text(conf.ARCHIVE_URL, s)
    assert exc_info.typename == "HTTPError"


def test_getting_503_page_response(requests_mock: rm_Mocker) -> None:
    """It raises HTTPError if service is unavailable."""
    requests_mock.get(req_mock.ANY, text="Response OK", status_code=503)
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        parser.get_web_page_html_text(conf.ARCHIVE_URL, s)
    assert exc_info.typename == "HTTPError"


def test_retrieve_all_links_from_soup() -> None:
    """It returns only <a> tags from soup object."""
    html_doc = """<html><head><title>The Dormouse's story</title></head>
        <body>
            <p class="title"><b>The Dormouse's story</b></p>
            <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
                <a href="http://example.com/Sara" class="sister" id="link2">Sara</a> and
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                and they lived at the bottom of a well.
            </p>
            <p class="story">...</p>
    """
    soup = BeautifulSoup(html_doc, "lxml")
    only_links = parser.get_all_links_from_soup(soup)
    assert len(only_links) == 3


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
    new_list: t.List[str] = parser.remove_irrelevant_links(test_list)
    assert len(new_list) == 3


def test_removing_not_episode_links() -> None:
    """It removes links from list which are not match by regex pattern."""
    test_list: t.List[str] = [
        "https://teacherluke.co.uk/2020/11/23/wisbolep/",
        "https://teacherluke.co.uk/premium/archive-comment-section/",  # <- bad
        "https://teacherluke.co.uk/2014/04/01/177-what-londoners-say-vs-what-they-mean/",
        "https://teacherluke.co.uk/2021/03/26/711-william-from-france-%f0%9f%87%ab%f0%9f%87%b7-wisbolep-runner-up/",
        "http://wp.me/p4IuUx-7sg",
        "http://teacherluke.wordpress.com/2012/09/27/113-setting-the-world-to-rights/",
        "https://example.com/",  # <- bad
    ]
    new_list: t.List[str] = parser.remove_not_episode_links_by_regex_pattern(test_list)
    assert len(new_list) == 5


def test_getting_links_text_by_href() -> None:
    """It gets list of link texts, searching by their 'href' attribute."""
    html_doc: str = """<html><head><title>The Dormouse's story</title></head>
        <body>
            <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
                <a href="https://teacherluke.co.uk/2017/05/26/i-was-invited-onto-the-english-across-the-pond-podcast/" class="sister" id="link2">
                    Link from dict</a> and
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                <a href="http://example.com/spaces" class="sister" id="link3">  Text with spaces   
                    </a>;
                and they lived at the bottom of a well.
            </p>
            <a href="http://example.com/john" class="sister" id="link3">4th sister is John!</a>;

    """
    search_links: t.List[str] = [
        "https://teacherluke.co.uk/2017/05/26/i-was-invited-onto-the-english-across-the-pond-podcast/",
        "http://example.com/spaces",
        "http://example.com/john",
    ]
    soup = BeautifulSoup(html_doc, "lxml")
    texts = parser.get_links_text_by_href(soup, search_links)
    expected_texts: t.List[str] = [
        "[Website content] I was invited onto the “English Across The Pond” Podcast",
        "Text with spaces",
        "4th sister is John!",
    ]
    assert texts == expected_texts


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
    """"Callback for creating mocked Response of archive page."""
    context.status_code = 200
    # resp = io.StringIO()
    resp = OFFLINE_HTML_DIR / conf.LOCAL_ARCHIVE_HTML
    return open(resp, "rb")


def test_parsing_result(requests_mock: rm_Mocker) -> None:
    """It parses mocked archived page."""
    requests_mock.get(conf.ARCHIVE_URL, body=mock_archive_page)
    parsing_result = parser.get_archive_parsing_results(conf.ARCHIVE_URL)
    all_links = parsing_result[0]
    assert all_links is not None
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
    assert parsing_result is None


def mocked_single_page_matcher(request: requests.Request) -> t.Optional[requests.Response]:
    """Return OK response if URL has mocked (pre-saved) local file."""
    url = request.url.lower()
    if url in MAPPING_KEYS:
        resp = requests.Response()
        resp.status_code = 200
        return resp
    return None


def mock_single_page(request: requests.Request, context: rm_Context) -> t.IO[bytes]:
    """"Callback for creating mocked Response of episode page."""
    # context.status_code = 200
    url = request.url.lower()
    local_path = OFFLINE_HTML_DIR / "ep_htmls" / LINK_FILE_MAPPING[url]
    return open(local_path, "rb")


def test_mocking_single_page(requests_mock: rm_Mocker) -> None:
    """It parses mocked episode page."""
    requests_mock.get(conf.ARCHIVE_URL, body=mock_archive_page)
    parsing_result: t.Tuple[t.List[str], ...] = parser.get_archive_parsing_results(conf.ARCHIVE_URL)
    all_links: t.List[str] = parsing_result[0]

    session = requests.Session()
    titles = []
    for url in all_links:
        try:
            requests_mock.get(url, additional_matcher=mocked_single_page_matcher, body=mock_single_page)
            title = parser.parse_single_page(url, session)
            titles.append(title)
        except req_mock.exceptions.NoMockAddress:
            pass
    assert len(titles) > 15
