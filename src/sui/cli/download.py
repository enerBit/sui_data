import typer

download = typer.Typer(no_args_is_help=True)


@download.command()
def billing(year: int = typer.Option(..., help="The year to download data for")):
    typer.echo(f"Downloading billing data for {year} ...")


@download.command()
def tc1(retailer: str = typer.Argument(..., help="The retailer to download data for")):
    typer.echo("Downloading tc1 data for retailer '{retailer}' ...")
