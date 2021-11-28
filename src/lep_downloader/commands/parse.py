"""Parse command."""
import click


@click.command(name="parse")
def cli() -> None:
    """Parses LEP archive web page."""
    click.echo("parse_cmd() was executed...")
