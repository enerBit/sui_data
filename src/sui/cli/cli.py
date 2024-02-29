import typer

from .download import download

cli = typer.Typer(no_args_is_help=True)


cli.add_typer(download, name="download")
