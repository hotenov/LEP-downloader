"""LEP module for parsing logic."""
import copy
import re
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import requests
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from bs4.element import Tag

from lep_downloader import config as conf
from lep_downloader.lep import LepEpisode


deleted_links = []


# COMPILED REGEX PATTERNS #

EP_LINK_PATTERN = re.compile(conf.EPISODE_LINK_RE, re.IGNORECASE)

duplicated_ep_links_re = r"^\[(website\scontent|video)\]$|episode\s522$"
DUPLICATED_EP_PATTERN = re.compile(duplicated_ep_links_re, re.IGNORECASE)

INVALID_PATH_CHARS_PATTERN = re.compile(conf.INVALID_PATH_CHARS_RE)

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

post_indexes: List[int] = []

s = requests.Session()


def get_web_page_html_text(page_url: str, session: requests.Session) -> Any:
    """Return HTML text of LEP archive page."""
    final_location = page_url
    is_url_ok = False
    with session:
        try:
            resp = session.get(page_url, timeout=(6, 33))
            final_location = resp.url
            if not resp.ok:
                resp.raise_for_status()
        except requests.exceptions.HTTPError as err:
            return (f"[ERROR]: {err}", final_location, is_url_ok)
        except requests.exceptions.Timeout as err:
            return (f"[ERROR]: Timeout | {err}", final_location, is_url_ok)
        except requests.exceptions.ConnectionError as err:
            return (f"[ERROR]: Bad request | {err}", final_location, is_url_ok)
        except Exception as err:
            return (f"[ERROR]: Unhandled error | {err}", final_location, is_url_ok)
        else:
            resp.encoding = "utf-8"
            final_location = resp.url
            is_url_ok = True
            return (resp.text, final_location, is_url_ok)


def tag_a_with_episode(tag_a: Tag) -> bool:
    """Returns True for appropriate link to episode."""
    tag_text = tag_a.get_text()
    is_appropriate = False
    match = DUPLICATED_EP_PATTERN.search(tag_text.strip())
    is_appropriate = False if match else True
    return is_appropriate


def get_all_episode_links_from_soup(
    soup_obj: BeautifulSoup,
) -> Tuple[List[str], List[str]]:
    """Return list of links from HTML block."""
    all_links: List[str] = []
    all_titles: List[str] = []
    soup_a_only = BeautifulSoup(
        str(soup_obj),
        features="lxml",
        parse_only=only_a_tags_with_ep_link,
    )
    if len(soup_a_only) > 1:
        tags_a_episodes = soup_a_only.find_all(tag_a_with_episode, recursive=False)
        if len(tags_a_episodes) > 0:
            for tag_a in tags_a_episodes:
                link = tag_a["href"].strip()
                link_string = " ".join([text for text in tag_a.stripped_strings])
                all_links.append(link)
                all_titles.append(link_string)
            return (all_links, all_titles)
        else:
            return (all_links, all_titles)
    else:
        return (all_links, all_titles)


def replace_misspelled_link(soup_obj: BeautifulSoup) -> BeautifulSoup:
    """Replace link with '.ukm' misspelled LTD."""
    modified_soup = copy.copy(soup_obj)  # TODO: Really needs to copy?
    misspelled_tag_a = modified_soup.find(
        "a", href="https://teacherluke.co.ukm/2012/08/06/london-olympics-2012/"
    )
    if misspelled_tag_a:
        misspelled_tag_a[
            "href"
        ] = "https://teacherluke.co.uk/2012/08/06/london-olympics-2012/"
    del misspelled_tag_a
    return modified_soup


def remove_irrelevant_links(
    links: List[str],
    texts: List[str],
) -> Tuple[List[str], List[str]]:
    """Return list of links without known irrelevant links."""
    for i, link in enumerate(links[:]):
        if link in conf.IRRELEVANT_LINKS:
            deleted_links.append(link)
            del links[i]
            del texts[i]
    return (links, texts)


def substitute_short_links(unique_links: List[str]) -> List[str]:
    """Return list of links with final location for short links."""
    final_links = copy.deepcopy(unique_links)

    for key, value in conf.SHORT_LINKS_MAPPING_DICT.items():
        try:
            short_link_index = unique_links.index(key)
            final_links[short_link_index] = value
        except ValueError:
            print(f"[WARNING]: No short links: {key}")
    return final_links


def get_archive_parsing_results(archive_url: str) -> Any:
    """Return Tuple with valid episode links and discarded links."""
    html_page = get_web_page_html_text(archive_url, s)[0]
    soup_article = BeautifulSoup(html_page, "lxml", parse_only=only_article_content)

    if len(soup_article) > 1:
        modified_soup = replace_misspelled_link(soup_article)
        all_links: List[str] = []
        link_strings: List[str] = []
        all_links, link_strings = get_all_episode_links_from_soup(modified_soup)

        cleaned_links: List[str] = []
        cleaned_strings: List[str] = []
        cleaned_links, cleaned_strings = remove_irrelevant_links(
            all_links,
            link_strings,
        )
        final_list = substitute_short_links(cleaned_links)
        parsing_result = (final_list, deleted_links, cleaned_strings)
        return parsing_result
    else:
        print("[ERROR] Can't parse this page: <article> tag was not found.")
        return None


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


def generate_post_index(post_url: str, indexes: List[int]) -> int:
    """Returns index number for post."""
    match = EP_LINK_PATTERN.match(post_url)
    if match:
        groups_dict = match.groupdict()
        date_from_url = groups_dict["date"]
        date_numbers = date_from_url.replace("/", "")

        number_at_same_day = 1
        index_as_string = date_numbers + str(number_at_same_day).zfill(2)
        new_index = int(index_as_string)
        exists = False
        while not exists:
            if new_index in indexes:
                new_index += 1
            else:
                indexes.append(new_index)
                exists = True
        return new_index
    else:
        return 0


def appropriate_tag_a(tag_a: Tag) -> bool:
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
        tags_a_audio = soup_a_only.find_all(appropriate_tag_a, recursive=False)
        if len(tags_a_audio) > 0:
            for tag_a in tags_a_audio:
                audio = [tag_a["href"]]
                audios.append(audio)
            return audios
        else:
            return audios
    else:
        return audios


def parse_single_page(
    url: str,
    session: requests.Session,
    url_title: str,
) -> Optional[Dict[str, Any]]:
    """Returns a dict of parsed episode."""
    current_date_utc = datetime.now(timezone.utc)
    parsing_date = current_date_utc.strftime(r"%Y-%m-%dT%H:%M:%S.%fZ")

    html_page, final_location, is_url_ok = get_web_page_html_text(url, session)

    index = generate_post_index(final_location, post_indexes)
    if index == 0:
        return None

    ep_number = parse_episode_number(url_title)

    if not is_url_ok:
        bad_ep = LepEpisode(
            episode=ep_number,
            url=final_location,
            post_title=url_title,
            parsing_utc=parsing_date,
            index=index,
            admin_note=html_page[:50],
        )
        return bad_ep.__dict__

    soup_article = BeautifulSoup(html_page, "lxml", parse_only=only_article_content)
    post_date = parse_post_publish_datetime(soup_article)

    post_type = "AUDIO"
    post_audios = parse_post_audio(soup_article)
    if not post_audios:
        post_type = "TEXT"

    lep_ep = LepEpisode(
        episode=ep_number,
        date=post_date,
        url=final_location,
        post_title=url_title,
        post_type=post_type,
        audios=post_audios,
        parsing_utc=parsing_date,
        index=index,
    )
    return lep_ep.__dict__


def get_parsed_episodes(
    urls: List[str],
    session: requests.Session,
    texts: List[str],
) -> List[Dict[str, Any]]:
    """Returns list of parsed episodes."""
    parsed_episodes: List[Dict[str, Any]] = []
    texts_from_first_to_last = list(reversed(texts))
    for i, url in enumerate(list(reversed(urls))):
        url_title = texts_from_first_to_last[i]
        ep = parse_single_page(url, session, url_title)
        if ep is not None:
            parsed_episodes.append(ep)
    return parsed_episodes
