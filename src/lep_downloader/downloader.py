"""LEP module for downloading logic."""
import re
import typing as t
from pathlib import Path

from lep_downloader import config as conf
from lep_downloader.lep import LepEpisode


# COMPILED REGEX PATTERNS #

INVALID_PATH_CHARS_PATTERN = re.compile(conf.INVALID_PATH_CHARS_RE)


def select_all_audio_episodes(
    db_episodes: t.List[LepEpisode],
) -> t.List[LepEpisode]:
    """Return filtered list with AUDIO episodes."""
    audio_episodes = [ep for ep in db_episodes if ep.post_type == "AUDIO"]
    return audio_episodes


def get_audios_data(audio_episodes: t.List[LepEpisode]) -> t.Any:
    """Return list with audios data for next downloading."""
    audios_data: t.List[object] = []
    is_multi_part: bool = False
    for ep in reversed(audio_episodes):
        short_date = ep.date[:10]
        title = ep.post_title
        audios = ep.audios
        if audios is not None:
            is_multi_part = False if len(audios) < 2 else True
        else:
            audios = []
        data_item = [short_date, title, audios, is_multi_part]
        audios_data.append(data_item)
    return audios_data


def bind_name_and_file_url(audios_data: t.Any) -> t.List[t.Tuple[str, t.List[str]]]:
    """Return list of tuples (filename, list(file_urls))."""
    single_part_name: str = ""
    audios_links: t.List[t.Tuple[str, t.List[str]]] = []
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
    audios_links: t.List[t.Tuple[str, t.List[str]]],
    save_dir: Path,
    file_ext: str = ".mp3",
) -> t.Tuple[t.List[t.Tuple[str, t.List[str]]], t.List[t.Tuple[str, t.List[str]]]]:
    """Return lists for existing and non-existing files."""
    existing: t.List[t.Tuple[str, t.List[str]]] = []
    non_existing: t.List[t.Tuple[str, t.List[str]]] = []
    only_files_by_ext: t.List[str] = []
    only_files_by_ext = [
        p.stem for p in save_dir.glob("*") if p.suffix.lower() == file_ext
    ]
    for audio in audios_links:
        if audio[0] in only_files_by_ext:
            existing.append(audio)
        else:
            non_existing.append(audio)
    return (existing, non_existing)
