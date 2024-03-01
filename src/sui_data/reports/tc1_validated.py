import enum
import io
import logging
import zipfile
from typing import Optional

import bs4
import httpx
import pydantic

from sui_data.reports import BASE_URL, OutputFormat, SUIReport

logger = logging.getLogger(__name__)
FIXED_PARAMS = {
    "idreporte": SUIReport.tc1_validated.value,
    "integration_masterreport": SUIReport.tc1_validated.value,
}


RETAILER_MAPPING = [
    ("3372", "A.S.C INGENIERIA SOCIEDAD ANONIMA SA ESP."),
    ("1864", "AES COLOMBIA & CIA S C A E S P"),
    ("48307", "AIR-E S.A.S. E.S.P."),
    ("62371", "BIA ENERGY SAS ESP"),
    ("48305", "CARIBEMAR DE LA COSTA S.A.S. E.S.P."),
    ("536", "CELSIA COLOMBIA S.A. E.S.P."),
    ("27572", "CEMEX ENERGY SAS ESP"),
    (
        "502",
        "CENTRAL HIDROELECTRICA DE CALDAS S.A. E.S.P. BIC BENEFICIO E INTERES COLECTIVO",
    ),
    ("520", "CENTRALES ELECTRICAS DE NARIÑO S.A. E.S.P."),
    ("604", "CENTRALES ELECTRICAS DEL NORTE DE SANTANDER S.A. ESP"),
    ("41976", "COLOMBINA ENERGIA SAS ESP"),
    ("23442", "COMPAÑIA ENERGETICA DE OCCIDENTE S.A.S.E.S.P."),
    ("637", "COMPAÑÍA DE ELECTRICIDAD DE TULUÁ S.A. E.S.P."),
    ("2378", "DICELER S.A E.S.P."),
    ("2020", "DISTRIBUIDORA Y COMERCIALIZADORA DE ENERGIA ELECTRICA S.A. E.S.P."),
    ("63694", "DRUMMOND POWER SAS ESP"),
    ("524", "ELECTRIFICADORA DE SANTANDER S.A. E.S.P."),
    ("1032", "ELECTRIFICADORA DEL CAQUETA S.A. ESP"),
    ("1014", "ELECTRIFICADORA DEL HUILA S.A. E.S.P."),
    ("600", "ELECTRIFICADORA DEL META S.A. E.S.P."),
    ("599", "EMPRESA DE ENERGIA DE ARAUCA"),
    ("500", "EMPRESA DE ENERGIA DE BOYACA S.A. E.S.P. EMPRESA DE SERVICIOS PUBLICOS"),
    ("3370", "EMPRESA DE ENERGIA DE CASANARE SA ESP"),
    ("523", "EMPRESA DE ENERGIA DELQUINDIO S.A.E.S.P."),
    ("2371", "EMPRESA DE ENERGIA DEL BAJO PUTUMAYOS.A.E.S.P."),
    ("2016", "EMPRESA DE ENERGIA DEL PUTUMAYO S.A. ESP"),
    ("1846", "EMPRESA DE ENERGIA DEL VALLE DE SIBUNDOY S.A. E.S.P."),
    ("3076", "EMPRESA DE ENERGIA ELECTRICA DEL DEPARTAMENTO DEL GUAVIARE SA ESP"),
    ("2073", "EMPRESA DE ENERGÍA DE PEREIRA S.A. ESP."),
    ("694", "EMPRESA MUNICIPAL DE ENERGÍA ELÉCTRICA S.A-E.S.P"),
    ("2438", "EMPRESAS MUNICIPALES DE CALI E.I.C.EE.S.P"),
    ("564", "EMPRESAS PÚBLICAS DE MEDELLIN E.S.P."),
    ("597", "ENEL COLOMBIA S.A. E.S.P."),
    ("59850", "ENERBIT SAS ESP"),
    ("2824", "ENERCO S.A. E.S.P."),
    ("44077", "ENERMAS SAS ESP"),
    ("20437", "ENERTOTAL S.A. E.S.P."),
    ("62071", "Enel X Colombia SAS ESP"),
    ("37094", "FRANCA ENERGIA SA ESP"),
    ("25655", "FUENTES DE ENERGÍAS RENOVABLES S.A.S. ESP"),
    ("50205", "GAP ENERGY GROUP S.A.S ESP"),
    ("21600", "GENERADORA Y COMERCIALIZADORA DE ENERGIA DEL CARIBE S.A E.S.P"),
    ("25982", "GENERSA S.A.S E.S.P."),
    ("48663", "GREENYELLOW COMERCIALIZADORA SAS ESP"),
    ("480", "ISAGEN S.A. E.S.P."),
    ("25984", "ITALCOL ENERGIA S.A. ESP."),
    ("39136", "MESSER ENERGY SERVICES SAS ESP"),
    ("45298", "NEU ENERGY SAS ESP"),
    ("23330", "PROFESIONALES EN ENERGÍA S.A E.S.P"),
    ("27691", "QI ENERGY SAS ESP"),
    ("27631", "RIOPAILA ENERGÍA SAS ESP"),
    ("1737", "RUITOQUE S.A. E.S.P."),
    ("60990", "SOL & CIELO ENERGIA SAS ESP"),
    ("38315", "SOUTH32 ENERGY S.A.S. E.S.P."),
    ("26641", "SPECTRUM RENOVAVEIS SAS ESP"),
    ("2412", "TERMOPIEDRAS S.A. E.S.P."),
    ("31191", "TERPEL ENERGIA S.A.S E.S.P"),
    ("54406", "Transacciones Energeticas S.A.S Empresa de Servicios Públicos E.S.P"),
    ("2322", "VATIA S.A. E.S.P."),
    ("44956", "VOLTAJE EMPRESARIAL SAS ESP"),
]


class Ubicacion(str, enum.Enum):
    rural = 1
    urbano = 2
    centro_poblado = 3
    total = 4


class TC1ReportParams(pydantic.BaseModel, use_enum_values=True):
    """Usage report for a given period of time."""

    formatting_chosenformat: Optional[OutputFormat] = pydantic.Field(
        default=OutputFormat.html.value, serialization_alias="formatting_chosenformat"
    )

    año: int = pydantic.Field(..., serialization_alias="ele_com_133.agno")
    periodo: int = pydantic.Field(..., serialization_alias="ele_com_133.periodo")
    comercializador: str = pydantic.Field(
        ..., serialization_alias="ele_com_133.comercializador"
    )
    items: Optional[int] = pydantic.Field(default=-1, serialization_alias="sizeChooser")


def get_tc1_validated(client: httpx.Client, definition: TC1ReportParams):
    """Get the TC1 report from the SUI."""
    params = FIXED_PARAMS | definition.model_dump(by_alias=True, exclude_none=True)
    response = client.get(BASE_URL, params=params, timeout=500)
    response.raise_for_status()
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    anchor = soup.find("a", href=True)
    assert anchor is not None
    url: str = anchor.get("href")
    response = client.get(url, timeout=500)
    response.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(response.content))
    raw_data = z.read("info").decode("utf-8")
    return raw_data


class TC1TidyRecord(pydantic.BaseModel):
    id_mercado: str
    niu: str
    mes: int
    año: int


def tidy_tc1(content: str, sep: str = "-"):
    records = []
    for i, line in enumerate(content.splitlines()):
        if i == 0:
            continue
        id_mercado, niu, mes, año = line.strip().split(sep)
        records.append(
            TC1TidyRecord(
                id_mercado=id_mercado,
                niu=niu,
                mes=int(mes),
                año=int(año),
            )
        )
    return records


if __name__ == "__main__":
    params = TC1ReportParams(año=2024, periodo=1, comercializador="59850")
    with httpx.Client() as client:
        tc1_validated = get_tc1_validated(client, params)

    records = tidy_tc1(tc1_validated)
    for record in records:
        print(record)
