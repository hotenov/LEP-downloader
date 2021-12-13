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
"""Module for getting data from the Internet."""
import json
import typing as t

import requests

from lep_downloader.lep import as_lep_episode_obj
from lep_downloader.lep import LepEpisode


s = requests.Session()


def get_web_page_html_text(page_url: str, session: requests.Session) -> t.Any:
    """Return HTML text of LEP archive page."""
    final_location = page_url
    is_url_ok = False
    with session:
        try:
            resp = session.get(page_url, timeout=(6, 33))
            final_location = resp.url
            if not resp.ok:
                resp.raise_for_status()
        except requests.exceptions.HTTPError as err:
            return (f"[ERROR]: {err}", final_location, is_url_ok)
        except requests.exceptions.Timeout as err:
            return (f"[ERROR]: Timeout | {err}", final_location, is_url_ok)
        except requests.exceptions.ConnectionError as err:
            return (f"[ERROR]: Bad request | {err}", final_location, is_url_ok)
        except Exception as err:
            return (
                f"[ERROR]: Unhandled error | {err}",
                final_location,
                is_url_ok,
            )
        else:
            resp.encoding = "utf-8"
            final_location = resp.url
            is_url_ok = True
            return (resp.text, final_location, is_url_ok)


def get_list_of_valid_episodes(
    json_body: str,
    json_url: t.Optional[str] = None,
) -> t.List[LepEpisode]:
    """Return list of valid (not None) LepEpisode objects."""
    db_episodes: t.List[LepEpisode] = []
    try:
        db_episodes = json.loads(json_body, object_hook=as_lep_episode_obj)
    except json.JSONDecodeError:
        print(f"[ERROR]: Data is not a valid JSON document.\n\tURL: {json_url}")
        return []
    else:
        is_db_str: bool = isinstance(db_episodes, str)
        db_episodes = [obj for obj in db_episodes if obj]
        if not db_episodes or is_db_str:
            print(
                f"[WARNING]: JSON file ({json_url}) has no valid episode objects."  # noqa: E501,B950
            )
            return []
        else:
            return db_episodes
