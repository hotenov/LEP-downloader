"""Test cases for the cli module."""
from typing import Callable
from typing import List

from click.testing import CliRunner
from click.testing import Result

from lep_downloader import cli


def test_main_succeeds(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(cli.cli)
    assert result.exit_code == 0


def test_cli_prints_version(
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints version."""
    result = run_cli_with_args(["--version"])
    assert result.exit_code == 0
    assert "lep-downloader, version 3.0.0a" in result.output


def test_cli_when_no_such_command(
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints error and exits for unknown command."""
    result = run_cli_with_args(["burn"])
    assert result.exit_code == 2
    assert "Error:" in result.output
    assert "No such command 'burn'." in result.output


def test_cli_prints_help(
    run_cli_with_args: Callable[[List[str]], Result],
) -> None:
    """It prints help text and exits."""
    result = run_cli_with_args(["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Options:" in result.output
    assert "Commands:" in result.output
