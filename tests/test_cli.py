"""Test cases for the cli module."""
from click.testing import CliRunner

from lep_downloader import cli


def test_main_succeeds(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(cli.cli_main)
    assert result.exit_code == 0


def test_cli_prints_version(runner: CliRunner) -> None:
    """It prints version."""
    result = runner.invoke(
        cli.cli_main,
        ["--version"],
        prog_name="lep-downloader",
    )
    assert result.exit_code == 0
    assert "lep-downloader, version 3.0.0a" in result.output
