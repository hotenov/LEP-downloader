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


# COMPILED REGEX PATTERNS #
URL_ENCODED_CHARS_PATTERN = re.compile(r"%[0-9A-Z]{2}")


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


@dataclass
class ATrack(LepFile):
    """Represent audio track to episode (or part of it) object."""

    ext: str = ".mp3"
    part_no: int = 0

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
    file_class: Union[Type[Audio], Type[ATrack]],
) -> None:
    """Gather data for each episode audio.

    Then add it as 'Audio' or 'ATrack' object to shared list of LepFile objects.
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


def add_page_pdf_file(
    ep_id: int,
    name: str,
    short_date: str,
    page_pdf: List[str],
) -> None:
    """Gather page PDF for episode.

    Then add it as 'PagePDF' object to shared 'files' list of LepFile objects.
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


def gather_all_files(lep_episodes: LepEpisodeList) -> LepFileList:
    """Skim passed episode list and collect all files.

    Return module's 'files_box' list.
    """
    global files_box
    files_box = LepFileList()
    ep: LepEpisode

    for ep in reversed(lep_episodes):
        if ep.files:
            audios = ep.files.setdefault("audios", [])
            if audios:
                add_each_audio_to_shared_list(
                    ep.index, ep.post_title, ep._short_date, audios, Audio
                )
            audio_tracks = ep.files.setdefault("atrack", [])
            if audio_tracks:
                add_each_audio_to_shared_list(
                    ep.index, ep.post_title, ep._short_date, audio_tracks, ATrack
                )
            page_pdf = ep.files.setdefault("page_pdf", [])
            add_page_pdf_file(ep.index, ep.post_title, ep._short_date, page_pdf)
    return files_box


def detect_existing_files(
    save_dir: Path,
    files: LepFileList,
) -> Tuple[LepFileList, LepFileList]:
    """Separate lists for existing and non-existing files."""
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
            Lep.msg("<g> + </g>{filename}", filename=filename)
            return True
    except OSError:
        if is_writing_started:
            # It's hard to mock / monkeypatch this case. Tested manually
            file_path.unlink()  # Delete incomplete file # pragma: no cover
        Lep.msg("Can't write file: {filename}", filename=filename, msg_lvl="ERROR")
        return False
    except Exception as err:
        Lep.msg("URL: {url} | Unhandled: {err}", err=err, url=url, msg_lvl="CRITICAL")
        return False


class LepDL(Lep):
    """Represent downloader object."""

    def __init__(
        self,
        json_url: str = conf.JSON_DB_URL,
        session: requests.Session = None,
    ) -> None:
        """Initialize LepDL object.

        Args:
            json_url (str): URL to JSON datavase
            session (requests.Session): Requests session object
                if None, get default global session.
        """
        super().__init__(session)
        self.json_url = json_url
        self.db_episodes: LepEpisodeList = LepEpisodeList()
        self.db_urls: Dict[str, str] = {}
        self.files: LepFileList = LepFileList()
        self.downloaded: LepFileList = LepFileList()
        self.not_found: LepFileList = LepFileList()
        self.existed: LepFileList = LepFileList()
        self.non_existed: LepFileList = LepFileList()

    def use_or_get_db_episodes(self) -> None:
        """Take database episodes after parsing stage.

        Or get them from web JSON file.
        """
        if not self.db_episodes:
            self.db_episodes = Lep.get_db_episodes(self.json_url)
            self.db_urls = extract_urls_from_episode_list(self.db_episodes)

    def detach_existed_files(
        self,
        save_dir: Path,
        files: Optional[LepFileList] = None,
    ) -> None:
        """Detach 'existed' files from non 'non_existed'."""
        files = files if files else self.files
        self.existed, self.non_existed = detect_existing_files(save_dir, files)

    def populate_default_url(self) -> None:
        """Fill in download url (if it is empty) with default value.

        Operate with 'files' shared list.
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
        """Download files from passed links bunch."""
        for file_obj in self.non_existed:
            filename = file_obj.filename
            primary_link = file_obj.primary_url

            if Path(save_dir / filename).exists():
                self.existed.append(file_obj)
                continue  # Skip already downloaded file on disc.

            result_ok = download_and_write_file(
                primary_link,
                Lep().cls_session,
                save_dir,
                filename,
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
                        secondary_url, self.session, save_dir, filename
                    )
                if tertiary_url and not aux_result_ok:
                    aux_result_ok = download_and_write_file(
                        tertiary_url, self.session, save_dir, filename
                    )
                if aux_result_ok:
                    self.downloaded.append(file_obj)
                else:
                    self.not_found.append(file_obj)
                    Lep.msg("<r> - </r>{filename}", filename=filename)


def url_encoded_chars_to_lower_case(url: str) -> str:
    """Change %-escaped chars in string to lower case."""
    lower_url = URL_ENCODED_CHARS_PATTERN.sub(
        lambda matchobj: matchobj.group(0).lower(), url
    )
    return lower_url


def extract_urls_from_episode_list(episodes: LepEpisodeList) -> Dict[str, str]:
    """Extract page URL and its title for each episode object  in list."""
    urls_titles = {
        url_encoded_chars_to_lower_case(ep.url): ep.post_title for ep in episodes
    }
    return urls_titles
