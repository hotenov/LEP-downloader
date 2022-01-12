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
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar
from typing import List
from typing import Tuple

import requests

from lep_downloader import config as conf
from lep_downloader.exceptions import EmptyDownloadsBunch
from lep_downloader.exceptions import NoEpisodesInDataBase
from lep_downloader.lep import Lep
from lep_downloader.lep import LepEpisode


DataForEpisodeAudio = List[Tuple[str, str, List[List[str]], bool]]
NamesWithAudios = List[Tuple[str, List[str]]]


# COMPILED REGEX PATTERNS #

INVALID_PATH_CHARS_PATTERN = re.compile(conf.INVALID_PATH_CHARS_RE)


# STATISTICS (LOG) DICTIONARIES #

# successful_downloaded: Dict[str, str] = {}
# unavailable_links: Dict[str, str] = {}
# already_on_disc: Dict[str, str] = {}
# duplicated_links: Dict[str, str] = {}


# def select_all_audio_episodes(
#     db_episodes: List[LepEpisode],
# ) -> List[LepEpisode]:
#     """Return filtered list with AUDIO episodes."""
#     audio_episodes = [ep for ep in db_episodes if ep.post_type == "AUDIO"]
#     return audio_episodes


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
    primary_url = secondary_url = tertiary_url = ""

    for i, part_links in enumerate(audios, start=start):
        part_no = i
        part_urls_number = len(part_links)
        if part_urls_number == 1:
            primary_url = part_links[0]
        else:
            if part_urls_number == 2:
                primary_url = part_links[0]
                secondary_url = part_links[1]
            if part_urls_number == 3:
                primary_url = part_links[0]
                secondary_url = part_links[1]
                tertiary_url = part_links[2]
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


# def get_audios_data(audio_episodes: List[LepEpisode]) -> DataForEpisodeAudio:
#     """Return list with audios data for next downloading."""
#     audios_data: DataForEpisodeAudio = []
#     is_multi_part: bool = False
#     for ep in reversed(audio_episodes):
#         short_date = ep._short_date
#         title = ep.post_title
#         audios = ep.files["audios"]
#         if audios is not None:
#             is_multi_part = False if len(audios) < 2 else True
#         else:
#             audios = []
#         data_item = (short_date, title, audios, is_multi_part)
#         audios_data.append(data_item)
#     return audios_data
def gather_all_audio_files(audio_episodes: List[LepEpisode]) -> None:
    """Skim passed episode list and collect all audio files.

    Add each file to shared 'files' list fo further actions.
    """
    for ep in reversed(audio_episodes):
        audios = ep.files["audios"]
        if audios:
            add_each_audio_to_shared_list(
                ep.index, ep.post_title, ep._short_date, audios
            )


# def bind_name_and_file_url(audios_data: DataForEpisodeAudio) -> NamesWithAudios:
#     """Return list of tuples (filename, list(file_urls))."""
#     single_part_name: str = ""
#     audios_links: NamesWithAudios = []
#     for item in audios_data:
#         short_date, title = item[0], item[1]
#         audios, is_multi_part = item[2], item[3]
#         single_part_name = f"[{short_date}] # {title}"
#         safe_part_name = INVALID_PATH_CHARS_PATTERN.sub("_", single_part_name)
#         if is_multi_part:
#             for i, audio_part in enumerate(audios, start=1):
#                 part_name = safe_part_name + f" [Part {str(i).zfill(2)}]"
#                 part_item = (part_name, audio_part)
#                 audios_links.append(part_item)
#         else:
#             binding = (safe_part_name, item[2][0])
#             audios_links.append(binding)
#     return audios_links


# def detect_existing_files(
#     audios_links: List[Tuple[str, str]],
#     save_dir: Path,
#     file_ext: str = ".mp3",
# ) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
#     """Return lists for existing and non-existing files."""
#     existing: List[Tuple[str, str]] = []
#     non_existing: List[Tuple[str, str]] = []
#     only_files_by_ext: List[str] = []
#     only_files_by_ext = [
#         p.stem + file_ext for p in save_dir.glob("*") if p.suffix.lower() == file_ext
#     ]
#     for audio in audios_links:
#         if audio[0] in only_files_by_ext:
#             existing.append(audio)
#         else:
#             non_existing.append(audio)
#     return (existing, non_existing)
def detect_existing_files(
    files: List[LepFile],
    save_dir: Path,
) -> None:
    """Separate lists for existing and non-existing files."""
    Downloader.existed = []
    Downloader.non_existed = []
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

    downloaded: ClassVar[List[LepFile]] = []
    not_found: ClassVar[List[LepFile]] = []
    # existed: ClassVar[Dict[str, str]] = {}

    files: ClassVar[List[LepFile]] = []
    existed: ClassVar[List[LepFile]] = []
    non_existed: ClassVar[List[LepFile]] = []

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


def construct_audio_links_bunch() -> None:
    """Constract audio links with filenames for them."""
    # if not Lep.db_episodes:
    #     Lep.db_episodes = Lep.get_db_episodes(json_url)
    # take_or_get_db_episodes(json_url)

    # audio_links: NamesWithAudios = []
    if Lep.db_episodes:
        audio_episodes = Lep.db_episodes.filter_by_type("AUDIO")
        # only_audio_data = get_audios_data(audio_episodes)
        # audio_links = bind_name_and_file_url(only_audio_data)
        gather_all_audio_files(audio_episodes)
    else:
        raise NoEpisodesInDataBase(
            "JSON is available, but\nthere are NO episodes in this file. Exit."
        )


def download_files(
    downloads_bunch: List[LepFile],
    save_dir: Path,
    # file_ext: str = ".mp3",
) -> None:
    """Download files from passed links bunch."""
    if not downloads_bunch:
        raise EmptyDownloadsBunch()
    for file_obj in downloads_bunch:
        # file_stem: str = item[0]
        # links: List[str] = item[1]
        # filename = file_stem + file_ext
        filename = file_obj.filename

        # primary_link = links[0]
        primary_link = file_obj.primary_url
        if Path(save_dir / filename).exists():
            Downloader.existed.append(file_obj)
            continue  # Skip already downloaded file on disc.
        # if primary_link in successful_downloaded:
        #     duplicated_links[primary_link] = filename
        #     continue  # Skip already processed URL.

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
