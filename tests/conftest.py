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
"""Package-wide test fixtures."""
import copy
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import Tuple

import pytest
import requests
import requests_mock as req_mock
from click.testing import CliRunner
from click.testing import Result
from pytest import TempPathFactory
from requests_mock.mocker import Mocker as rm_Mocker
from requests_mock.request import _RequestObjectProxy
from requests_mock.response import _Context as rm_Context


DataForEpisodeAudio = List[Tuple[str, str, List[List[str]], bool]]
NamesWithAudios = List[Tuple[str, List[str]]]

# yapf: disable
URL_HTML_MAPPING = {
    "https://teacherluke.co.uk/2009/04/12/episode-1-introduction/":
        "2021-09-13_05-37-36 teacherluke.co.uk _2009_04_12_episode-1-introduction_.html",  # noqa: E501,B950
    "https://teacherluke.co.uk/2009/10/19/extra-podcast-12-phrasal-verbs/":
        "2021-09-07_09-14-02 teacherluke.co.uk _2009_10_19_extra-podcast-12-phrasal-verbs_.html",  # noqa: E501,B950
    "https://teacherluke.co.uk/2009/10/19/episode-11-michael-jackson/":
        "2021-09-07_09-14-02 teacherluke.co.uk _2009_10_19_episode-11-michael-jackson_.html",  # noqa: E501,B950
    "https://teacherluke.co.uk/2010/03/25/london-video-interviews-pt-1/":
        "2021-09-07_09-14-02 teacherluke.co.uk _2010_03_25_london-video-interviews-pt-1_.html",  # noqa: E501,B950
    "http://teacherluke.wordpress.com/2012/09/27/113-setting-the-world-to-rights/":  # noqa: E501,B950
        "2021-09-07_09-14-02 teacherluke.wordpress.com _2012_09_27_113-setting-the-world-to-rights_.html",  # noqa: E501,B950
    "https://teacherluke.co.uk/2014/06/30/193-culture-shock-life-in-london-pt-2/":  # noqa: E501,B950
        "2021-09-07_09-14-02 teacherluke.co.uk _2014_06_30_193-culture-shock-life-in-london-pt-2_.html",  # noqa: E501,B950
    "https://teacherluke.co.uk/2015/10/21/304-back-to-the-future-part-1/":
        "2021-09-07_09-14-02 teacherluke.co.uk _2015_10_07_300-episode-300-part-1_.html",  # noqa: E501,B950
    "https://teacherluke.co.uk/2015/10/22/305-back-to-the-future-part-2/":
        "2021-09-07_09-14-02 teacherluke.co.uk _2015_10_07_300-episode-300-part-2_.html",  # noqa: E501,B950
    "https://teacherluke.co.uk/2016/08/07/370-in-conversation-with-rob-ager-from-liverpool-part-1-life-in-liverpool-interest-in-film-analysis/":  # noqa: E501,B950
        "2021-09-07_09-14-02 teacherluke.co.uk _2016_08_07_370-in-conversation-with-rob-ager-from.html",  # noqa: E501,B950
    "https://teacherluke.co.uk/2017/03/11/lep-on-zep-my-recent-interview-on-zdeneks-english-podcast/":  # noqa: E501,B950
        "2021-09-07_09-14-02 teacherluke.co.uk _2017_03_11_lep-on-zep-my-recent-interview-on-zden.html",  # noqa: E501,B950
    "https://teacherluke.co.uk/2017/05/26/i-was-invited-onto-the-english-across-the-pond-podcast/":  # noqa: E501,B950
        "2021-09-07_09-14-02 teacherluke.co.uk _2017_05_26_i-was-invited-onto-the-english-across-.html",  # noqa: E501,B950
    "https://teacherluke.co.uk/2017/08/26/website-only-a-history-of-british-pop-a-musical-tour-through-james-vinyl-collection/":  # noqa: E501,B950
        "2021-09-07_09-14-02 teacherluke.co.uk _2017_08_26_website-only-a-history-of-british-pop-.html",  # noqa: E501,B950
    "https://teacherluke.co.uk/2021/02/03/703-walaa-from-syria-wisbolep-competition-winner-%f0%9f%8f%86/":  # noqa: E501,B950
        "2021-08-11_lep-e703-page-content-pretty.html",
    "https://teacherluke.co.uk/2021/03/26/711-william-from-france-%f0%9f%87%ab%f0%9f%87%b7-wisbolep-runner-up/":  # noqa: E501,B950
        "2021-08-11_lep-e711-page-content-pretty.html",
    "https://teacherluke.co.uk/2021/04/11/714-robin-from-hamburg-%f0%9f%87%a9%f0%9f%87%aa-wisbolep-runner-up/":  # noqa: E501,B950
        "2021-09-07_09-14-02 teacherluke.co.uk _2021_04_11_714-robin-from-hamburg-🇩🇪-wisbolep-run.html",  # noqa: E501,B950
    "https://teacherluke.co.uk/2021/08/03/733-a-summer-ramble/":
        "2021-08-11_lep-e733-page-content-pretty.html",
    "https://teacherluke.co.uk/premium/archive-comment-section/":
        "2021-09-28_10-44-00 Archive & Comment Section _ (premium archive).html",  # noqa: E501,B950  # None-episode link
}
# yapf: enable


@pytest.fixture(scope="session")
def req_ses() -> requests.Session:
    """Returns global (for all tests) requests session."""
    s = requests.Session()
    return s


@pytest.fixture(scope="session")
def url_html_map() -> Dict[str, str]:
    """Returns dictionary of mocked URLs and their HTML files."""
    return URL_HTML_MAPPING


@pytest.fixture(scope="session")
def mocked_urls(url_html_map: Dict[str, str]) -> List[str]:
    """Returns list of mocked URLs."""
    return [*url_html_map]


@pytest.fixture(scope="session")
def mocks_dir_path() -> Path:
    """Returns path to 'fixtures' direcory."""
    fixtures_dir = Path(
        Path(__file__).resolve().parent,
        "fixtures",
    )
    return fixtures_dir


@pytest.fixture(scope="module")
def html_mocks_path(mocks_dir_path: Path) -> Path:
    """Returns path to 'ep_htmls' sub-direcory of mocks."""
    html_dir = mocks_dir_path / "ep_htmls"
    return html_dir


@pytest.fixture(scope="module")
def archive_page_mock(mocks_dir_path: Path) -> str:
    """Returns str object of archive HTML mocked page."""
    from lep_downloader import config as conf

    page_path = mocks_dir_path / conf.LOCAL_ARCHIVE_HTML
    return page_path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def single_page_mock(
    html_mocks_path: Path,
    url_html_map: Dict[str, str],
) -> Callable[[requests.Request, rm_Context], str]:
    """Returns custom callback for mocking."""

    def _mock_single_page(
        request: requests.Request,
        context: rm_Context,
    ) -> str:
        """Callback for creating mocked Response of episode page."""
        url = request.url.lower()
        page_path = html_mocks_path / url_html_map[url]
        return page_path.read_text(encoding="utf-8")

    return _mock_single_page


@pytest.fixture(scope="module")
def single_page_matcher(
    mocked_urls: List[str],
) -> Optional[Callable[[_RequestObjectProxy], bool]]:
    """Returns custom matcher callback."""

    def _single_page_matcher(
        request: _RequestObjectProxy,
    ) -> bool:
        """Return True response if URL has mocked (pre-saved) local file."""
        url = request.url.lower()
        return url in mocked_urls

    return _single_page_matcher


@pytest.fixture(scope="session")
def json_db_mock(mocks_dir_path: Path) -> str:
    """Returns str object of JSON mocked database."""
    from lep_downloader import config as conf

    json_path = mocks_dir_path / conf.LOCAL_JSON_DB
    return json_path.read_text(encoding="utf-8")


@pytest.fixture
def db_episodes(json_db_mock: str) -> List[object]:
    """Returns reusable list of LepEpisode objects from JSON mocked database."""
    from lep_downloader import lep

    db_episodes: List[object] = json.loads(
        json_db_mock,
        object_hook=lep.as_lep_episode_obj,
    )
    return db_episodes


@pytest.fixture
def modified_json_less_db_mock(db_episodes: List[object]) -> str:
    """Returns mocked JSON database with less episodes."""
    from lep_downloader import lep

    # Delete three episodes
    del db_episodes[0]  # Remove '733'
    del db_episodes[0]  # Remove '714'
    del db_episodes[4]  # Remove 'LEP on ZEP'
    modified_json = json.dumps(db_episodes, cls=lep.LepJsonEncoder)
    del db_episodes
    return modified_json


@pytest.fixture
def modified_json_extra_db_mock(db_episodes: List[object]) -> str:
    """Returns mocked JSON database with plus one episode."""
    from lep_downloader import lep

    lep_ep = lep.LepEpisode(episode=999, post_title="Extra episode")
    db_episodes.append(lep_ep)  # Add extra episode
    modified_json = json.dumps(db_episodes, cls=lep.LepJsonEncoder)
    del db_episodes
    return modified_json


@pytest.fixture
def archive_parsing_results_mock(
    requests_mock: rm_Mocker,
    archive_page_mock: str,
    req_ses: requests.Session,
) -> Dict[str, str]:
    """Returns two lists: links and texts from mocked archive page."""
    from lep_downloader import config as conf
    from lep_downloader import parser
    from lep_downloader.lep import Archive

    requests_mock.get(conf.ARCHIVE_URL, text=archive_page_mock)
    archive_parser = parser.ArchiveParser(conf.ARCHIVE_URL, req_ses)
    archive_parser.parse_url()
    archive_urls = Archive.collected_links.copy()
    del archive_parser
    return archive_urls


@pytest.fixture
def parsed_episodes_mock(
    requests_mock: rm_Mocker,
    archive_parsing_results_mock: Dict[str, str],
    single_page_mock: str,
    single_page_matcher: Optional[Callable[[_RequestObjectProxy], bool]],
    req_ses: requests.Session,
) -> Any:
    """Returns list of LepEpisode objects.

    Mocked episodes among others, with parsed (not default) post date.
    """
    from lep_downloader import parser
    from lep_downloader.lep import Archive
    from lep_downloader.lep import LepEpisodeList

    Archive.episodes = LepEpisodeList()

    parsed_episodes: LepEpisodeList
    requests_mock.get(
        req_mock.ANY,
        additional_matcher=single_page_matcher,
        text=single_page_mock,
    )
    parser.parse_each_episode(archive_parsing_results_mock, req_ses)
    parsed_episodes = copy.deepcopy(Archive.episodes)
    return parsed_episodes


@pytest.fixture
def mocked_episodes(
    parsed_episodes_mock: List[Any],
) -> List[Any]:
    """Fixture with episodes which have HTML mock page only."""
    lep_date_format = "%Y-%m-%dT%H:%M:%S%z"
    min_date = datetime.strptime(
        "2009-03-03T03:03:03+02:00",
        lep_date_format,
    )
    mocked_episodes = [
        ep
        for ep in parsed_episodes_mock
        if datetime.strptime(ep.date, lep_date_format) > min_date
    ]
    return mocked_episodes


@pytest.fixture(scope="session")
def lep_temp_path(tmp_path_factory: TempPathFactory) -> Iterator[Path]:
    """Returns path to custom temp directory.

    This fixture is redundant, but it lets to clear
    the base pytest temp directory at the end of session.
    https://github.com/pytest-dev/pytest/issues/8141
    If disc space is not a problem - can be replaced with 'tmp_path'
    """
    temp_path = tmp_path_factory.mktemp("lep_tmp")
    yield temp_path
    # Cleanup all folders in fixture's base temp directory
    shutil.rmtree(tmp_path_factory.getbasetemp().resolve())
    # If we clean base temp directory itself
    # 'typeguard' will warn on Windows hosts
    # tmp_path_factory.getbasetemp().parent.rmdir()


@pytest.fixture(scope="module")
def mp3_mocks_path(mocks_dir_path: Path) -> Path:
    """Returns path to 'mp3' sub-direcory of mocks."""
    mp3_dir = mocks_dir_path / "mp3"
    return mp3_dir


@pytest.fixture(scope="module")
def mp3_file1_mock(mp3_mocks_path: Path) -> bytes:
    """Returns bytes of the first mocked mp3 file."""
    mocked_file_1 = mp3_mocks_path / "test_lep_audio1.mp3"
    return mocked_file_1.read_bytes()


@pytest.fixture(scope="module")
def mp3_file2_mock(mp3_mocks_path: Path) -> bytes:
    """Returns bytes of the second mocked mp3 file."""
    mocked_file_2 = mp3_mocks_path / "test_lep_audio2.mp3"
    return mocked_file_2.read_bytes()


@pytest.fixture(scope="session")
def only_valid_episodes(json_db_mock: str) -> List[Any]:
    """Returns list of valid LepEpisode objects from JSON mocked database."""
    from lep_downloader import data_getter

    mocked_db_episodes = data_getter.get_list_of_valid_episodes(json_db_mock)
    return mocked_db_episodes


@pytest.fixture(scope="session")
def only_audio_episodes(only_valid_episodes: List[Any]) -> List[Any]:
    """Returns only audio episodes from all."""
    from lep_downloader import downloader

    audio_episodes = downloader.select_all_audio_episodes(only_valid_episodes)
    return audio_episodes


@pytest.fixture(scope="session")
def only_audio_data(only_audio_episodes: List[Any]) -> DataForEpisodeAudio:
    """Returns only extracted audio data from audio episodes."""
    from lep_downloader import downloader

    audio_data = downloader.get_audios_data(only_audio_episodes)
    return audio_data


@pytest.fixture(scope="session")
def only_audio_links(only_audio_data: DataForEpisodeAudio) -> NamesWithAudios:
    """Returns only links and names for audio files."""
    from lep_downloader import downloader

    audio_links = downloader.bind_name_and_file_url(only_audio_data)
    return audio_links


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


@pytest.fixture
def run_cli_with_args(runner: CliRunner) -> Callable[[List[str]], Result]:
    """Fixture for getting CLI runner result for this package."""
    from lep_downloader import cli

    def _my_pkg_result(cli_args: List[str]) -> Result:
        result = runner.invoke(
            cli.cli,
            cli_args,
            prog_name="lep-downloader",
        )
        return result

    return _my_pkg_result
