"""Parse command."""
from pathlib import Path

import click
from click import Context

from lep_downloader import config as conf
from lep_downloader import parser
from lep_downloader.cli_shared import validate_dir
from lep_downloader.exceptions import DataBaseUnavailableError
from lep_downloader.exceptions import NoEpisodeLinksError
from lep_downloader.exceptions import NoEpisodesInDataBaseError
from lep_downloader.exceptions import NotEpisodeURLError
from lep_downloader.lep import LepEpisodeList
from lep_downloader.lep import LepLog


@click.command(name="parse")
@click.option(
    "--mode",
    "-m",
    "mode",
    type=click.Choice(["raw", "fetch", "pull"], case_sensitive=False),
    default="fetch",
    help=(
        "Parsing mode:\n"
        "RAW - Parse archive episodes only (ignoring database); "
        "FETCH - Parse and add new episodes "
        "(following 'after' last episode in database); "
        "PULL - Parse all episodes not present in database "
        "and merge them with previous ones in database. "
        "Default is FETCH."
    ),
)
@click.option(
    "--with-html",
    "-html",
    "html_yes",
    is_flag=True,
    help="Tells script to save episode page to local HTML file.",
)
@click.option(
    "--html-dir",
    "-hd",
    "html_dir",
    type=click.Path(file_okay=False, path_type=Path),
    callback=validate_dir,
    default=Path(conf.PATH_TO_HTML_FILES),
    help=(
        "Directory path (absolute or relative) for storing HTML files. "
        "It makes sense only if option '--with-html' is provided."
    ),
    metavar="<path>",
)
@click.option(
    "--dest",
    "-d",
    type=click.Path(file_okay=False, path_type=Path),
    callback=validate_dir,
    default=Path(),
    help="Directory path (absolute or relative) to JSON result file destination.",
    metavar="<path>",
)
@click.option(
    "--db-url",
    "-db",
    "db_url",
    default=conf.JSON_DB_URL,
    help="URL to custom JSON database file.",
    metavar="<url>",
)
@click.pass_context
def cli(
    ctx: Context,
    mode: str,
    html_yes: bool,
    html_dir: Path,
    dest: Path,
    db_url: str,
) -> None:
    """Parses LEP archive web page."""
    lep_log: LepLog = ctx.obj["log"]
    ctx.obj["parsed_episodes"] = LepEpisodeList()
    path_to_html = str(html_dir.absolute())

    try:
        archive = parser.Archive(
            mode=mode, log=lep_log, with_html=html_yes, html_path=path_to_html
        )

        lep_log.msg("<m>Starting parsing...</m>")
        archive.do_parsing_actions(db_url, str(dest))
        ctx.obj["parsed_episodes"] = archive.episodes

    except NotEpisodeURLError as ex:
        lep_log.msg("<r>{err}:</r>\n\t<c>{url}</c>", err=ex.args[1], url=ex.args[0])
        lep_log.msg("Archive page has invalid HTML content. Exit.")

    except NoEpisodeLinksError as ex:
        lep_log.msg("<r>{err}:</r>\n\t<c>{url}</c>", err=ex.args[1], url=ex.args[0])
        lep_log.msg("Can't parse any episodes. Exit.")

    except DataBaseUnavailableError:
        lep_log.msg("<r>JSON database is not available.</r> <c>Exit.</c>")

    except NoEpisodesInDataBaseError as ex:
        lep_log.msg(
            "<y>WARNING: JSON file <c>{url}</c> has no valid episode objects.</y>",
            url=db_url,
        )
        lep_log.msg("\t" + ex.args[0])

    except Exception as ex:
        lep_log.msg("<r>Oops.. Unhandled error.</r>")
        if not lep_log.debug:
            lep_log.msg("<y>\t{ex}</y>", ex=ex)
        else:
            lep_log.msg("Unhandled: {ex}", ex=ex, msg_lvl="CRITICAL")
            lep_log.msg(
                "See details in log file: <c>{logpath}</c>",
                logpath=lep_log.logfile,
            )
