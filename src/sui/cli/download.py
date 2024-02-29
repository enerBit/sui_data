import httpx
import typer

import sui.console as console
import sui.reports.billing as billing
import sui.reports.tc1_validated as tc1

app = typer.Typer(no_args_is_help=True)


@app.command(no_args_is_help=True, name="billing")
def billing_download(
    ctx: typer.Context,
    month_str: str = typer.Option(..., "--month", help="Month", metavar="YYYY-MM"),
):

    client = httpx.Client()
    year, month = month_str.split("-")

    query_def = billing.BillingReportParams(año=int(year), periodo=int(month))
    console.err_console.print(f"Downloading billing data with {query_def} ...")
    raw = billing.get(client, query_def)

    if ctx.meta["SUI_TIDY"]:
        records = billing.tidy_billing(raw)
        for record in records:
            console.out_console.print(record)
    else:
        console.out_console.print(raw)


@app.command(no_args_is_help=True, name="tc1")
def tc1_download(
    ctx: typer.Context,
    month_str: str = typer.Option(..., "--month", help="Month", metavar="YYYY-MM"),
    retailer: str = typer.Argument(..., help="The retailer to download data for"),
):
    year, month = month_str.split("-")
    client = httpx.Client()
    query_def = tc1.TC1ReportParams(
        año=int(year), periodo=int(month), comercializador=retailer
    )
    console.err_console.print(f"Downloading tc1 data with {query_def} ...")
    raw = tc1.get_tc1_validated(client, query_def)
    if ctx.meta["SUI_TIDY"]:
        records = tc1.tidy_tc1(raw)
        for record in records:
            console.out_console.print(record)
    else:
        console.out_console.print(raw)
