"""Download command."""
from datetime import datetime
from datetime import time
from datetime import timedelta
from datetime import timezone
from pathlib import Path
from typing import Any

import click
from click import Context
from click import Parameter

from lep_downloader import config as conf
from lep_downloader import downloader
from lep_downloader.downloader import Audio
from lep_downloader.downloader import LepFileList
from lep_downloader.downloader import PagePDF
from lep_downloader.exceptions import DataBaseUnavailable
from lep_downloader.lep import Lep
from lep_downloader.lep import LepEpisodeList


LepInt: click.IntRange = click.IntRange(0, 9999, clamp=True)


def validate_episode_number(
    ctx: Context,
    param: Parameter,
    value: Any,
) -> Any:
    """Validate value of 'episode' option."""
    # try:
    start, sep, end = value.partition("-")
    if start and not end and not sep:
        return LepInt(start), LepInt(start)
    elif start and not end:
        return LepInt(start), LepInt(9999)
    elif not start and end:
        return LepInt(0), LepInt(end)
    # elif not start and not end:
    #     raise click.BadParameter("format must be 'N-N'")
    return LepInt(start), LepInt(end)
    # except ValueError:
    #     raise click.BadParameter("format must be 'N-N'")


def validate_date(
    ctx: Context,
    param: Parameter,
    value: Any,
) -> Any:
    """Validate value of '-S' and '-E' (start / end date) options."""
    if not value:
        return None

    filter_time = time(0, 1)  # Begining of a day
    if param.name == "end_date":
        filter_time = time(23, 55)  # End of a day
    try:
        parsed_date = datetime.strptime(value, "%Y-%m-%d")
        # date_utc = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
        date_utc = datetime.combine(
            parsed_date.date(),
            filter_time,
            tzinfo=timezone(timedelta(hours=2)),
        )
        # parsed_date = parsed_date.astimezone(timezone(timedelta(hours=18)))
        # date_utc_ = date_utc.astimezone(timezone(timedelta(hours=2)))
        return date_utc
    except ValueError:
        raise click.BadParameter("date format must be 'YYYY-MM-DD'")


def validate_dir(ctx: Context, param: Parameter, value: Any) -> Any:
    """Check is dir writable or not.

    Create all parent folders to target destination.
    """
    try:
        value.mkdir(parents=True, exist_ok=True)
        probe_file = value / "tmp_dest.txt"
        probe_file.write_text("Directory is writable", encoding="utf-8")
        probe_file.unlink()
        return value
    except PermissionError:
        raise click.BadParameter("folder has no 'write' permission.")
    except OSError as ex:
        raise click.BadParameter(ex.args[1])


@click.command(name="download")
@click.option(
    "--episode",
    "-ep",
    type=click.UNPROCESSED,
    callback=validate_episode_number,
    default="0-9999",
    help="Episode number (or range of episodes) for downloading.",
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
        "For dowloading the last episode from database only. "
        "Episode number and date filters (ranges) will be ignored."
    ),
)
@click.option(
    "-S",
    "start_date",
    type=click.UNPROCESSED,
    callback=validate_date,
    # default="2007-01-01",
    help="To specify a START DATE for date range filtering. Format 'YYYY-MM-DD'",
)
@click.option(
    "-E",
    "end_date",
    type=click.UNPROCESSED,
    callback=validate_date,
    # default="2999-01-01",
    help="To specify a END DATE for date range filtering. Format 'YYYY-MM-DD'",
)
@click.option(
    "--dest",
    "-d",
    type=click.Path(file_okay=False, path_type=Path),
    callback=validate_dir,
    default=Path(),
    help="Directory path (absolute or relative) to LEP files destination.",
    metavar="<string>",
)
@click.option(
    "--db-url",
    "-db",
    "db_url",
    default=conf.JSON_DB_URL,
    help="URL to JSON database file.",
    metavar="<string>",
)
@click.option(
    "--quiet",
    "-q",
    "quiet",
    is_flag=True,
    help=(
        "Activate quiet mode. "
        + "There is no question whether to download files or not."
    ),
)
def cli(
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
    click.echo("download_cmd() was executed...")

    filtered_episodes = LepEpisodeList()
    filtered_files = LepFileList()

    try:
        downloader.use_or_get_db_episodes(db_url)
    except DataBaseUnavailable:
        click.echo("JSON database is not available now.\n" + "Try again later.")
        click.get_current_context().exit()

    if not Lep.db_episodes:  # no valid episode objects
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
