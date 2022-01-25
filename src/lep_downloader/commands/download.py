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
from datetime import datetime
from pathlib import Path

import click

from lep_downloader import downloader
from lep_downloader.cli_shared import common_options
from lep_downloader.downloader import Audio
from lep_downloader.downloader import LepFileList
from lep_downloader.downloader import PagePDF
from lep_downloader.exceptions import DataBaseUnavailable
from lep_downloader.lep import Lep
from lep_downloader.lep import LepEpisodeList


def require_to_press_enter(quiet: bool) -> None:
    """Prevent script closing without reading execution output."""
    if not quiet:
        click.confirm(
            "Press 'Enter' key to close 'LEP-downloader'",
            # prompt_suffix="...",
            show_default=False,
        )
        click.get_current_context().exit()


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
) -> None:
    """Downloads LEP episodes on disk."""
    filtered_episodes = LepEpisodeList()
    filtered_files = LepFileList()

    try:
        downloader.use_or_get_db_episodes(db_url)
    except DataBaseUnavailable:
        click.echo("JSON database is not available now.\n" + "Try again later.")
        require_to_press_enter(quiet)
        click.get_current_context().exit()

    if not Lep.db_episodes:  # no valid episode objects
        require_to_press_enter(quiet)
        click.get_current_context().exit()

    if not last_yes:
        if start_date or end_date:
            filtered_episodes = Lep.db_episodes.filter_by_date(start_date, end_date)
        else:
            filtered_episodes = Lep.db_episodes.filter_by_number(*episode)
    else:
        filtered_episodes.append(Lep.db_episodes[0])

    downloader.gather_all_files(filtered_episodes)
    downloader.populate_default_url()

    file_filter: LepFileList = LepFileList()
    file_filter.append(Audio)

    if pdf_yes:
        file_filter.append(PagePDF)

    filtered_files = downloader.Downloader.files.filter_by_type(*file_filter)

    downloader.detect_existing_files(filtered_files, dest)

    total_number = len(downloader.Downloader.non_existed)

    if total_number > 0:
        if not quiet:
            click.echo(f"{total_number} non-existing file(s) will be downloaded.")
            # click.echo("Would download file(s). Proceed (y/n)?: ")
            if click.confirm("Do you want to continue?"):
                downloader.download_files(downloader.Downloader.non_existed, dest)
            else:
                click.echo("Your answer is 'NO'. Exit.")
        else:
            downloader.download_files(downloader.Downloader.non_existed, dest)
    else:
        click.echo("Nothing to download for now.")

    require_to_press_enter(quiet)
