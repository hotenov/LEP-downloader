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
"""LEP module for general logic and classes."""
import json
import re
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from functools import total_ordering
from operator import attrgetter
from typing import Any
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Union

import requests

from lep_downloader import config as conf


# COMPILED REGEX PATTERNS #

INVALID_PATH_CHARS_PATTERN = re.compile(conf.INVALID_PATH_CHARS_RE)


@total_ordering
class LepEpisode:
    """LEP episode class.

    Args:
        episode (int): Episode number.
        date (str | datetime | None): Post datetime (default 2000-01-01T00:00:00+00:00).
            It will be converted to UTC timezone. For None value default is set.
        url (str): Final location of post URL.
        post_title (str): Post title
            extracted from tag <a> text and converted to be safe for Windows path.
        post_type (str): Post type ("AUDIO", "TEXT", etc.).
        audios (list): List of links lists (for multi-part episodes).
        parsed_at (str): Parsing datetime in UTC timezone
            with microseconds).
        index (int): Parsing index
            concatenation of URL date and increment (for several posts).
        admin_note (str): Note for administrator
            and storing error message (for bad response)
        updated_at (str): Datetime in UTC when episode was updated
            (usually manually by admin)
        html_title (str): Page title in HTML tag <title>.
            Important: Not stored in JSON database.
    """

    def _convert_date(self, date: Union[datetime, str, None]) -> datetime:
        """Convert string date to datetime object and UTC timezone.

        Input format: 2000-01-01T00:00:00+00:00
        If datetime is passed, then only convert date to UTC timezone.
        """
        if isinstance(date, str):
            converted_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
            converted_date = converted_date.astimezone(timezone.utc)
        else:
            if date is not None:  # To satisfy 'typeguard' check
                converted_date = date.astimezone(timezone.utc)
            else:
                converted_date = datetime(2000, 1, 1, tzinfo=timezone.utc)
        return converted_date

    def __init__(
        self,
        episode: int = 0,
        date: Union[datetime, str, None] = None,
        url: str = "",
        post_title: str = "",
        post_type: str = "",
        parsed_at: str = "",
        index: int = 0,
        audios: Optional[List[List[str]]] = None,
        admin_note: str = "",
        updated_at: str = "",
        html_title: str = "",
    ) -> None:
        """Initialize default instance of LepEpisode."""
        self.episode = episode
        self.date = date
        self.url = url
        self._post_title = post_title
        self._origin_post_title = post_title
        self.post_type = post_type
        self.audios = audios
        self.parsed_at = parsed_at
        self.index = index
        self.admin_note = admin_note
        self.updated_at = updated_at
        self._title = html_title

    @property
    def date(self) -> Any:
        """Episode date."""
        return self._date

    @date.setter
    def date(self, new_post_date: Union[datetime, str, None]) -> None:
        """Episode date setter."""
        self._date = self._convert_date(new_post_date)

    @property
    def post_title(self) -> str:
        """Post title (safe to use as filename)."""
        return self._post_title

    @post_title.setter
    def post_title(self, new_post_title: str) -> None:
        """Post title setter (makes it safe)."""
        self._origin_post_title = new_post_title
        self._post_title = replace_unsafe_chars(new_post_title)

    def __lt__(self, object: Any) -> Any:
        """Compare objects 'less than'."""
        return any(
            (
                self.date < object.date,
                self.index < object.index,
            )
        )

    def __eq__(self, object: Any) -> bool:
        """Compare equal objects."""
        return all(
            (
                self.date == object.date,
                self.index == object.index,
            )
        )

    def __repr__(self) -> str:
        """String representation of LepEpisode object."""
        return f"{self.index}:{self.episode}:{self.post_title[:16]}"


class LepJsonEncoder(json.JSONEncoder):
    """Custom JSONEncoder for LepEpisode objects."""

    def default(self, obj: Any) -> Any:
        """Override 'default' method for encoding JSON objects."""
        if isinstance(obj, LepEpisode):
            date_0200_zone = obj.date.astimezone(timezone(timedelta(hours=2)))
            return {
                "episode": obj.episode,
                "date": date_0200_zone.strftime(r"%Y-%m-%dT%H:%M:%S%z"),
                "url": obj.url,
                "post_title": obj.post_title,
                "post_type": obj.post_type,
                "audios": obj.audios,
                "parsed_at": obj.parsed_at,
                "index": obj.index,
                "admin_note": obj.admin_note,
                "updated_at": obj.updated_at,
            }
        # Let the base class default method raise the TypeError
        return super().default(obj)


def as_lep_episode_obj(dct: Dict[str, Any]) -> Optional[LepEpisode]:
    """Specialize JSON object decoding."""
    try:
        lep_ep = LepEpisode(**dct)
    except TypeError:
        print(f"[WARNING]: Invalid object in JSON!\n\t{dct}")
        return None
    else:
        return lep_ep


class Lep:
    """Represent base class for general attributes."""

    def __init__(self, session: requests.Session = None) -> None:
        """Default instance of LepTemplate.

        Args:
            session (requests.Session): General session for descendants.
        """
        # TODO (hotenov): Take default session from config file.
        # Or move this field into parser / downloader classes only
        self.ses = session if session else requests.Session()


class LepEpisodeList(List[Any]):
    """Represent list of LepEpisode objects."""

    def desc_sort_by_date_and_index(self) -> Any:
        """Return new sorted list by post datetime, then index."""
        sorted_episodes = LepEpisodeList(
            sorted(self, key=attrgetter("date", "index"), reverse=True)
        )
        return sorted_episodes


class Archive(Lep):
    """Represent archive page object."""

    collected_links: ClassVar[Dict[str, str]] = {}
    deleted_links: ClassVar[Set[str]] = set()
    used_indexes: ClassVar[Set[int]] = set()
    episodes: ClassVar[LepEpisodeList] = LepEpisodeList()

    def __init__(self, url: str = "") -> None:
        """Default instance of Archive.

        Args:
            url (str): URL to archive page.
                if not passed, take default from config file.
        """
        super().__init__()
        self.url = url if url else conf.ARCHIVE_URL


def replace_unsafe_chars(filename: str) -> str:
    """Replace most common invalid path characters with '_'."""
    return INVALID_PATH_CHARS_PATTERN.sub("_", filename)
