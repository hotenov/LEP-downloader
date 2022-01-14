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
from typing import ClassVar
from typing import List
from typing import Tuple

import requests

from lep_downloader import config as conf
from lep_downloader.exceptions import EmptyDownloadsBunch
from lep_downloader.exceptions import NoEpisodesInDataBase
from lep_downloader.lep import Lep
from lep_downloader.lep import LepEpisode
from lep_downloader.lep import LepEpisodeList


# COMPILED REGEX PATTERNS #

INVALID_PATH_CHARS_PATTERN = re.compile(conf.INVALID_PATH_CHARS_RE)


@dataclass
class LepFile:
    """Represent base class for LEP file object."""

    ep_id: int = 0
    name: str = ""
    ext: str = ""
    short_date: str = ""
    filename: str = ""
    primary_url: str = ""
    secondary_url: str = ""
    tertiary_url: str = ""


@dataclass
class Audio(LepFile):
    """Represent episode (or part of it) audio object."""

    ext: str = ".mp3"
    part_no: int = 0

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
    """Represent PDF file of episode page."""

    ext: str = ".pdf"

    def __post_init__(self) -> None:
        """Compose filename for this instance."""
        self.filename = f"[{self.short_date}] # {self.name}" + self.ext


class LepFileList(List[Any]):
    """Represent list of LepFile objects."""

    def filter_by_type(self, *file_types: Any) -> Any:
        """Return new filtered list by file type(s)."""
        file_types = tuple(file_types)
        filtered = LepFileList(file for file in self if isinstance(file, file_types))
        return filtered


def crawl_list(links: List[str]) -> Tuple[str, str, str]:
    """Crawl list of links and return tuple of three links."""
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


def add_each_audio_to_shared_list(
    ep_id: int,
    name: str,
    short_date: str,
    audios: List[List[str]],
) -> None:
    """Gather data for each episode audio.

    Then add it as 'Audio' object to shared 'files' list of LepFile objects.
    """
    is_multi_part = False if len(audios) < 2 else True
    start = int(is_multi_part)

    for i, part_links in enumerate(audios, start=start):
        part_no = i
        primary_url, secondary_url, tertiary_url = crawl_list(part_links)
        audio_file = Audio(
            ep_id=ep_id,
            name=name,
            short_date=short_date,
            part_no=part_no,
            primary_url=primary_url,
            secondary_url=secondary_url,
            tertiary_url=tertiary_url,
        )
        Downloader.files.append(audio_file)


def add_page_pdf_file(
    ep_id: int,
    name: str,
    short_date: str,
    page_pdf: List[str],
) -> None:
    """Gather page PDF for episode.

    Then add it as 'PagePDF' object to shared 'files' list of LepFile objects.
    """
    if not page_pdf:
        pdf_file = PagePDF(
            ep_id=ep_id,
            name=name,
            short_date=short_date,
        )
        Downloader.files.append(pdf_file)
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
        Downloader.files.append(pdf_file)


def gather_all_files(lep_episodes: LepEpisodeList) -> None:
    """Skim passed episode list and collect all files.

    Add each file to shared 'files' list fo further actions.
    """
    ep: LepEpisode
    if lep_episodes:
        for ep in reversed(lep_episodes):
            if ep.files:
                audios = ep.files["audios"]
                if audios:
                    add_each_audio_to_shared_list(
                        ep.index, ep.post_title, ep._short_date, audios
                    )

                page_pdf = ep.files["page_pdf"]
                add_page_pdf_file(ep.index, ep.post_title, ep._short_date, page_pdf)
    else:
        raise NoEpisodesInDataBase("No episodes for gathering files. Exit.")


def detect_existing_files(
    files: LepFileList,
    save_dir: Path,
) -> None:
    """Separate lists for existing and non-existing files."""
    Downloader.existed = LepFileList()
    Downloader.non_existed = LepFileList()
    only_files_by_ext: List[str] = []
    possible_extensions = {".mp3", ".pdf", ".mp4"}
    only_files_by_ext = [
        p.name for p in save_dir.glob("*") if p.suffix.lower() in possible_extensions
    ]
    for file in files:
        if file.filename in only_files_by_ext:
            Downloader.existed.append(file)
        else:
            Downloader.non_existed.append(file)


def download_and_write_file(
    url: str,
    session: requests.Session,
    save_dir: Path,
    filename: str,
) -> bool:
    """Downloads file by URL and returns operation status."""
    is_writing_started = False
    file_path: Path = save_dir / filename
    try:
        with session.get(url, stream=True) as response:
            response.raise_for_status()
            with file_path.open(mode="wb") as out_file:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024  # 1MB chunks
                ):
                    out_file.write(chunk)
                    is_writing_started = True
            print(f" + {filename}")
            return True
    except OSError as err:
        print(f"[ERROR]: Can't write file: {err}")
        if is_writing_started:
            file_path.unlink()  # Delete incomplete file # pragma: no cover
            # It's hard to mock / monkeypatch this case
            # Tested manually
        return False
    except Exception as err:
        print(f"[ERROR]: Unknown error: {err}")
        return False


class Downloader(Lep):
    """Represent downloader object."""

    downloaded: ClassVar[LepFileList] = LepFileList()
    not_found: ClassVar[LepFileList] = LepFileList()

    files: ClassVar[LepFileList] = LepFileList()
    existed: ClassVar[LepFileList] = LepFileList()
    non_existed: ClassVar[LepFileList] = LepFileList()

    # def __init__(self, url: str = "", session: requests.Session = None) -> None:
    #     """Initialize Downloader instance.

    #     Args:
    #         url (str): URL for parsing.
    #         session (requests.Session): Requests session object
    #             if None, get default global session.
    #     """
    #     self.url = url
    #     self.session = session if session else Lep.session


def use_or_get_db_episodes(json_url: str) -> None:
    """Take database episodes after parsing stage.

    Or get them from web JSON file.
    """
    if not Lep.db_episodes:
        Lep.db_episodes = Lep.get_db_episodes(json_url)


def populate_default_url() -> None:
    """Fill in download url (if it is empty) with default value.

    Operate with 'files' shared list.
    """
    populated_files = LepFileList()
    for file in Downloader.files:
        if not file.secondary_url:
            file.secondary_url = conf.DOWNLOADS_BASE_URL + urllib.parse.quote(
                file.filename
            )
        populated_files.append(file)
    Downloader.files = populated_files


def download_files(
    downloads_bunch: LepFileList,
    save_dir: Path,
) -> None:
    """Download files from passed links bunch."""
    if not downloads_bunch:
        raise EmptyDownloadsBunch()
    for file_obj in downloads_bunch:
        filename = file_obj.filename
        primary_link = file_obj.primary_url

        if Path(save_dir / filename).exists():
            Downloader.existed.append(file_obj)
            continue  # Skip already downloaded file on disc.

        result_ok = download_and_write_file(
            primary_link,
            Lep().session,
            save_dir,
            filename,
        )
        if result_ok:
            Downloader.downloaded.append(file_obj)
        else:
            secondary_url = file_obj.secondary_url
            tertiary_url = file_obj.tertiary_url
            aux_result_ok = False

            # Try downloading for auxiliary links
            if secondary_url:
                aux_result_ok = download_and_write_file(
                    secondary_url, Lep().session, save_dir, filename
                )
            if tertiary_url and not aux_result_ok:
                aux_result_ok = download_and_write_file(
                    tertiary_url, Lep().session, save_dir, filename
                )
            else:
                Downloader.not_found.append(file_obj)
                print(f"[INFO]: Can't download: {filename}")
            if aux_result_ok:
                Downloader.downloaded.append(file_obj)
