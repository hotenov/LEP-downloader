"""Download command."""
import click


@click.command(name="download")
def cli() -> None:
    """Downloads LEP episodes on disk."""
    click.echo("download_cmd() was executed...")
