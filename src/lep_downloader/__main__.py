"""Command-line interface."""
import click

from lep_downloader import __version__


@click.command()
@click.version_option(version=__version__)
def main() -> None:
    """LEP Downloader."""


if __name__ == "__main__":
    main(prog_name="lep-downloader")  # pragma: no cover
