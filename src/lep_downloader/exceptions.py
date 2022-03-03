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
"""Module for LEP custom exceptions."""
from typing import Any


class LepExceptionError(Exception):
    """Base class for exceptions in 'lep_downloader' package."""

    pass


class NoEpisodeLinksError(LepExceptionError):
    """Raised when no valid episode links on page.

    Args:
        url (str): URL which has no episode links. Default is empty string.
        message (str): Explanation of the error. Default is empty string.
    """

    def __init__(self, url: str = "", message: str = "") -> None:
        """Initialize  NoEpisodeLinksError exception."""
        #: URL which has no episode links.
        self.url: str = url
        #: Explanation of the error.
        self.message: str = message


class NotEpisodeURLError(LepExceptionError):
    """Raised when given URL is not episode / archive URL.

    Args:
        url (str): URL which has no <article> tag. Default is empty string.
        message (str): Explanation of the error. Default is empty string.
    """

    def __init__(self, url: str = "", message: str = "") -> None:
        """Initialize  NotEpisodeURLError exception."""
        #: URL which has no <article> tag.
        self.url: str = url
        #: Explanation of the error.
        self.message: str = message


class LepEpisodeNotFoundError(LepExceptionError):
    """Raised when given episode URL is not available.

    First argument serves to pass partially filled episode instance,
    in order to add it as 'bad' episode.

    Args:
        episode (LepEpisode): Episode instance.
        message (str): Explanation of the error. Default is empty string.
    """

    def __init__(self, episode: Any, message: str = "") -> None:
        """Initialize  NotEpisodeURLError exception."""
        from lep_downloader.lep import LepEpisode

        #: Episode instance.
        self.bad_episode: LepEpisode = episode
        #: Explanation of the error.
        self.message: str = message


class DataBaseUnavailableError(LepExceptionError):
    """Raised when JSON database file is not available.

    Args:
        message (str): Explanation of the error. Default is empty string.
    """

    def __init__(self, message: str = "") -> None:
        """Initialize  DataBaseUnavailable exception."""
        #: Explanation of the error.
        self.message: str = message


class NoEpisodesInDataBaseError(LepExceptionError):  # pragma: no cover for Python 3.10
    """Raised when JSON database has no any valid episode.

    Args:
        message (str): Explanation of the error. Default is empty string.
    """

    def __init__(self, message: str = "") -> None:
        """Initialize  NoEpisodesInDataBase exception."""
        #: Explanation of the error.
        self.message: str = message
