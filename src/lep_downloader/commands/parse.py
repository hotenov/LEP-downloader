"""Parse command."""
from pathlib import Path

import click

from lep_downloader import config as conf
from lep_downloader import parser
from lep_downloader.cli_shared import validate_dir
from lep_downloader.exceptions import DataBaseUnavailable
from lep_downloader.exceptions import NoEpisodeLinksError
from lep_downloader.exceptions import NoEpisodesInDataBase
from lep_downloader.exceptions import NotEpisodeURLError


@click.command(name="parse")
@click.option(
    "--with-html",
    "-html",
    "html_yes",
    is_flag=True,
    help="Tells script to save episode page to local HTML file.",
)
@click.option(
    "--html-dir",
    "-hd",
    "html_dir",
    type=click.Path(file_okay=False, path_type=Path),
    callback=validate_dir,
    default=Path(conf.PATH_TO_HTML_FILES),
    help=(
        "Directory path (absolute or relative) for storing HTML files. "
        "It makes sense only if option '--with-html' is provided."
    ),
    metavar="<string>",
)
def cli(
    html_yes: bool,
    html_dir: Path,
) -> None:
    """Parses LEP archive web page."""
    if html_yes:
        conf.WITH_HTML = True
        conf.PATH_TO_HTML_FILES = str(html_dir.absolute())

    try:
        archive = parser.Archive()
        archive.do_parsing_actions(conf.JSON_DB_URL)
    except NotEpisodeURLError as ex:
        click.echo(f"{ex.args[1]}:\n\t{ex.args[0]}")
        click.echo("Archive page has invalid HTML content. Exit.")
    except NoEpisodeLinksError as ex:
        click.echo(f"{ex.args[1]}:\n\t{ex.args[0]}")
        click.echo("Can't parse any episodes. Exit.")
    except DataBaseUnavailable:
        click.echo("JSON database is not available. Exit.")
    except NoEpisodesInDataBase as ex:
        click.echo(
            f"[WARNING]: JSON file ({conf.JSON_DB_URL}) has no valid episode objects."
        )
        click.echo("\t" + ex.args[0])
