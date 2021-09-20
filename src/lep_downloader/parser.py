"""LEP module for parsing logic."""
import copy
import re
from typing import Any
from typing import List

import requests
from bs4 import BeautifulSoup
from bs4 import SoupStrainer

from lep_downloader import config as conf


deleted_links = []
regex = conf.EPISODE_LINK_RE
ep_pattern = re.compile(regex, re.IGNORECASE)
s = requests.Session()


def get_web_page_html_text(page_url: str, session: requests.Session) -> Any:
    """Return HTML text of LEP archive page."""
    with session:
        try:
            resp = session.get(page_url, timeout=(6, 33))
            if not resp.ok:
                resp.raise_for_status()
        except requests.exceptions.HTTPError:
            raise
        except requests.exceptions.Timeout:
            raise
        except requests.exceptions.ConnectionError:
            raise
        except Exception:
            raise
        else:
            resp.encoding = "utf-8"
            return resp.text


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
        link_strings.append(link_string)

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
    html_page = get_web_page_html_text(archive_url, s)
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


def parse_single_page(url: str, session: requests.Session) -> Any:
    """Returns result of parsing of single page."""
    req = session.get(url, timeout=(3.05, 27))
    req.encoding = "utf-8"
    html_text = req.text

    soup_obj = BeautifulSoup(html_text, "lxml")
    page_title = soup_obj.title.string
    result = page_title
    return result
