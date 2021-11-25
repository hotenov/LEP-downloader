"""Parse command."""
import click


@click.command(name="parse")
def parse_cmd() -> None:
    """Parses LEP archive web page."""
    click.echo("parse_cmd() was executed...")
