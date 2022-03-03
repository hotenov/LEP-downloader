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
"""LEP module for downloading logic."""
import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union

import requests

from lep_downloader import config as conf
from lep_downloader.lep import Lep
from lep_downloader.lep import LepEpisode
from lep_downloader.lep import LepEpisodeList
from lep_downloader.lep import LepLog


# COMPILED REGEX PATTERNS #
URL_ENCODED_CHARS_PATTERN = re.compile(r"%[0-9A-Z]{2}")
"""re.Pattern: Pattern for matching %-encoded Unicode characters."""


@dataclass
class LepFile:
    """Represent base class for LEP file object.

    Args:
        ep_id (int): Episode index. Defaults to 0.
        name (str): File name (without extension). Defaults to empty str.
        ext (str): File extension. Defaults to empty str.
        short_date (str): Episode date (format "YYYY-MM-DD"). Defaults to empty str.
        filename (str): File name + extension. Defaults to empty str.
        primary_url (str): Primary URL to download file. Defaults to empty str.
        secondary_url (str): Secondary URL to download file. Defaults to empty str.
        tertiary_url (str): Tertiary URL to download file. Defaults to empty str.
    """

    ep_id: int = 0  #: Episode index.
    name: str = ""  #: File name (without extension).
    ext: str = ""  #: File extension.
    short_date: str = ""  #: Episode date (format "YYYY-MM-DD").
    filename: str = ""  #: File name + extension.
    primary_url: str = ""  #: Primary URL to download file.
    secondary_url: str = ""  #: Secondary URL to download file.
    tertiary_url: str = ""  #: Tertiary URL to download file.


@dataclass
class Audio(LepFile):
    """Represent audio object to episode (or part of it).

    Args:
        ep_id (int): Episode index. Defaults to 0.
        name (str): File name (without extension). Defaults to empty str.
        ext (str): File extension. Defaults to ".mp3".
        short_date (str): Episode date (format "YYYY-MM-DD"). Defaults to empty str.
        filename (str): File name + extension. Defaults to empty str.
        primary_url (str): Primary URL to download file. Defaults to empty str.
        secondary_url (str): Secondary URL to download file. Defaults to empty str.
        tertiary_url (str): Tertiary URL to download file. Defaults to empty str.
        part_no (int): Part number. Defaults to 0.

    Notes:
        Filename depends on part number.
            - If `part_no` = 0, composed as ``f"[{short_date}] # {name}" + ext``
            - If `part_no` > 0, ``f"[{short_date}] # {name}" + " [Part NN]" + ext``

        Other attrs see :class:`LepFile`
    """

    ext: str = ".mp3"  #: Extension for audio file.
    part_no: int = 0  #: Part number.

    def __post_init__(self) -> None:
        """Compose filename for this instance."""
        if self.part_no > 0:
            self.filename = (
                f"[{self.short_date}] # {self.name} [Part {str(self.part_no).zfill(2)}]"
                + self.ext
            )
        else:
            self.filename = f"[{self.short_date}] # {self.name}" + self.ext


@dataclass
class PagePDF(LepFile):
    """Represent PDF file of episode page.

    Args:
        ep_id (int): Episode index. Defaults to 0.
        name (str): File name (without extension). Defaults to empty str.
        ext (str): File extension. Defaults to ".pdf".
        short_date (str): Episode date (format "YYYY-MM-DD"). Defaults to empty str.
        filename (str): File name + extension. Defaults to empty str.
        primary_url (str): Primary URL to download file. Defaults to empty str.
        secondary_url (str): Secondary URL to download file. Defaults to empty str.
        tertiary_url (str): Tertiary URL to download file. Defaults to empty str.

    Notes:
        Filename is composed after initialization other attrs as:
        ``f"[{short_date}] # {name}" + ext``

        Other attrs see :class:`LepFile`
    """

    ext: str = ".pdf"  #: Extension for PDF file.

    def __post_init__(self) -> None:
        """Compose filename for this instance."""
        self.filename = f"[{self.short_date}] # {self.name}" + self.ext


@dataclass
class ATrack(LepFile):
    """Represent audio track object (to episode video or part of it).

    Args:
        ep_id (int): Episode index. Defaults to 0.
        name (str): File name (without extension). Defaults to empty str.
        ext (str): File extension. Defaults to ".mp3".
        short_date (str): Episode date (format "YYYY-MM-DD"). Defaults to empty str.
        filename (str): File name + extension. Defaults to empty str.
        primary_url (str): Primary URL to download file. Defaults to empty str.
        secondary_url (str): Secondary URL to download file. Defaults to empty str.
        tertiary_url (str): Tertiary URL to download file. Defaults to empty str.
        part_no (int): Part number. Defaults to 0.

    Notes:
        Filename depends on part number.
            - If `part_no` = 0,
                composed as ``f"[{short_date}] # {name}" + " _aTrack_" + ext``
            - If `part_no` > 0,
                ``f"[{short_date}] # {name}" + " [Part NN]" + " _aTrack_" + ext``

        Other attrs see :class:`LepFile`
    """

    ext: str = ".mp3"  #: Extension for audio track file.
    part_no: int = 0  #: Part number.

    def __post_init__(self) -> None:
        """Compose filename for this instance."""
        if self.part_no > 0:
            self.filename = (
                f"[{self.short_date}] # {self.name} [Part {str(self.part_no).zfill(2)}]"
                + " _aTrack_"
                + self.ext
            )
        else:
            self.filename = (
                f"[{self.short_date}] # {self.name}" + " _aTrack_" + self.ext
            )


class LepFileList(List[Any]):
    """Represent list of LepFile objects."""

    def filter_by_type(self, *file_types: Any) -> Any:
        """Filter list by file type(s).

        Args:
            file_types (Any): Variable length argument list of file types
                (Audio, PagePDF, ATrack, and others).

        Returns:
            :class:`LepFileList`: New filtered LepFileList.
        """
        file_types = tuple(file_types)
        filtered = LepFileList(file for file in self if isinstance(file, file_types))
        return filtered


def crawl_list(links: List[str]) -> Tuple[str, str, str]:
    """Crawl list of links and return tuple of three links.

    For absent URL empty string is assigned.

    Args:
        links (list[str]): List of URLs (for one file).

    Returns:
        Tuple[str, str, str]: A tuple of three strings (URLs).
    """
    primary_url = secondary_url = tertiary_url = ""
    links_number = len(links)
    if links_number == 1:
        primary_url = links[0]
    else:
        if links_number == 2:
            primary_url = links[0]
            secondary_url = links[1]
        if links_number == 3:
            primary_url = links[0]
            secondary_url = links[1]
            tertiary_url = links[2]
    return primary_url, secondary_url, tertiary_url


def append_each_audio_to_container_list(
    ep_id: int,
    name: str,
    short_date: str,
    audios: List[List[str]],
    file_class: Union[Type[Audio], Type[ATrack]],
) -> None:
    """Relate links for each audio file with episode.

    And put audio as 'Audio' or 'ATrack' object to container list of LepFile objects.

    Args:
        ep_id (int): Episode number.
        name (str): File name (without extension).
        short_date (str): Date (format "YYYY-MM-DD").
        audios (list[list[str]]): List of list of URLs for each audio part.
        file_class (:class:`Audio` | :class:`ATrack`): LepFile subclass (audio type).
    """
    is_multi_part = False if len(audios) < 2 else True
    start = int(is_multi_part)

    for i, part_links in enumerate(audios, start=start):
        part_no = i
        primary_url, secondary_url, tertiary_url = crawl_list(part_links)
        audio_file = file_class(
            ep_id=ep_id,
            name=name,
            short_date=short_date,
            part_no=part_no,
            primary_url=primary_url,
            secondary_url=secondary_url,
            tertiary_url=tertiary_url,
        )
        global files_box
        files_box.append(audio_file)


def append_page_pdf_file_to_container_list(
    ep_id: int,
    name: str,
    short_date: str,
    page_pdf: List[str],
) -> None:
    """Relate links for page PDF file with episode.

    And put it as 'PagePDF' object to container list of LepFile objects.

    Args:
        ep_id (int): Episode number.
        name (str): File name (without extension).
        short_date (str): Date (format "YYYY-MM-DD").
        page_pdf (list[str]): List of URLs for page PDF file.
    """
    global files_box
    if not page_pdf:
        pdf_file = PagePDF(
            ep_id=ep_id,
            name=name,
            short_date=short_date,
        )
        files_box.append(pdf_file)
    else:
        primary_url, secondary_url, tertiary_url = crawl_list(page_pdf)
        pdf_file = PagePDF(
            ep_id=ep_id,
            name=name,
            short_date=short_date,
            primary_url=primary_url,
            secondary_url=secondary_url,
            tertiary_url=tertiary_url,
        )
        files_box.append(pdf_file)


files_box = LepFileList()
""":class:`LepFileList`: Module level container list of LepFile objects."""


def gather_all_files(lep_episodes: LepEpisodeList) -> LepFileList:
    """Skim list of episodes and collect all files.

    Args:
        lep_episodes (LepEpisodeList): List of LepEpisode objects.

    Returns:
        :class:`LepFileList`: Module's container list
        :const:`files_box`.
    """
    global files_box
    files_box = LepFileList()
    ep: LepEpisode

    for ep in reversed(lep_episodes):
        if ep.files:
            audios = ep.files.setdefault("audios", [])
            if audios:
                append_each_audio_to_container_list(
                    ep.index, ep.post_title, ep.short_date, audios, Audio
                )
            audio_tracks = ep.files.setdefault("atrack", [])
            if audio_tracks:
                append_each_audio_to_container_list(
                    ep.index, ep.post_title, ep.short_date, audio_tracks, ATrack
                )
            page_pdf = ep.files.setdefault("page_pdf", [])
            append_page_pdf_file_to_container_list(
                ep.index, ep.post_title, ep.short_date, page_pdf
            )
    return files_box


def detect_existing_files(
    save_dir: Path,
    files: LepFileList,
) -> Tuple[LepFileList, LepFileList]:
    """Separate list for existing and non-existing files.

    Method scans all files in the directory and composes
    list of filtered files by extensions: mp3, pdf, mp4.
    Then it separates 'files' list on two:
    existed files and non-existed files
    (iterating over filtered files in the directory, not all).

    Args:
        save_dir (Path): Path to destination folder.
        files (LepFileList): List of LepFile objects.

    Returns:
        Tuple[LepFileList, LepFileList]: A tuple with
        two lists: existed, non_existed.
    """
    existed = LepFileList()
    non_existed = LepFileList()
    only_files_by_ext: List[str] = []
    possible_extensions = {".mp3", ".pdf", ".mp4"}
    only_files_by_ext = [
        p.name for p in save_dir.glob("*") if p.suffix.lower() in possible_extensions
    ]
    for file in files:
        if file.filename in only_files_by_ext:
            existed.append(file)
        else:
            non_existed.append(file)
    return existed, non_existed


def download_and_write_file(
    url: str,
    session: requests.Session,
    save_dir: Path,
    filename: str,
    log: LepLog,
) -> bool:
    """Download a file by URL and save it.

    Args:
        url (str): URL to file.
        session (requests.Session): Session to send request.
        save_dir (Path): Folder where to save file.
        filename (str): Filename (with extension).
        log (LepLog): Log object where to print messages.

    Returns:
        bool: Status operation. True for success, False otherwise.
    """
    is_writing_started = False
    file_path: Path = save_dir / filename
    try:
        with session.get(url, stream=True) as response:
            response.raise_for_status()
            with file_path.open(mode="wb") as out_file:
                for chunk in response.iter_content(  # pragma: no cover for Python 3.10
                    chunk_size=1024 * 1024  # 1MB chunks
                ):
                    out_file.write(chunk)
                    is_writing_started = True
            log.msg("<g> + </g>{filename}", filename=filename)
            return True
    except OSError:
        if is_writing_started:
            # It's hard to mock / monkeypatch this case. Tested manually
            file_path.unlink()  # Delete incomplete file # pragma: no cover
        log.msg("Can't write file: {filename}", filename=filename, msg_lvl="MISSING")
        return False
    except Exception as err:
        log.msg("URL: {url} | Unhandled: {err}", err=err, url=url, msg_lvl="CRITICAL")
        return False


class LepDL(Lep):
    """Represent downloader object.

    Args:
        json_url (str): URL to JSON database
        session (requests.Session): Requests session object.
            If None defaults to global session :const:`lep.PROD_SES`.
        log (LepLog): Log instance where to output messages.
    """

    def __init__(
        self,
        json_url: str = conf.JSON_DB_URL,
        session: requests.Session = None,
        log: Optional[LepLog] = None,
    ) -> None:
        """Initialize LepDL object."""
        super().__init__(session, log)

        #: URL to JSON database.
        self.json_url: str = json_url

        #: List of episodes in JSON database.
        self.db_episodes: LepEpisodeList = LepEpisodeList()

        #: Dictionary "URL - post title".
        self.db_urls: Dict[str, str] = {}

        #: List of all files (gathered for downloading).
        self.files: LepFileList = LepFileList()

        #: List of downloaded files.
        self.downloaded: LepFileList = LepFileList()

        #: List of unavailable files.
        self.not_found: LepFileList = LepFileList()

        #: List of existing files on disc.
        self.existed: LepFileList = LepFileList()

        #: List of non-existing files on disc.
        self.non_existed: LepFileList = LepFileList()

    def get_remote_episodes(self) -> None:
        """Get database episodes from remote JSON database.

        After retreiving episodes, also extract all URLs and their titles
        and store them in 'db_urls' attribute.
        """
        self.db_episodes = Lep.get_db_episodes(self.json_url)
        self.db_urls = extract_urls_from_episode_list(self.db_episodes)

    def detach_existed_files(
        self,
        save_dir: Path,
        files: Optional[LepFileList] = None,
    ) -> None:
        """Detach 'existed' files from non 'non_existed'.

        Args:
            save_dir (Path): Folder for saving files.
            files (LepFileList, optional): List of files.
                If None, defaults to self 'files' attribute.
        """
        files = files if files else self.files
        self.existed, self.non_existed = detect_existing_files(save_dir, files)

    def populate_default_url(self) -> None:
        """Fill in secondary download url (if it is empty) with default value.

        Iterate over 'files' attribute list.
        Default value composed as: :const:`config.DOWNLOADS_BASE_URL` + url-encoded
        filename.
        """
        populated_files = LepFileList()
        for file in self.files:
            if not file.secondary_url:
                file.secondary_url = conf.DOWNLOADS_BASE_URL + urllib.parse.quote(
                    file.filename
                )
            populated_files.append(file)
        self.files = populated_files

    def download_files(
        self,
        save_dir: Path,
    ) -> None:
        """Download files from 'non_existed' attribute list.

        For reliability: If primary link is not available,
        method will try to download other two links (if they present).

        Args:
            save_dir (Path): Path to folder where to save files.
        """
        for file_obj in self.non_existed:
            filename = file_obj.filename
            primary_link = file_obj.primary_url

            if Path(save_dir / filename).exists():
                self.existed.append(file_obj)
                continue  # Skip already downloaded file on disc.

            result_ok = download_and_write_file(
                primary_link,
                self.session,
                save_dir,
                filename,
                self.lep_log,
            )
            if result_ok:
                self.downloaded.append(file_obj)
            else:
                secondary_url = file_obj.secondary_url
                tertiary_url = file_obj.tertiary_url
                aux_result_ok = False

                # Try downloading for auxiliary links
                if secondary_url:
                    aux_result_ok = download_and_write_file(
                        secondary_url, self.session, save_dir, filename, self.lep_log
                    )
                if tertiary_url and not aux_result_ok:
                    aux_result_ok = download_and_write_file(
                        tertiary_url, self.session, save_dir, filename, self.lep_log
                    )
                if aux_result_ok:
                    self.downloaded.append(file_obj)
                else:
                    self.not_found.append(file_obj)
                    self.lep_log.msg("<r> - </r>{filename}", filename=filename)


def url_encoded_chars_to_lower_case(url: str) -> str:
    """Change %-escaped chars in string to lower case.

    Args:
        url (str): URL with uppercase unicode characters.

    Returns:
        str: URL with lowercase unicode characters.

    Example:
        >>> import lep_downloader.downloader
        >>> url = "https://teacherluke.co.uk/2016/03/01/333-more-misheard-lyrics-%E2%99%AC/"
        >>> lep_downloader.downloader.url_encoded_chars_to_lower_case(url)
        'https://teacherluke.co.uk/2016/03/01/333-more-misheard-lyrics-%e2%99%ac/'
    """  # noqa: E501,B950
    lower_url = URL_ENCODED_CHARS_PATTERN.sub(
        lambda matchobj: matchobj.group(0).lower(), url
    )
    return lower_url


def extract_urls_from_episode_list(episodes: LepEpisodeList) -> Dict[str, str]:
    """Extract page URL and its title for each episode object in list.

    Args:
        episodes (LepEpisodeList): List of episodes.

    Returns:
        dict[str, str]: Dictionary "URL - post title".
    """
    urls_titles = {
        url_encoded_chars_to_lower_case(ep.url): ep.post_title for ep in episodes
    }
    return urls_titles
