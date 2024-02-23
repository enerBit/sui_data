import enum

import httpx
from pydantic import BaseModel, Field

from sui.reports import BASE_URL, OutputFormat, SUIReport


class Variable(str, enum.Enum):
    suscriptores = 1
    consumo = 2
    valor_consumo = 3
    factura_promedio = 4
    consumo_promedio = 5
    tarifa_media = 6
    total_facturado = 7


class Ubicacion(str, enum.Enum):
    rural = 1
    urbano = 2
    centro_poblado = 3
    total = 4


class UsageReportParams(BaseModel, use_enum_values=True):
    """Usage report for a given period of time."""

    idreporte: SUIReport = Field(SUIReport.usage.value, serialization_alias="idreporte")
    integration_masterreport: SUIReport = Field(
        SUIReport.usage.value, serialization_alias="integration_masterreport"
    )
    formatting_chosenformat: OutputFormat = "CSV"

    año: int = Field(..., serialization_alias="ele_com_096.agno")
    periodo: int = Field(..., serialization_alias="ele_com_096.periodo")
    ubic: int = Field(..., serialization_alias="ele_com_096.ubic")
    depto: str = Field("NULL_VALUE", serialization_alias="ele_com_096.depto")
    municipio: str = Field("NULL_VALUE", serialization_alias="ele_com_096.municipio")
    empresa: str = Field("NULL_VALUE", serialization_alias="ele_com_096.empresa")
    valor: Variable = "3"


def get_sdf(client: httpx.Client, params: UsageReportParams):
    """Get the usage report from the SUI."""
    params = params.model_dump(by_alias=True)
    response = client.get(BASE_URL, params=params, timeout=500)
    response.raise_for_status()
    response.encoding = "ANSI"
    text = response.text
    text = text.replace("BOGOTA, D.C.", "BOGOTA D.C.")
    return response.text


if __name__ == "__main__":
    params = UsageReportParams(
        año=2021,
        periodo=1,
        ubic=Ubicacion.total,
    )
    client = httpx.Client()
    sdf = get_sdf(client, params)
    print(sdf)
    client.close()
