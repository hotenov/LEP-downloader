"""LEP module for parsing logic."""
import copy
import re
from typing import Any, Dict, Optional
from typing import List

import requests
from bs4 import BeautifulSoup
from bs4 import SoupStrainer

from lep_downloader import config as conf
from lep_downloader.lep import LepEpisode


deleted_links = []
regex = conf.EPISODE_LINK_RE
ep_pattern = re.compile(regex, re.IGNORECASE)
INVALID_PATH_CHARS_PATTERN = re.compile(conf.INVALID_PATH_CHARS_RE)
begining_digits_re = r"^\d{1,5}"
BEGINING_DIGITS_PATTERN = re.compile(begining_digits_re)

only_div_content_main = SoupStrainer("div", id="content", role="main")

post_indexes = []

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


def get_all_links_from_soup(soup_obj: BeautifulSoup) -> List[str]:
    """Return list of links from HTML block."""
    all_links: List[str] = []
    all_tags_a = soup_obj("a")
    for tag_a in all_tags_a:
        all_links.append(tag_a["href"].strip())

    return all_links


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


def remove_irrelevant_links(links: List[str]) -> List[str]:
    """Return list of links without known irrelevant links."""
    for i, link in enumerate(links[:]):
        if link in conf.IRRELEVANT_LINKS:
            deleted_links.append(link)
            del links[i]
    return links


def remove_not_episode_links_by_regex_pattern(links: List[str]) -> List[str]:
    """Return list of adopted episode (post) links."""
    result: List[str] = []
    for link in links:
        match = ep_pattern.match(link)
        if match:
            result.append(link)
        else:
            deleted_links.append(link)
    return result


def get_links_text_by_href(
    soup_obj: BeautifulSoup,
    links: List[str],
) -> List[str]:
    """Return text of <a></a> tag by its href attribute."""
    link_strings = []
    for url in links:
        a_tag = soup_obj.find("a", href=url)
        if url in [*conf.LINK_TEXTS_MAPPING]:
            link_string = conf.LINK_TEXTS_MAPPING[url]
        else:
            link_string = " ".join([text for text in a_tag.stripped_strings])
        safe_name = INVALID_PATH_CHARS_PATTERN.sub("_", link_string)
        link_strings.append(safe_name)

    return link_strings


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
    only_div_entry_content = SoupStrainer("div", class_="entry-content")
    soup_div = BeautifulSoup(html_page, "lxml", parse_only=only_div_entry_content)

    if len(soup_div) > 0:
        modified_soup_div = replace_misspelled_link(soup_div)
        all_links = get_all_links_from_soup(modified_soup_div)
        cleaned_links = remove_irrelevant_links(all_links)
        cleaned_links = remove_not_episode_links_by_regex_pattern(cleaned_links)

        # Get unique links with preserved order for Python 3.7+
        unique_links = list(dict.fromkeys(cleaned_links))

        # Get list of 'link labeles'
        link_strings = get_links_text_by_href(modified_soup_div, unique_links)

        final_list = substitute_short_links(unique_links)
        parsing_result = (final_list, deleted_links, link_strings)
        return parsing_result
    else:
        print("[ERROR] Can't parse this page: Main <div> is not found")
        return None


def parse_post_publish_datetime(soup: BeautifulSoup) -> str:
    """Returns post datetime as string."""
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
    match = ep_pattern.match(post_url)
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


def parse_single_page(
    url: str,
    session: requests.Session,
    url_title: str,
) -> Optional[Dict[str, Any]]:
    """Returns a dict of parsed episode."""
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
            index=index,
            admin_note=html_page[:50],
        )
        return bad_ep.__dict__

    soup_div = BeautifulSoup(html_page, "lxml", parse_only=only_div_content_main)
    post_date = parse_post_publish_datetime(soup_div)

    lep_ep = LepEpisode(
        episode=ep_number,
        date=post_date,
        url=final_location,
        post_title=url_title,
        index=index,
    )
    return lep_ep.__dict__


def get_parsed_episodes(
    urls: List[str],
    session: requests.Session,
    texts: List[str],
) -> List[Dict[str, Any]]:
    """Returns list of parsed episodes."""
    parsed_episodes: List[LepEpisode] = []
    texts_from_first_to_last = list(reversed(texts))
    for i, url in enumerate(list(reversed(urls))):
        url_title = texts_from_first_to_last[i]
        ep = parse_single_page(url, session, url_title)
        if ep is not None:
            parsed_episodes.append(ep)
    return parsed_episodes
