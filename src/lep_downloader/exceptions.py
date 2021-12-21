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
from lep_downloader.lep import LepEpisode


class LepException(Exception):
    """Base class for exceptions in 'lep_downloader' package."""

    pass


class NoEpisodeLinksError(LepException):
    """Raised when no valid episode links on page.

    Attributes:
        url (str): URL which has no episode links. Default is ''
        message (str): Explanation of the error. Default is ''
    """

    def __init__(self, url: str = "", message: str = "") -> None:
        """Initialize  NoEpisodeLinksError exception."""
        self.url = url
        self.message = message


class NotEpisodeURLError(LepException):
    """Raised when given URL is not episode / archive URL.

    Attributes:
        url (str): URL which has <article> tag. Default is ''
        message (str): Explanation of the error. Default is ''
    """

    def __init__(self, url: str = "", message: str = "") -> None:
        """Initialize  NotEpisodeURLError exception."""
        self.url = url
        self.message = message


class LepEpisodeNotFound(LepException):
    """Raised when given episode URL is not available.

    Attributes:
        episode (LepEpisode): Episode object.
            Partially filled to add as 'bad' episode.
        message (str): Explanation of the error. Default is ''
    """

    def __init__(self, episode: LepEpisode, message: str = "") -> None:
        """Initialize  NotEpisodeURLError exception."""
        self.bad_episode = episode
        self.message = message
