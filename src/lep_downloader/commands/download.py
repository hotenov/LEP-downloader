"""Download command."""
# MIT License
#
# Copyright (c) 2022 Artem Hotenov
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
import sys
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Optional

import click
from click import Context

from lep_downloader import downloader
from lep_downloader.cli_shared import common_options
from lep_downloader.downloader import ATrack
from lep_downloader.downloader import Audio
from lep_downloader.downloader import LepFileList
from lep_downloader.downloader import PagePDF
from lep_downloader.exceptions import DataBaseUnavailableError
from lep_downloader.lep import LepEpisodeList
from lep_downloader.lep import LepLog


def require_to_press_enter(quiet: bool, log: LepLog) -> None:
    """Prevent script closing without reading execution output."""
    if not quiet:
        log.msg("\n", skip_file=True)  # Empty line for console output
        log.msg(
            "<Y><k>Press the [ENTER] key to close 'LEP-downloader'</k></Y>",
            wait_input=True,
        )
        click.confirm(
            "",
            # prompt_suffix="...",
            show_default=False,
        )
        # click.get_current_context().exit()
        sys.exit(0)


def phrase_for_filtered_episodes(  # noqa: C901 'too complex'
    start_num: int,
    end_num: int,
    date_start: Optional[datetime],
    date_end: Optional[datetime],
    last: bool,
) -> str:
    """Compose phrase (or word) for specified episodes."""
    interval = Template("from $left to $right")
    left = right = ""

    if last:
        return "LAST"

    if date_start or date_end:

        date_start = date_start if date_start else LepEpisodeList.default_start_date
        date_end = date_end if date_end else LepEpisodeList.default_end_date
        start_date = date_start.date()
        end_date = date_end.date()

        if start_date == end_date:
            return f"posted on {start_date}"

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        if start_date == LepEpisodeList.default_start_date.date():
            left = "FIRST"
        else:
            left = start_date.strftime(r"%Y-%m-%d")
        if end_date == LepEpisodeList.default_end_date.date():
            right = "LAST"
        else:
            right = end_date.strftime(r"%Y-%m-%d")
        date_interval = interval.substitute(left=left, right=right)
        return date_interval
    else:
        if start_num == 0 and end_num == 0:
            return "Without audio (TEXT)"
        if start_num == end_num:
            return f"Number {start_num}"
        if start_num == 0 and end_num == 9999:
            return "ALL"
        else:
            if start_num > end_num:
                start_num, end_num = end_num, start_num
            left = "FIRST" if start_num == 0 else str(start_num)
            right = "LAST" if end_num == 9999 else str(end_num)
            num_interval = interval.substitute(left=left, right=right)
            return num_interval


@click.command(name="download")
@common_options
@click.pass_context
def cli(  # noqa: C901 'too complex'
    ctx: Context,
    episode: str,
    pdf_yes: bool,
    last_yes: bool,
    start_date: datetime,
    end_date: datetime,
    dest: Path,
    db_url: str,
    quiet: bool,
    debug: bool,
) -> None:
    """Downloads LEP episodes on disk."""
    lep_log: LepLog = ctx.obj["log"]
    lep_dl = downloader.LepDL(db_url, log=lep_log)
    filtered_episodes = LepEpisodeList()
    filtered_files = LepFileList()

    try:
        lep_dl.get_remote_episodes()
    except DataBaseUnavailableError:
        lep_log.msg("<r>JSON database is not available now.</>\n")
        lep_log.msg("<c>Try again later.</c>\n")
        require_to_press_enter(quiet, lep_log)
        click.get_current_context().exit()

    if not lep_dl.db_episodes:  # no valid episode objects
        require_to_press_enter(quiet, lep_log)
        click.get_current_context().exit()

    # Print text interval
    start, end = episode[0], episode[1]
    lep_log.msg(
        "Specified episodes: <g>{phrase}</g>",
        phrase=phrase_for_filtered_episodes(
            int(start), int(end), start_date, end_date, last_yes
        ),
    )

    if not last_yes:
        if start_date or end_date:
            filtered_episodes = lep_dl.db_episodes.filter_by_date(start_date, end_date)
        else:
            filtered_episodes = lep_dl.db_episodes.filter_by_number(*episode)
    else:
        filtered_episodes.append(lep_dl.db_episodes[0])

    lep_dl.files = downloader.gather_all_files(filtered_episodes)
    lep_dl.populate_default_url()

    file_filter = LepFileList([Audio, ATrack])

    if pdf_yes:
        file_filter.append(PagePDF)

    filtered_files = lep_dl.files.filter_by_type(*file_filter)

    lep_dl.detach_existed_files(dest, filtered_files)

    total_number = len(lep_dl.non_existed)

    if total_number > 0:
        if not quiet:
            lep_log.msg(
                "\t<g>{total}</g> non-existing file(s) will be downloaded.",
                total=total_number,
            )
            lep_log.msg(
                "<Y><k>Do you want to continue?</k></Y>",
                wait_input=True,
            )
            if click.confirm(""):
                lep_log.msg("<m>Starting downloading...</m>")
                lep_dl.download_files(dest)
            else:
                lep_log.msg("<c>Your answer is '<y>NO</y>'. Exit.</c>")
        else:
            lep_log.msg("<m>Starting downloading...</m>")
            lep_dl.download_files(dest)
            lep_log.msg(
                "QUIET EXIT: Downloaded: {down_num}; Not Found: {notfound_num}",
                msg_lvl="DEBUG",
                down_num=len(lep_dl.downloaded),
                notfound_num=len(lep_dl.not_found),
            )
    else:
        lep_log.msg("<c>Nothing to download for now.</c>")

    require_to_press_enter(quiet, lep_log)
