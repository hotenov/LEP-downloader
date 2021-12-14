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
from typing import Any
from typing import Dict
from typing import List
from typing import Optional


class LepEpisode(object):
    """LEP episode class."""

    def __init__(
        self,
        episode: int = 0,
        date: str = "2000-01-01T00:00:00+00:00",
        url: str = "",
        post_title: str = "",
        post_type: str = "",
        parsing_utc: str = "",
        index: int = 0,
        audios: Optional[List[List[str]]] = None,
        admin_note: str = "",
    ) -> None:
        """Default instance of LepEpisode.

        Args:
            episode (int): Episode number.
            date (str): Post datetime (default 2000-01-01T00:00:00+00:00).
            url (str): Final location of post URL.
            post_title (str): Post title
                extracted from tag <a> and safe for windows path.
            post_type (str): Post type ("AUDIO", "TEXT", etc.).
            audios (list): List of links lists (for multi-part episodes).
            parsing_utc (str): Parsing datetime in UTC timezone
                with microseconds).
            index (int): Parsing index
                concatenation of URL date and increment (for several posts).
            admin_note (str): Note for administrator
                and storing error message (for bad response)
        """
        self.episode = episode
        self.date = date
        self.url = url
        self.post_title = post_title
        self.post_type = post_type
        self.audios = audios
        self.parsing_utc = parsing_utc
        self.index = index
        self.admin_note = admin_note


class LepJsonEncoder(json.JSONEncoder):
    """Custom JSONEncoder for LepEpisode objects."""

    def default(self, obj: Any) -> Any:
        """Override 'default' method for encoding JSON objects."""
        if isinstance(obj, LepEpisode):
            return {
                "episode": obj.episode,
                "date": obj.date,
                "url": obj.url,
                "post_title": obj.post_title,
                "post_type": obj.post_type,
                "audios": obj.audios,
                "parsing_utc": obj.parsing_utc,
                "index": obj.index,
                "admin_note": obj.admin_note,
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
