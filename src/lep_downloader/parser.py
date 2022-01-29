"""LEP module for parsing logic."""
import json
import re
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

import requests
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from bs4.element import Tag

from lep_downloader import config as conf
from lep_downloader.downloader import LepDL
from lep_downloader.exceptions import LepEpisodeNotFound
from lep_downloader.exceptions import NoEpisodeLinksError
from lep_downloader.exceptions import NoEpisodesInDataBase
from lep_downloader.exceptions import NotEpisodeURLError
from lep_downloader.lep import Lep
from lep_downloader.lep import LepEpisode
from lep_downloader.lep import LepEpisodeList
from lep_downloader.lep import LepJsonEncoder


# COMPILED REGEX PATTERNS #

EP_LINK_PATTERN = re.compile(conf.EPISODE_LINK_RE, re.IGNORECASE)

duplicated_ep_links_re = r"^\[(website\scontent|video)\]$|episode\s522$"
DUPLICATED_EP_PATTERN = re.compile(duplicated_ep_links_re, re.IGNORECASE)

begining_digits_re = r"^\d{1,5}"
BEGINING_DIGITS_PATTERN = re.compile(begining_digits_re)

audio_link_re = r"download\b|audio\s|click\s"
AUDIO_LINK_PATTERN = re.compile(audio_link_re, re.IGNORECASE)


# SoupStrainer's CALLBACKS #

only_article_content = SoupStrainer("article")
only_a_tags_with_ep_link = SoupStrainer("a", href=EP_LINK_PATTERN)
only_a_tags_with_mp3 = SoupStrainer(
    "a",
    href=re.compile(r"^(?!.*boos/(2794795|3727124))(?!.*uploads).*\.mp3$", re.I),
)


class Archive(Lep):
    """Represent archive page object."""

    def __init__(
        self,
        url: str = conf.ARCHIVE_URL,
        session: requests.Session = None,
    ) -> None:
        """Initialize an archive instance."""
        super().__init__(session)
        self.url = url
        self.parser = ArchiveParser(self, self.url)
        self.collected_links: Dict[str, str] = {}
        self.deleted_links: Set[str] = set()
        self.used_indexes: Set[int] = set()
        self.episodes: LepEpisodeList = LepEpisodeList()

    def fetch_updates(
        self,
        db_episodes: LepEpisodeList,
        archive_urls: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Fetch only new URLs between database and archive page."""
        archive_urls = archive_urls if archive_urls else self.collected_links
        # TODO (hotenov): Here method .lower() for URL it's not quite right,
        # need to replace with regex
        db_urls = {ep.url.lower(): ep.post_title for ep in db_episodes}
        last_url: str = [*db_urls][0]
        date_of_last_db_episode = convert_date_from_url(last_url)
        updates = {
            url: text
            for url, text in archive_urls.items()
            if convert_date_from_url(url) > date_of_last_db_episode
        }
        if len(db_urls) > len(archive_urls):
            return None
        else:
            return updates

    def parse_each_episode(
        self,
        urls: Dict[str, str],
    ) -> None:
        """Parse each episode collected from archive page.

        In for cycle: reversed collected links in order to start
            from first episode to last in parsing action.
        """
        # mypy warns only for Python 3.7.0 and below.
        # https://docs.python.org/3/library/typing.html#typing.Reversible
        for url, text in reversed(urls.items()):
            try:
                ep_parser = EpisodeParser(self, url, post_title=text)
                ep_parser.parse_url()
                self.episodes.append(ep_parser.episode)
            except (NotEpisodeURLError):
                # TODO (hotenov): Write to log / statistics
                # for non-episode URL, but skip here
                continue
            except (LepEpisodeNotFound) as ex:
                not_found_episode = ex.args[0]
                self.episodes.append(not_found_episode)
                continue

    def do_parsing_actions(
        self,
        json_url: str,
        json_name: str = conf.DEFAULT_JSON_NAME,
    ) -> None:
        """Main methdod to do parsing job."""
        updates: Dict[str, str] = {}

        # Collect (get and parse) links and their texts from web archive page.
        self.parser.parse_url()

        # Get database episodes from web JSON
        lep_dl = LepDL(json_url, self.session)
        lep_dl.use_or_get_db_episodes()
        if lep_dl.db_episodes:
            updates = self.fetch_updates(lep_dl.db_episodes, self.collected_links)
        else:
            raise NoEpisodesInDataBase(
                "JSON is available, but\nthere are NO episodes in this file. Exit."
            )
        if updates is None:
            print(
                "[WARNING]: Database contains more episodes",
                "than current archive!",
            )
            return None
        if len(updates) > 0:
            # Parse new episodes and add them to shared class list
            # with parsed episodes (list empty until this statement)
            self.parse_each_episode(updates)
            new_episodes = self.episodes
            new_episodes = LepEpisodeList(reversed(new_episodes))
            all_episodes = LepEpisodeList(new_episodes + lep_dl.db_episodes)
            all_episodes = all_episodes.desc_sort_by_date_and_index()
            write_parsed_episodes_to_json(all_episodes, json_name)
        else:
            print("There are no new episodes. Exit.")
            return None


def is_tag_a_repeated(tag_a: Tag) -> bool:
    """Returns True for appropriate link to episode."""
    tag_text = tag_a.get_text()
    is_repeated = False
    match = DUPLICATED_EP_PATTERN.search(tag_text.strip())
    is_repeated = False if match else True
    return is_repeated


def parse_post_publish_datetime(soup: BeautifulSoup) -> str:
    """Returns post datetime as string."""
    date_value: str = ""
    tag_entry_datetime = soup.find("time", class_="entry-date")
    if tag_entry_datetime is not None:
        date_value = tag_entry_datetime["datetime"]
    else:
        date_value = "1999-01-01T01:01:01+02:00"
    return date_value


def parse_episode_number(post_title: str) -> int:
    """Returns episode number."""
    match = BEGINING_DIGITS_PATTERN.match(post_title)
    if match:
        return int(match.group())
    else:
        return 0


def generate_post_index(post_url: str, indexes: Set[int]) -> int:
    """Returns index number for post."""
    match = EP_LINK_PATTERN.match(post_url)
    if match:
        groups_dict = match.groupdict()
        date_from_url = groups_dict["date"]
        date_numbers = date_from_url.replace("/", "")

        # Generate index using URL date, format example: 2021120101
        new_index = int(date_numbers + "1".zfill(2))
        exists = False
        while not exists:
            if new_index in indexes:
                new_index += 1
            else:
                indexes.add(new_index)
                exists = True
        return new_index
    else:
        return 0


def has_tag_a_appropriate_audio(tag_a: Tag) -> bool:
    """Returns True for appropriate link to audio."""
    tag_text = tag_a.get_text()
    if "http" in tag_text:
        return False
    else:
        is_appropriate = False
        match = AUDIO_LINK_PATTERN.search(tag_text)
        is_appropriate = True if match else False
        return is_appropriate


def parse_post_audio(soup: BeautifulSoup) -> List[List[str]]:
    """Returns list of lists with links to audio."""
    audios: List[List[str]] = []

    soup_a_only = BeautifulSoup(
        str(soup),
        features="lxml",
        parse_only=only_a_tags_with_mp3,
    )

    if len(soup_a_only) > 1:
        tags_a_audio = soup_a_only.find_all(
            has_tag_a_appropriate_audio,
            recursive=False,
        )
        if len(tags_a_audio) > 0:
            for tag_a in tags_a_audio:
                audio = [tag_a["href"]]
                audios.append(audio)
            return audios
        else:
            return audios
    else:
        return audios


def extract_date_from_url(url: str) -> str:
    """Parse date from URL in YYYY/MM/DD format."""
    match = EP_LINK_PATTERN.match(url)
    if match:
        groups_dict = match.groupdict()
        date_from_url = groups_dict["date"]
        return date_from_url
    else:
        return ""


def convert_date_from_url(url: str) -> datetime:
    """Convert URL string with date YYYY/MM/DD to datetime object."""
    url_date = extract_date_from_url(url)
    return datetime.strptime(url_date, r"%Y/%m/%d")


def write_parsed_episodes_to_json(
    lep_objects: LepEpisodeList,
    json_name: str = conf.DEFAULT_JSON_NAME,
) -> None:
    """Write list of LepEpisode objects to file."""
    with open(Path(json_name), "w") as outfile:
        json.dump(lep_objects, outfile, indent=4, cls=LepJsonEncoder)


class LepParser(Lep):
    """Base class for LEP archive parsers."""

    def __init__(
        self,
        archive_obj: Archive,
        url: str,
        session: requests.Session = None,
    ) -> None:
        """Initialize LepParser object.

        Args:
            archive_obj (Archive): Instance of Archive object
                to put and use data in its containers attributes.
            url (str): URL for parsing.
            session (requests.Session): Requests session object
                if None, get default global session.
        """
        super().__init__(session)
        self.archive = archive_obj
        self.url = url
        self.content: str = ""
        self.soup: BeautifulSoup = None
        self.final_location: str = self.url
        self.is_url_ok: bool = False

    def get_url(self) -> None:
        """Retrive text content of archive web page."""
        get_result = Lep.get_web_document(self.url, self.session)
        self.content = get_result[0]
        self.final_location = get_result[1]
        self.is_url_ok = get_result[2]

    def do_pre_parsing(self) -> None:
        """Extract useful data before and prepare for parsing.

        For archive page - Substitute link with '.ukm' misspelled TLD.
        For episode page - Generate index, parsed_at; parse episode number, etc.
        """
        raise NotImplementedError()

    def parse_dom_for_article_container(self) -> None:
        """Parse DOM for <article> tag only."""
        self.soup = BeautifulSoup(self.content, "lxml", parse_only=only_article_content)
        if len(self.soup) < 2:  # tag DOCTYPE always at [0] position
            raise NotEpisodeURLError(
                self.final_location,
                "[ERROR]: Can't parse this page: <article> tag was not found.",
            )

    def collect_links(self) -> None:
        """Parse all links matching regex pattern."""
        raise NotImplementedError()

    def do_post_parsing(self) -> None:
        """Finalize and process parsing results."""
        raise NotImplementedError()

    def parse_url(self) -> None:
        """Perform parsing."""
        self.get_url()
        self.do_pre_parsing()
        self.parse_dom_for_article_container()
        self.collect_links()
        self.do_post_parsing()


class ArchiveParser(LepParser):
    """Parser object for archive page."""

    def do_pre_parsing(self) -> None:
        """Substitute link with '.ukm' misspelled TLD in HTML content."""
        self.content = self.content.replace(".co.ukm", ".co.uk")

    def collect_links(self) -> None:
        """Parse all links matching episode URL and their texts.

        Also remove duplicated links. If an archive page consists completely of
            duplicated links - silently go further (as if there are no episodes at all).
        """
        soup_a_only = BeautifulSoup(
            str(self.soup),
            features="lxml",
            parse_only=only_a_tags_with_ep_link,
        )
        if len(soup_a_only) > 1:  # tag DOCTYPE always at [0] position
            # Remove all duplicated links
            tags_a_episodes = soup_a_only.find_all(is_tag_a_repeated, recursive=False)

            for tag_a in tags_a_episodes:
                link = tag_a["href"].strip()
                link_string = " ".join([text for text in tag_a.stripped_strings])
                self.archive.collected_links[link] = link_string
        else:
            raise NoEpisodeLinksError(
                self.final_location,
                "[ERROR]: No episode links on archive page",
            )

    def remove_irrelevant_links(self) -> None:
        """Delete known irrelevant links from dictionary.

        First, write irrelevant links into 'deleted_links'
            before deletion them from dictionary.
        Then rebuild dictionary skipping irrelevant links.
        """
        self.archive.deleted_links = {
            link
            for link in self.archive.collected_links.keys()
            if link in conf.IRRELEVANT_LINKS
        }
        self.archive.collected_links = {
            link: text
            for link, text in self.archive.collected_links.items()
            if link not in conf.IRRELEVANT_LINKS
        }

    def substitute_short_links(self) -> None:
        """Paste final URL destination instead of short links."""
        for short, final in conf.SHORT_LINKS_MAPPING_DICT.items():
            # Rebuild dictionary changing only matched key
            self.archive.collected_links = {
                final if k == short else k: v
                for k, v in self.archive.collected_links.items()
            }

    def do_post_parsing(self) -> None:
        """Remove irrelevant links and substitute short links."""
        self.remove_irrelevant_links()
        self.substitute_short_links()


class EpisodeParser(LepParser):
    """Parser object for episode page."""

    def __init__(
        self,
        archive_obj: Archive,
        page_url: str,
        session: Optional[requests.Session] = None,
        post_title: str = "",
    ) -> None:
        """Initialize EpisodeParser object."""
        super().__init__(archive_obj, page_url, session)
        self.episode = LepEpisode()
        self.episode.post_title = post_title
        self.used_indexes = archive_obj.used_indexes

    def do_pre_parsing(self) -> None:
        """Parse episode date, number, index."""
        self.episode.index = generate_post_index(self.final_location, self.used_indexes)
        if self.episode.index == 0:
            raise NotEpisodeURLError(self.final_location)

        self.episode.url = self.final_location
        current_date_utc = datetime.now(timezone.utc)
        self.episode.parsed_at = current_date_utc.strftime(r"%Y-%m-%dT%H:%M:%S.%fZ")

        self.episode.episode = parse_episode_number(self.episode.post_title)

        full_soup = BeautifulSoup(self.content, "lxml")
        if full_soup.title is not None:
            self.episode._title = full_soup.title.string
        else:
            self.episode._title = "NO TITLE!"
        del full_soup

        if not self.is_url_ok:
            self.episode.url = self.final_location
            self.episode.admin_note = self.content[:50]
            raise LepEpisodeNotFound(self.episode)

    def collect_links(self) -> None:
        """Parse link(s) to episode audio(s)."""
        self.episode.date = parse_post_publish_datetime(self.soup)
        self.episode.files["audios"] = parse_post_audio(self.soup)
        if not self.episode.files["audios"]:
            self.episode.post_type = "TEXT"
        else:
            self.episode.post_type = "AUDIO"

    def do_post_parsing(self) -> None:
        """Add parsed episode to shared list."""
        pass
