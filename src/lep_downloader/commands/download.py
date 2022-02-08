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

import click

from lep_downloader import downloader
from lep_downloader.cli_shared import common_options
from lep_downloader.downloader import ATrack
from lep_downloader.downloader import Audio
from lep_downloader.downloader import LepFileList
from lep_downloader.downloader import PagePDF
from lep_downloader.exceptions import DataBaseUnavailable
from lep_downloader.lep import Lep
from lep_downloader.lep import LepEpisodeList


def require_to_press_enter(quiet: bool) -> None:
    """Prevent script closing without reading execution output."""
    if not quiet:
        Lep.msg(
            "<Y><k>Press [ENTER] key to close 'LEP-downloader'</k></Y>", wait_input=True
        )
        click.confirm(
            "",
            # prompt_suffix="...",
            show_default=False,
        )
        # click.get_current_context().exit()
        sys.exit(0)


@click.command(name="download")
@common_options
def cli(  # noqa: C901 'too complex'
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
    lep_dl = downloader.LepDL(db_url)
    filtered_episodes = LepEpisodeList()
    filtered_files = LepFileList()

    try:
        lep_dl.use_or_get_db_episodes()
    except DataBaseUnavailable:
        Lep.msg("<r>JSON database is not available now.</>\n")
        Lep.msg("<c>Try again later.</c>\n")
        require_to_press_enter(quiet)
        click.get_current_context().exit()

    if not lep_dl.db_episodes:  # no valid episode objects
        require_to_press_enter(quiet)
        click.get_current_context().exit()

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
            click.echo(f"{total_number} non-existing file(s) will be downloaded.")
            # click.echo("Would download file(s). Proceed (y/n)?: ")
            if click.confirm("Do you want to continue?"):
                lep_dl.download_files(dest)
            else:
                click.echo("Your answer is 'NO'. Exit.")
        else:
            lep_dl.download_files(dest)
            Lep.msg(
                "QUIET EXIT: Downloaded: {down_num}; Not Found: {notfound_num}",
                msg_lvl="DEBUG",
                down_num=len(lep_dl.downloaded),
                notfound_num=len(lep_dl.not_found),
            )
    else:
        # click.echo("Nothing to download for now.")
        Lep.msg("Nothing to download for now.")

    require_to_press_enter(quiet)
