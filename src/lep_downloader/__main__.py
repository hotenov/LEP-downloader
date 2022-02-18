"""Command-line interface."""
import sys  # pragma: no cover

from lep_downloader import cli  # pragma: no cover


def main() -> None:  # pragma: no cover
    """Calls click group."""
    cli.cli(obj={})  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    if len(sys.argv) == 1:  # pragma: no cover
        cli.cli(prog_name="playlist-along", obj={})  # pragma: no cover
    else:  # pragma: no cover
        main()  # pragma: no cover
