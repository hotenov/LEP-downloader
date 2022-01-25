"""CLI main click group."""
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
from click import Context

from lep_downloader import __version__
from lep_downloader.cli_shared import common_options
from lep_downloader.cli_shared import MyCLI
from lep_downloader.commands.download import cli as download_cli


@click.command(
    cls=MyCLI,
    invoke_without_command=True,
)
@click.version_option(version=__version__)
@common_options
@click.pass_context
def cli(
    ctx: Context,
    episode: str,
    pdf_yes: bool,
    last_yes: bool,
    start_date: datetime,
    end_date: datetime,
    dest: Path,
    db_url: str,
    quiet: bool,
) -> None:
    """LEP-downloader - console application.

    Get free episodes of Luke's English Podcast archive page.
    """
    click.echo(f"cli() in '{Path(__file__).name}' was executed...")

    if ctx.invoked_subcommand is None:
        ctx.forward(download_cli)
