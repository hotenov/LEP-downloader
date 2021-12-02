"""Parse command."""
import click

from lep_downloader import config as conf
from lep_downloader import parser


@click.command(name="parse")
def cli() -> None:
    """Parses LEP archive web page."""
    click.echo("'parse' command was executed...")

    parser.do_parsing_actions(conf.JSON_DB_URL, conf.ARCHIVE_URL)
