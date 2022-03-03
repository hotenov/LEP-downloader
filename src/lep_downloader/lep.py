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
import sys
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from functools import partial
from functools import total_ordering
from operator import attrgetter
from pathlib import Path
from typing import Any
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import requests
from loguru import logger

from lep_downloader import config as conf
from lep_downloader.exceptions import DataBaseUnavailableError


default_episode_datetime = datetime(2000, 1, 1, tzinfo=timezone.utc)

# COMPILED REGEX PATTERNS #

INVALID_PATH_CHARS_PATTERN = re.compile(conf.INVALID_PATH_CHARS_RE)

# PRODUCTION SESSION #
PROD_SES = requests.Session()
PROD_SES.headers.update(conf.ses_headers)


# SETUP LOGGER #
logger = logger.opt(colors=True)
logger.opt = partial(logger.opt, colors=True)  # type: ignore
new_level_print = logger.level("PRINT", no=22)
new_level_missing = logger.level("MISSING", no=33)


def stdout_formatter(record: Any) -> str:
    """Return formatter string for console sink.

    Args:
        record (Any): Loguru's record dict.

    Returns:
        Format string for stdout log
            ``"{message}" + end``

    Notes:
        Controling ending character for log message by
        storing it in the 'extra' dict and changing later via bind().
        Default is the newline character.
    """
    end: str = record["extra"].get("end", "\n")
    return "{message}" + end


def logfile_formatter(record: Any) -> str:
    """Return formatter string for log file sink.

    Args:
        record (Any): Loguru's record dict.

    Returns:
        Format string for log file
            ``{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "{message}" + LF``
                LF - newline character here.

    Note:
        .. code-block:: text

            2022-02-25 07:20:48.909 | PRINT    | Running script...⏎
            2022-02-25 07:20:48.917 | PRINT    | Starting parsing...

    """
    date = "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    level = "{level: <8} | "
    return date + level + "{message}" + "\n"


def init_lep_log(
    debug: bool = False,
    logfile: str = conf.DEBUG_FILENAME,
) -> Any:
    """Create custom logger object.

    Args:
        debug (bool): Debug log or not. Defaults to False.
        logfile (str): Name of the logfile.
            Defaults to :const:`config.DEBUG_FILENAME` = "_lep_debug_.log"

    Returns:
        Custom loguru.logger object
    """
    lep_log = logger
    lep_log.remove()
    file_log = Path(logfile)

    if debug:
        lep_log.add(
            file_log,
            format=logfile_formatter,
            filter=lambda record: "to_file" in record["extra"],
        )

    lep_log.add(
        sys.stdout,
        format=stdout_formatter,
        filter=lambda record: "to_console" in record["extra"],
    )
    return lep_log


@total_ordering
class LepEpisode:
    """LEP episode class.

    Args:
        episode (int): Episode number.
        date (str | datetime): Post datetime.
            It will be converted to aware `datetime` object (with timezone).
            If None, defaults to `datetime` equaling "2000-01-01T00:00:00+00:00".
        url (str): Final location of web post URL.
        post_title (str): Post title
            extracted from link text (unsafe).
        post_type (str): Post type ("AUDIO", "TEXT", etc.).
        files (dict | None): Dictionary with files for episode. Each key of it is
            a file category ("audios", "audiotrack", "page_pdf", etc).
            If None defaults to empty dict.
        parsed_at (str): Parsing datetime in UTC timezone, with microseconds.
        index (int): Parsing index,
            concatenation of date from URL and increment (for several posts in a day).
        admin_note (str): Note for administrator
            and storing error message (for bad response during parsing)
        updated_at (str): Datetime in UTC when episode was updated
            (usually manually by admin).
        html_title (str): Page title extracted from HTML tag <title>.
            **Important:** Not stored in JSON database.
    """

    def _convert_date(self, date: Union[datetime, str]) -> Tuple[datetime, str]:
        """Convert string datetime to aware datetime object.

        String datetime format: 2000-01-01T00:00:00+00:00
        If `datetime` is passed, it will be set "as-is".
        """
        converted_date = default_episode_datetime
        short_date: str = converted_date.strftime(r"%Y-%m-%d")
        if isinstance(date, str):
            converted_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
            short_date = converted_date.strftime(r"%Y-%m-%d")
        else:
            short_date = date.strftime(r"%Y-%m-%d")
            converted_date = date
        return converted_date, short_date

    def __init__(
        self,
        episode: int = 0,
        date: Any = default_episode_datetime,
        url: str = "",
        post_title: str = "",
        post_type: str = "",
        parsed_at: str = "",
        index: int = 0,
        files: Optional[Dict[str, Any]] = None,
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
        self.files = files if files else {}
        self.parsed_at = parsed_at
        self.index = index
        self.admin_note = admin_note
        self.updated_at = updated_at
        self._title = html_title

    @property
    def date(self) -> Any:
        """Episode datetime (with timezone).

        To be accurate, posting datetime on the website.
        """
        return self._date

    @date.setter
    def date(self, new_post_date: Union[datetime, str]) -> None:
        """Episode date setter."""
        self._date, self._short_date = self._convert_date(new_post_date)

    @property
    def short_date(self) -> str:
        """Episode short date.

        It's the same as posting date in the episode URL,
        just formatted as "YYYY-MM-DD".
        """
        return self._short_date

    @property
    def post_title(self) -> str:
        """Post title converted to be safe for Windows path (filename).

        Conversion via :func:`replace_unsafe_chars`.
        """
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
        return f"{self.index}:{self.episode:{4}}:{self.post_title[:16]}"


class LepEpisodeList(List[Any]):
    """Represent list of LepEpisode objects.

    Attributes:
        default_start_date (datetime): Min date.
            It's equal to "1999-01-01T00:01:00+00:00"
        default_end_date (datetime): Max date.
            It's equal to "2999-12-31T23:55:00+00:00"
    """

    def desc_sort_by_date_and_index(self) -> Any:
        """Sort LepEpisodeList by post datetime.

        Returns:
            :class:`LepEpisodeList`: New sorted LepEpisodeList.

        Notes:
            Sort is descending (last by date will be first).
            Sort goes by two attrs: "date" and "index".
        """
        sorted_episodes = LepEpisodeList(
            sorted(self, key=attrgetter("date", "index"), reverse=True)
        )
        return sorted_episodes

    def filter_by_type(self, type: str) -> Any:
        """Filter list by episode type.

        Args:
            type (str): Episode type ("AUDIO", "TEXT", etc)

        Returns:
            :class:`LepEpisodeList`: New filtered LepEpisodeList.
        """
        filtered = LepEpisodeList(ep for ep in self if ep.post_type == type)
        return filtered

    def filter_by_number(self, start: int, end: int) -> Any:
        """Filter list by episode number.

        Args:
            start (int): Episode number (left bound)
            end (int): Episode number (right bound)

        Returns:
            :class:`LepEpisodeList`: New filtered LepEpisodeList.

        Notes:
            If end < start - they are swapped.
        """
        if start > end:
            start, end = end, start
        filtered = LepEpisodeList(
            ep for ep in self if ep.episode >= start and ep.episode <= end
        )
        return filtered

    default_start_date = datetime(1999, 1, 1, 0, 1, tzinfo=timezone.utc)
    default_end_date = datetime(2999, 12, 31, 23, 55, tzinfo=timezone.utc)

    def filter_by_date(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Any:
        """Filter list by episode date.

        Args:
            start (datetime, optional): Episode date (left bound).
                If start is None, defaults to min date
                :class:`LepEpisodeList.default_start_date`.
            end (datetime, optional): Episode date (right bound).
                If end is None, defaults to max date
                :class:`LepEpisodeList.default_end_date`.

        Returns:
            :class:`LepEpisodeList`: New filtered LepEpisodeList.

        Notes:
            If end < start - they are swapped.
        """
        start = start if start else self.default_start_date
        end = end if end else self.default_end_date

        if start.date() > end.date():
            start, end = end, start

        filtered = LepEpisodeList(
            ep
            for ep in self
            if ep.date.date() >= start.date() and ep.date.date() <= end.date()
        )

        return filtered


class LepJsonEncoder(json.JSONEncoder):
    """Custom JSONEncoder for LepEpisode objects."""

    def default(self, obj: Any) -> Any:
        """Override 'default' method for encoding JSON objects.

        Args:
            obj (Any): Object for encoding.

        Returns:
            Any: If object is :class:`LepEpisode` returns dict.
                Otherwise, TypeError exception is raised.
        """
        if isinstance(obj, LepEpisode):
            return {
                "episode": obj.episode,
                "date": obj.date.strftime(r"%Y-%m-%dT%H:%M:%S%z"),
                "url": obj.url,
                "post_title": obj.post_title,
                "post_type": obj.post_type,
                "files": obj.files,
                "parsed_at": obj.parsed_at,
                "index": obj.index,
                "admin_note": obj.admin_note,
                "updated_at": obj.updated_at,
            }
        # Let the base class default method raise the TypeError
        return super().default(obj)


def as_lep_episode_obj(dct: Dict[str, Any]) -> Any:
    """Specialize JSON objects decoding.

    Args:
        dct (dict): Dictionary object from JSON
            (including nested dictionaries).

    Returns:
        Any: :class:`LepEpisode` object or None.

    Notes:
        If dictionary is empty or has "audios" key it's returned "as-is".
        Returns None if TypeError was raised.

    """
    if dct == {} or ("audios" in dct):
        return dct
    try:
        lep_ep = LepEpisode(**dct)
    except TypeError:
        # Message only to log file
        Lep.cls_lep_log.msg("Invalid object in JSON: {dct}", dct=dct, msg_lvl="WARNING")
        return None
    else:
        return lep_ep


@dataclass
class LepLog:
    """Represent LepLog object.

    Args:
        debug (bool): Debug mode flag. Defaults to False.
        logfile (str): Name of log file.
            Defaults to :const:`config.DEBUG_FILENAME` = "_lep_debug_.log".

    Attributes:
        debug (bool): Debug mode flag (True / False).
        logfile (str): Name of log file.
        lep_log (loguru.logger): Custom *loguru.logger* object,
            which is returned from :func:`init_lep_log`.
    """

    debug: bool = False
    logfile: str = conf.DEBUG_FILENAME

    def __post_init__(self) -> None:
        """Create logger for LepLog instance."""
        self.lep_log = init_lep_log(debug=self.debug, logfile=self.logfile)

    def msg(
        self,
        msg: str,
        *,
        skip_file: bool = False,
        one_line: bool = True,
        msg_lvl: str = "PRINT",
        wait_input: bool = False,
        **kwargs: Any,
    ) -> None:
        """Output message to console or log file.

        Args:
            msg (str): Message to output. Supports
                `loguru <https://loguru.readthedocs.io/en/stable/api/logger.html#color>`__
                color markups.
            skip_file (bool): Flag to skip writing to logfile (even in Debug mode).
                Defaults to False.
            one_line (bool): Flag to replace new line character
                with Unicode char of it, i.e. ⏎. Defaults to True.
            msg_lvl (str): Message level. Defaults to "PRINT".
            wait_input (bool): Flag to stay on line after printing message to console.
                Defaults to False.
            kwargs (Any): Arbitrary keyword arguments.

        Notes:
            If Debug mode is False and message level is "PRINT",
            method outputs to console only.
            Otherwise, it duplicates all console messages to log file too
            (with level PRINT).
            Also records (messages) for other log levels goes into file
            (if `skip_file` is not True).
        """  # noqa: E501,B950
        if msg_lvl == "PRINT" and not self.debug:
            if wait_input:
                self.lep_log.bind(to_console=True, end="").info(msg, **kwargs)
            else:
                self.lep_log.bind(to_console=True).info(msg, **kwargs)
        else:
            msg_oneline = msg
            if one_line:
                msg_oneline = msg.replace("\n", "⏎")

            if msg_lvl == "PRINT" and skip_file:
                self.lep_log.bind(to_console=True).info(msg, **kwargs)
            elif msg_lvl == "PRINT" and wait_input:
                self.lep_log.bind(to_console=True, end="").info(msg, **kwargs)
                self.lep_log.bind(to_file=True).log(msg_lvl, msg_oneline, **kwargs)
            elif msg_lvl == "PRINT":
                self.lep_log.bind(to_console=True).info(msg, **kwargs)
                self.lep_log.bind(to_file=True).log(msg_lvl, msg_oneline, **kwargs)
            else:
                if self.debug:
                    self.lep_log.bind(to_file=True).log(msg_lvl, msg_oneline, **kwargs)


class Lep:
    """Represent base class for LEP's general attributes and methods.

    Args:
        session (requests.Session, optional): Global session for descendants.
        log (:class:`LepLog`, optional): Log object where to output messages.

    Attributes:
        cls_session (requests.Session): Class session.
            Default is taken from module variable :const:`PROD_SES`
        cls_lep_log (LepLog): Class log object where to output messages.
            Default is LepLog() - only **stdout** output.
        json_body (str): Content of JSON database file.
    """

    cls_session: ClassVar[requests.Session] = requests.Session()
    json_body: ClassVar[str] = ""
    cls_lep_log: ClassVar[LepLog]

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        log: Optional[LepLog] = None,
    ) -> None:
        """Default instance of Lep class."""
        self.session = session if session else PROD_SES
        self.lep_log = log if log else LepLog()
        Lep.cls_session = self.session
        Lep.cls_lep_log = self.lep_log

    @classmethod
    def get_web_document(
        cls,
        page_url: str,
        session: Optional[requests.Session] = None,
    ) -> Tuple[str, str, bool]:
        """Get text content of web document (HTML, JSON, etc.).

        Args:
            page_url (str): URL for getting text response.
            session (requests.Session, optional): Session object
                to send request. Default is :class:`Lep.cls_session`.

        Returns:
            A tuple (resp.text, final_location, is_url_ok) where
                - resp.text (str) is text content of URL response
                - final_location (str) is location after all redirections
                - is_url_ok (bool) is flag of URL status
        """
        session = session if session else cls.cls_session
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
                is_url_ok = True
                return (resp.text, final_location, is_url_ok)

    @classmethod
    def extract_only_valid_episodes(
        cls,
        json_body: str,
        json_url: Optional[str] = None,
    ) -> LepEpisodeList:
        """Return list of valid (not None) LepEpisode objects.

        Args:
            json_body (str): Content of JSON database file.
            json_url (str, optional): JSON URL, only for printing it to output.

        Returns:
            :class:`LepEpisodeList`: List of :class:`LepEpisode` objects.
                It's empty if there are no valid objects at all.
        """
        db_episodes = LepEpisodeList()
        try:
            db_episodes = json.loads(json_body, object_hook=as_lep_episode_obj)
        except json.JSONDecodeError:
            cls.cls_lep_log.msg(
                "<r>ERROR: Data is not a valid JSON document.</r>\n\tURL: {json_url}",
                json_url=json_url,
            )
            return LepEpisodeList()
        else:
            is_db_str: bool = isinstance(db_episodes, str)
            # Remove None elements
            db_episodes = LepEpisodeList(obj for obj in db_episodes if obj)
            if not db_episodes or is_db_str:
                cls.cls_lep_log.msg(
                    "<y>WARNING: JSON file ({json_url}) has no valid episode objects.</y>",  # noqa: E501,B950
                    json_url=json_url,
                )
                return LepEpisodeList()
            else:
                return db_episodes

    @classmethod
    def get_db_episodes(
        cls,
        json_url: str,
        session: Optional[requests.Session] = None,
    ) -> LepEpisodeList:
        """Get valid episodes from JSON.

        Args:
            json_url (str): URL to JSON database file.
            session (requests.Session, optional): Session object
                to send request. Default is :class:`Lep.cls_session`.

        Returns:
            :class:`LepEpisodeList`:

        Raises:
            DataBaseUnavailableError: if JSON is unavailable
        """
        session = session if session else cls.cls_session
        db_episodes = LepEpisodeList()
        cls.json_body, _, status_db_ok = Lep.get_web_document(json_url, session)
        if status_db_ok:
            db_episodes = Lep.extract_only_valid_episodes(cls.json_body, json_url)
        else:
            raise DataBaseUnavailableError()
        return db_episodes


def replace_unsafe_chars(filename: str) -> str:
    """Replace most common invalid path characters with '_'.

    Args:
        filename (str): Filename (should be a string representing
            the final path component) without the drive and root.

    Returns:
        Safe name for writing file on Windows OS (and others).

    Example:
        >>> import lep_downloader.lep
        >>> unsafe = "What/ will: be* replaced?.mp3"
        >>> lep_downloader.lep.replace_unsafe_chars(unsafe)
        'What_ will_ be_ replaced_.mp3'
    """
    return INVALID_PATH_CHARS_PATTERN.sub("_", filename)
