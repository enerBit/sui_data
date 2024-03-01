import logging

import rich.logging
import typer

import sui.cli.download as download

logger = logging.getLogger("asic")
logger.addHandler(rich.logging.RichHandler())

cli = typer.Typer(no_args_is_help=True)

cli.add_typer(
    download.app,
    name="download",
)


@cli.callback()
def main(
    ctx: typer.Context,
    verbosity: int = typer.Option(0, "--verbosity", "-v", count=True),
    tidy: bool = typer.Option(default=True, envvar="SUI_TIDY"),
):
    logger.info(f"Verbosity level {verbosity}")
    match verbosity:
        case 0:
            logger.setLevel(logging.ERROR)
        case 1:
            logger.setLevel(logging.WARNING)
        case 2:
            logger.setLevel(logging.INFO)
        case 3:
            logger.setLevel(logging.DEBUG)
        case _:
            logger.setLevel(logging.DEBUG)

    ctx.meta["SUI_TIDY"] = tidy
