"""Test cases for the parser module."""
from pathlib import Path

import pytest
import requests
import requests_mock as req_mock

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

MAPPING_KEYS = [*LINK_FILE_MAPPING]


def mock_archive_page(request, context):
    """"Callback for creating mocked Response."""
    context.status_code = 200
    # resp = io.StringIO()
    resp = OFFLINE_HTML_DIR / conf.LOCAL_ARCHIVE_HTML
    return open(resp, "rb")


def test_parsing_result(requests_mock) -> None:
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


def mocked_single_page_matcher(request):
    """Return local file instead of real web page."""
    url = request.url.lower()
    if url in MAPPING_KEYS:
        resp = requests.Response()
        resp.status_code = 200
        return resp
    return None


def mock_single_page(request, context):
    """"Callback for creating mocked Response."""
    # context.status_code = 200
    url = request.url.lower()
    local_path = OFFLINE_HTML_DIR / "ep_htmls" / LINK_FILE_MAPPING[url]
    return open(local_path, "rb")


def test_mocking_single_page(requests_mock) -> None:
    """It parses mocked archived page."""
    requests_mock.get(conf.ARCHIVE_URL, body=mock_archive_page)
    parsing_result = parser.get_archive_parsing_results(conf.ARCHIVE_URL)
    all_links = parsing_result[0]

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