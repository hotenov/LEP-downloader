"""CLI main click group."""
import click

from lep_downloader import __version__
from lep_downloader.commands import download
from lep_downloader.commands import parse


@click.group(
    invoke_without_command=True,
    # no_args_is_help=True,
)
@click.version_option(version=__version__)
@click.pass_context
def cli_main(ctx: click.Context) -> None:
    """LEP-downloader - parse and download with your console.

    Free episodes of Luke's English Podcast archive page.
    """
    click.echo("cli_main() was executed...")


cli_main.add_command(parse.parse_cmd)
cli_main.add_command(download.download_cmd)
