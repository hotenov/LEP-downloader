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
"""App configuration module."""


ARCHIVE_URL = "https://hotenov.com"

JSON_DB_URL = "https://hotenov.com/some_json.json"

LOCAL_ARCHIVE_HTML = "2021-08-10_lep-archive-page-content-pretty.html"
LOCAL_JSON_DB = "mocked-db-json-equal-786-objects.json"

# yapf: disable
SHORT_LINKS_MAPPING_DICT = {
    "http://wp.me/p4IuUx-7PL":
        "https://teacherluke.co.uk/2017/06/20/460-catching-up-with-amber-paul-6-feat-sarah-donnelly/",  # noqa: E501,B950
    "http://wp.me/p4IuUx-7C6":
        "https://teacherluke.co.uk/2017/04/25/444-the-rick-thompson-report-snap-general-election-2017/",  # noqa: E501,B950
    "http://wp.me/p4IuUx-7C4":
        "https://teacherluke.co.uk/2017/04/21/443-the-trip-to-japan-part-2/",
    "http://wp.me/p4IuUx-7BQ":
        "https://teacherluke.co.uk/2017/04/21/442-the-trip-to-japan-part-1/",
    "http://wp.me/p4IuUx-7BO":
        "https://teacherluke.co.uk/2017/04/18/441-andy-johnson-at-the-iatefl-conference/",  # noqa: E501,B950
    "http://wp.me/p4IuUx-7Av":
        "https://teacherluke.co.uk/2017/03/28/436-the-return-of-the-lying-game-with-amber-paul-video/",  # noqa: E501,B950
    "http://wp.me/p4IuUx-7zK":
        "https://teacherluke.co.uk/2017/03/26/i-was-interviewed-on-my-fluent-podcast-with-daniel-goodson/",  # noqa: E501,B950
    "http://wp.me/p4IuUx-7sg":
        "https://teacherluke.co.uk/2017/01/10/415-with-the-family-part-3-more-encounters-with-famous-people/",  # noqa: E501,B950
    "https://wp.me/p4IuUx-29":
        "https://teacherluke.co.uk/2011/10/11/notting-hill-carnival-video-frustration-out-takes/",  # noqa: E501,B950
}
# yapf: enable

IRRELEVANT_LINKS = ("https://wp.me/P4IuUx-82H",)

EPISODE_LINK_RE = r"https?://((?P<short>wp\.me/p4IuUx-[\w-]+)|(teacherluke\.(co\.uk|wordpress\.com)/(?P<date>\d{4}/\d{2}/\d{2})/))"  # noqa: E501,B950

INVALID_PATH_CHARS_RE = r"[<>:\"/\\\\|?*]"
