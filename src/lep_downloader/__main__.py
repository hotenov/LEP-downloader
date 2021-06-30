"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """LEP Downloader."""


if __name__ == "__main__":
    main(prog_name="lep-downloader")  # pragma: no cover
