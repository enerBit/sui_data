import datetime as dt

import httpx
import typer

import sui_data.console as console
import sui_data.reports.billing as billing
import sui_data.reports.tc1_validated as tc1

YEAR_MONTH_FORMATS = ["%Y-%m", "%Y%m"]
YEAR_MONTH_MATCH_ERROR_MESSAGE = f"Must match one of: {YEAR_MONTH_FORMATS}"


def validate_month(month: str) -> str:
    for f in YEAR_MONTH_FORMATS:
        try:
            dt.datetime.strptime(month, f).date()
            break
        except ValueError:
            continue
    else:
        raise typer.BadParameter(YEAR_MONTH_MATCH_ERROR_MESSAGE)

    return month


def parse_month(month: str) -> dt.date:
    for f in YEAR_MONTH_FORMATS:
        try:
            value = dt.datetime.strptime(month, f).date()
            break
        except ValueError:
            continue
    else:
        raise ValueError(f"Failed to parse {month} as date")

    return value


def months_callback(values: list[str]) -> list[str]:
    months = sorted(list(set([validate_month(v) for v in values])), reverse=True)
    return months


app = typer.Typer(no_args_is_help=True)


@app.command(no_args_is_help=True, name="billing")
def billing_download(
    ctx: typer.Context,
    months: list[str] = typer.Option(
        ...,
        "--month",
        callback=months_callback,
        help=YEAR_MONTH_MATCH_ERROR_MESSAGE,
    ),
):

    client = httpx.Client()

    for month in months:
        date = parse_month(month)
        query_def = billing.BillingReportParams(año=date.year, periodo=date.month)
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
    months: list[str] = typer.Option(
        ...,
        "--month",
        callback=months_callback,
        help=YEAR_MONTH_MATCH_ERROR_MESSAGE,
    ),
    retailer: str = typer.Argument(..., help="The retailer to download data for"),
):

    client = httpx.Client()

    for month in months:
        date = parse_month(month)

        query_def = tc1.TC1ReportParams(
            año=date.year, periodo=date.month, comercializador=retailer
        )
        console.err_console.print(f"Downloading tc1 data with {query_def} ...")
        raw = tc1.get_tc1_validated(client, query_def)
        if ctx.meta["SUI_TIDY"]:
            records = tc1.tidy_tc1(raw)
            for record in records:
                console.out_console.print(record)
        else:
            console.out_console.print(raw)
