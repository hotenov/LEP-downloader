"""LEP module for downloading logic."""
import re
from pathlib import Path
from typing import List
from typing import Tuple

from lep_downloader import config as conf
from lep_downloader.lep import LepEpisode

DataForEpisodeAudio = List[Tuple[str, str, List[List[str]], bool]]
NamesWithAudios = List[Tuple[str, List[str]]]


# COMPILED REGEX PATTERNS #

INVALID_PATH_CHARS_PATTERN = re.compile(conf.INVALID_PATH_CHARS_RE)


def select_all_audio_episodes(
    db_episodes: List[LepEpisode],
) -> List[LepEpisode]:
    """Return filtered list with AUDIO episodes."""
    audio_episodes = [ep for ep in db_episodes if ep.post_type == "AUDIO"]
    return audio_episodes


def get_audios_data(audio_episodes: List[LepEpisode]) -> DataForEpisodeAudio:
    """Return list with audios data for next downloading."""
    audios_data: DataForEpisodeAudio = []
    is_multi_part: bool = False
    for ep in reversed(audio_episodes):
        short_date = ep.date[:10]
        title = ep.post_title
        audios = ep.audios
        if audios is not None:
            is_multi_part = False if len(audios) < 2 else True
        else:
            audios = []
        data_item = (short_date, title, audios, is_multi_part)
        audios_data.append(data_item)
    return audios_data


def bind_name_and_file_url(audios_data: DataForEpisodeAudio) -> NamesWithAudios:
    """Return list of tuples (filename, list(file_urls))."""
    single_part_name: str = ""
    audios_links: NamesWithAudios = []
    for item in audios_data:
        short_date, title = item[0], item[1]
        audios, is_multi_part = item[2], item[3]
        single_part_name = f"[{short_date}] # {title}"
        safe_part_name = INVALID_PATH_CHARS_PATTERN.sub("_", single_part_name)
        if is_multi_part:
            for i, audio_part in enumerate(audios, start=1):
                part_name = safe_part_name + f" [Part {str(i).zfill(2)}]"
                part_item = (part_name, audio_part)
                audios_links.append(part_item)
        else:
            binding = (safe_part_name, item[2][0])
            audios_links.append(binding)
    return audios_links


def detect_existing_files(
    audios_links: NamesWithAudios,
    save_dir: Path,
    file_ext: str = ".mp3",
) -> Tuple[NamesWithAudios, NamesWithAudios]:
    """Return lists for existing and non-existing files."""
    existing: NamesWithAudios = []
    non_existing: NamesWithAudios = []
    only_files_by_ext: List[str] = []
    only_files_by_ext = [
        p.stem for p in save_dir.glob("*") if p.suffix.lower() == file_ext
    ]
    for audio in audios_links:
        if audio[0] in only_files_by_ext:
            existing.append(audio)
        else:
            non_existing.append(audio)
    return (existing, non_existing)
