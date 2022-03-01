"""Shared objects for CLI commands."""
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
import functools
import importlib
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Callable
from typing import List

import click
from click import Context
from click import Parameter

from lep_downloader import config as conf


plugin_folder = Path(
    Path(__file__).resolve().parent,
    "commands",
)
package_name = __package__

LepInt: click.IntRange = click.IntRange(0, 9999, clamp=True)


class MyCLI(click.MultiCommand):
    """Custom click multi command.

    To support  commands being loaded "lazily" from plugin folder.
    """

    def list_commands(self, ctx: click.Context) -> List[str]:
        """Returns list of commands in plugin_folder."""
        command_names = []
        for filepath in list(plugin_folder.iterdir()):
            if filepath.suffix == ".py" and filepath.name != "__init__.py":
                command_names.append(filepath.name[:-3])
        command_names.sort()
        return command_names

    def get_command(self, ctx: click.Context, name: str) -> Any:
        """Evaluates code of command module."""
        try:
            cmd_module = importlib.import_module(
                f"{package_name}.{plugin_folder.stem}.{name}"
            )
        except ModuleNotFoundError:
            return
        return cmd_module.cli  # type: ignore


def common_options(f: Callable[..., Any]) -> Callable[..., Any]:
    """Add a common (shared) options to click command."""

    @click.option(
        "--episode",
        "-ep",
        type=click.UNPROCESSED,
        callback=validate_episode_number,
        default="0-9999",
        help=(
            "Episode number for downloading. "
            "To specify range of episodes use hyphen, i.e. <num>-<num>."
        ),
        metavar="<range>",
    )
    @click.option(
        "--with-pdf",
        "-pdf",
        "pdf_yes",
        is_flag=True,
        help="Tells script to download PDF of episide page as well.",
    )
    @click.option(
        "--last",
        "last_yes",
        is_flag=True,
        help=(
            "For downloading the last episode from database. "
            "Episode number and date filters (ranges) will be ignored."
        ),
    )
    @click.option(
        "-S",
        "start_date",
        type=click.UNPROCESSED,
        callback=validate_date,
        help="To specify 'START_DATE' for date range filtering. Format 'YYYY-MM-DD'",
    )
    @click.option(
        "-E",
        "end_date",
        type=click.UNPROCESSED,
        callback=validate_date,
        help="To specify 'END_DATE' for date range filtering. Format 'YYYY-MM-DD'",
    )
    @click.option(
        "--dest",
        "-d",
        type=click.Path(file_okay=False, path_type=Path),
        callback=validate_dir,
        default=Path(),
        help="Directory path (absolute or relative) to LEP files destination.",
        metavar="<path>",
    )
    @click.option(
        "--db-url",
        "-db",
        "db_url",
        default=conf.JSON_DB_URL,
        help="URL to custom JSON database file.",
        metavar="<url>",
    )
    @click.option(
        "--quiet",
        "-q",
        "quiet",
        is_flag=True,
        help=(
            "Activate quiet mode. "
            "There is no question whether to download files or not."
        ),
    )
    @click.option(
        "--debug",
        "debug",
        is_flag=True,
        help=(
            "Enable DEBUG mode for writing log file "
            "with detailed information about script execution."
        ),
    )
    @functools.wraps(f)
    def wrapper_common_options(*args, **kwargs):  # type: ignore
        return f(*args, **kwargs)

    return wrapper_common_options


def validate_episode_number(
    ctx: Context,
    param: Parameter,
    value: Any,
) -> Any:
    """Validate value of 'episode' option."""
    start, sep, end = value.partition("-")
    if start and not end and not sep:
        return LepInt(start), LepInt(start)
    elif start and not end:
        return LepInt(start), LepInt(9999)
    elif not start and end:
        return LepInt(0), LepInt(end)
    return LepInt(start), LepInt(end)


def validate_date(
    ctx: Context,
    param: Parameter,
    value: Any,
) -> Any:
    """Validate value of '-S' and '-E' (start / end date) options."""
    if not value:
        return None

    try:
        parsed_date = datetime.strptime(value, "%Y-%m-%d")
        return parsed_date
    except ValueError:
        raise click.BadParameter("date format must be 'YYYY-MM-DD'") from None


def validate_dir(ctx: Context, param: Parameter, value: Any) -> Any:
    """Check if dir is writable or not.

    Create all parent folders to target destination during path validation.
    """
    # Do NOT check permission for 'parse' command
    # if option '--with-html' was not provided
    if "html_yes" in ctx.params:
        if not ctx.params["html_yes"] and param.name == "html_dir":
            return value
    try:
        value.mkdir(parents=True, exist_ok=True)
        probe_file = value / "tmp_dest.txt"
        probe_file.write_text("Directory is writable", encoding="utf-8")
        probe_file.unlink()
        return value
    except PermissionError as ex:
        raise click.BadParameter("folder has no 'write' permission.") from ex
    except OSError as ex:
        raise click.BadParameter(ex.args[1]) from ex
