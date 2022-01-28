"""Parse command."""
import click

from lep_downloader import config as conf
from lep_downloader import parser
from lep_downloader.exceptions import DataBaseUnavailable
from lep_downloader.exceptions import NoEpisodeLinksError
from lep_downloader.exceptions import NoEpisodesInDataBase
from lep_downloader.exceptions import NotEpisodeURLError


@click.command(name="parse")
def cli() -> None:
    """Parses LEP archive web page."""
    click.echo("'parse' command was executed...")

    try:
        archive = parser.Archive()
        parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL, archive)
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
