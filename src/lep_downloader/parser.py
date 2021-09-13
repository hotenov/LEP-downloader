"""LEP module for parsing logic."""
import copy
import re
from typing import List, Tuple

from bs4 import BeautifulSoup
import requests

from lep_downloader import config as conf


deleted_links = []
regex = conf.EPISODE_LINK_RE
ep_pattern = re.compile(regex, re.IGNORECASE)


def get_lep_archive_page(archive_url: str) -> str:
    """Return HTML text of LEP archive page."""
    with requests.Session() as s:
        req = s.get(archive_url)
        req.encoding = "utf-8"
    return req.text


def get_all_links_from_tag_with_class(
    soup_obj: BeautifulSoup,
    tag_name: str,
    class_name: str,
) -> List[str]:
    """Return list of links from HTML block."""
    tag_entry_content = soup_obj.find(tag_name, class_= class_name)
    all_links: List[str] = []
    all_link_tags = tag_entry_content.find_all("a")
    for link in all_link_tags:
        all_links.append(link["href"].strip())

    return all_links


def replace_misspelled_link(all_links: List) -> List:
    """Replace link with '.ukm' misspelled LTD"""
    links_without_misspelled_ltd = copy.deepcopy(all_links)
    try:
        bad_index = links_without_misspelled_ltd.index("https://teacherluke.co.ukm/2012/08/06/london-olympics-2012/")
        links_without_misspelled_ltd[bad_index] = "https://teacherluke.co.uk/2012/08/06/london-olympics-2012/"
    except ValueError:
        # Here, no need to handle it.
        pass
    return links_without_misspelled_ltd


def remove_irrelevant_links(links: List) -> List:
    """Return list of links without known irrelevant links."""
    for i, link in enumerate(links[:]):
        if link in conf.NOT_EPISODE_LINKS:
            deleted_links.append(link)
            del links[i]
    return links


def remove_not_episode_links(links: List) -> List:
    """Return list of adopted episode (post) links."""
    result = []
    for link in links:
        match = ep_pattern.match(link)
        if match:
            result.append(link)
        else:
            deleted_links.append(link)
    return result


def substitute_short_links(unique_links: List) -> List:
    """Return list of links with final location for short links."""
    final_links = copy.deepcopy(unique_links)

    for key, value in conf.SHORT_LINKS_MAPPING_DICT.items():
        try:
            short_link_index = unique_links.index(key)
            final_links[short_link_index] = value
        except ValueError:
            print(f"[WARNING]: No short links: {key}")
    return final_links


def get_archive_parsing_results(archive_url: str) -> Tuple:
    """Return Tuple with valid episode links and discarded links."""
    html_page = get_lep_archive_page(archive_url)
    soup_obj = BeautifulSoup(html_page, "lxml")
    all_links = get_all_links_from_tag_with_class(soup_obj, "div", "entry-content")
    cleaned_links = replace_misspelled_link(all_links)
    cleaned_links = remove_irrelevant_links(cleaned_links)
    cleaned_links = remove_not_episode_links(cleaned_links)
    # Get unique links with preserved order for Python 3.7+
    unique_links = list(dict.fromkeys(cleaned_links))
    final_list = substitute_short_links(unique_links)
    parsing_result = (final_list, deleted_links)
    return parsing_result


