"""CLI main click group."""
import importlib
from pathlib import Path
from typing import Any
from typing import List

import click

from lep_downloader import __version__


plugin_folder = Path(
    Path(__file__).resolve().parent,
    "commands",
)
package_name = __package__


class MyCLI(click.MultiCommand):
    """Custom click multi command.

    To support  commands being loaded "lazily" from plugin folder.
    """

    def list_commands(self, ctx: click.Context) -> List[str]:
        """Returns list of commands in plugin_folder."""
        command_names = []
        for filepath in list(plugin_folder.iterdir()):
            if filepath.suffix == ".py" and filepath.name != "__init__.py":
                command_names.append(filepath.name[:-3])
        command_names.sort()
        return command_names

    def get_command(self, ctx: click.Context, name: str) -> Any:
        """Evaluates code of command module."""
        try:
            cmd_module = importlib.import_module(
                f"{package_name}.{plugin_folder.stem}.{name}"
            )
        except ModuleNotFoundError:
            return
        return cmd_module.cli  # type: ignore


@click.command(
    cls=MyCLI,
    invoke_without_command=True,
)
@click.version_option(version=__version__)
def cli() -> None:
    """LEP-downloader - console application.

    Get free episodes of Luke's English Podcast archive page.
    """
    click.echo(f"cli() in '{Path(__file__).name}' was executed...")
