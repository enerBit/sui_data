import enum
import logging
import re
from typing import Optional

import httpx
import pandas as pd
import pydantic

from sui.reports import BASE_URL, OutputFormat, SUIReport

TAIL_METADATA_LENGTH = 1_000
METADA_SEPARATOR_PATTERN = re.compile(r",{14,16}")

logger = logging.getLogger(__name__)
FIXED_PARAMS = {
    "idreporte": SUIReport.billing.value,
    "integration_masterreport": SUIReport.billing.value,
}


class Reporte(int, enum.Enum):
    suscriptores = 1
    consumo = 2
    valor_consumo = 3
    factura_promedio = 4
    consumo_promedio = 5
    tarifa_media = 6
    total_facturado = 7


class Variable(str, enum.Enum):
    suscriptores = "usuarios Empresa Departamento y Municipio"
    consumo = "Consumos Empresa Departamento y Municipio"
    valor_consumo = "Valor Consumo Empresa Departamento y Municipio"
    factura_promedio = "factura promedio Empresa Departamento y Municipio"
    consumo_promedio = "consumo promedio Empresa Departamento y Municipio"
    tarifa_media = "tarifa media Empresa Departamento y Municipio"
    total_facturado = "Total Facturado Empresa Departamento y Municipio"


class Ubicacion(int, enum.Enum):
    rural = 1
    urbano = 2
    centro_poblado = 3
    total = 4


class BillingReportParams(pydantic.BaseModel, use_enum_values=True):

    año: int = pydantic.Field(..., serialization_alias="ele_com_096.agno")
    periodo: int = pydantic.Field(..., serialization_alias="ele_com_096.periodo")
    reporte: Optional[Reporte] = pydantic.Field(
        default=None, serialization_alias="ele_com_096.valor"
    )
    ubicación: Optional[Ubicacion] = pydantic.Field(
        default=Ubicacion.total.value, serialization_alias="ele_com_096.ubic"
    )
    formatting_chosenformat: Optional[OutputFormat] = pydantic.Field(
        default=OutputFormat.csv.value, serialization_alias="formatting_chosenformat"
    )

    depto: Optional[str] = pydantic.Field(
        default="NULL_VALUE",
        serialization_alias="ele_com_096.depto",
    )
    municipio: Optional[str] = pydantic.Field(
        default="NULL_VALUE", serialization_alias="ele_com_096.municipio"
    )
    empresa: Optional[str] = pydantic.Field(
        default="NULL_VALUE", serialization_alias="ele_com_096.empresa"
    )


def get(client: httpx.Client, definition: BillingReportParams):
    """Get the billing report from the SUI."""
    params = FIXED_PARAMS | definition.model_dump(by_alias=True, exclude_none=True)
    logger.debug(f"Getting billing report with params: {params}")
    response = client.get(BASE_URL, params=params, timeout=500)
    response.raise_for_status()
    response.encoding = "ANSI"
    return response.text


def float_or_none(value):
    return None if value in ["ND", ""] else float(value)


class BillingRawRecord(pydantic.BaseModel):
    año: int
    período: int
    departamento: str
    municipio: str
    empresa: str
    variable: Variable
    estrato_1: float | None
    estrato_2: float | None
    estrato_3: float | None
    estrato_4: float | None
    estrato_5: float | None
    estrato_6: float | None
    total_residencial: float | None
    industrial: float | None
    comercial: float | None
    oficial: float | None
    otros: float | None
    total_no_residencial: float | None


class Metadata(pydantic.BaseModel):
    año: int
    período: int
    ubicación: str | None = None
    reporte_a_consultar: str | None = None


class TipoActividad(str, enum.Enum):
    residencial = "residencial"
    no_residencial = "no_residencial"


class ActividadResidencial(str, enum.Enum):
    estrato_1 = "estrato_1"
    estrato_2 = "estrato_2"
    estrato_3 = "estrato_3"
    estrato_4 = "estrato_4"
    estrato_5 = "estrato_5"
    estrato_6 = "estrato_6"


class ActividadNoResidencial(str, enum.Enum):
    industrial = "industrial"
    comercial = "comercial"
    oficial = "oficial"
    otros = "otros"


RESIDENTIAL_ACTIVITIES = [a.value for a in ActividadResidencial]
NON_RESIDENTIAL_ACTIVITIES = [a.value for a in ActividadNoResidencial]


class UsageTidyRecord(pydantic.BaseModel, use_enum_values=True):
    año: int
    período: int
    departamento: str
    municipio: str
    empresa: str
    tipo_actividad: TipoActividad
    actividad: ActividadResidencial | ActividadNoResidencial
    suscriptores: Optional[float] = pydantic.Field(default=None)
    consumo: Optional[float] = pydantic.Field(default=None)
    valor_consumo: Optional[float] = pydantic.Field(default=None)
    factura_promedio: Optional[float] = pydantic.Field(default=None)
    consumo_promedio: Optional[float] = pydantic.Field(default=None)
    tarifa_media: Optional[float] = pydantic.Field(default=None)
    total_facturado: Optional[float] = pydantic.Field(default=None)


def split_content(content: str) -> tuple[str, str]:
    tail = content[-TAIL_METADATA_LENGTH:]
    match = METADA_SEPARATOR_PATTERN.search(tail)
    if match is not None:
        start = TAIL_METADATA_LENGTH - match.start()
        end = TAIL_METADATA_LENGTH - match.end() - 1
    else:
        raise ValueError("Metadata separator not found")
    data_content = content[:-start]
    metadata_content = content[-end:]

    return data_content, metadata_content


def parse_metadata(metadata_content: str) -> Metadata:
    temp_dict = {}
    for line in metadata_content.splitlines():
        key, value = line.split(",")
        temp_dict[key.lower()] = value if value != "" else None

    metadata = Metadata.model_validate(temp_dict)
    return metadata


def fix_bad_fields(content: str) -> str:
    return content.replace("BOGOTÁ, D.C.", "BOGOTÁ D.C.").replace(
        "BOGOTA, D.C.", "BOGOTÁ D.C."
    )


def billing_to_raw_dataframe(content: str, metadata: Metadata, sep: str = ","):
    records = []
    for i, line in enumerate(content.splitlines()):
        if i == 0:
            continue
        (
            departamento,
            municipio,
            empresa,
            variable_value,
            estrato_1,
            estrato_2,
            estrato_3,
            estrato_4,
            estrato_5,
            estrato_6,
            total_residencial,
            industrial,
            comercial,
            oficial,
            otros,
            total_no_residencial,
        ) = line.strip().split(sep)

        records.append(
            BillingRawRecord(
                año=metadata.año,
                período=metadata.período,
                departamento=departamento,
                municipio=municipio,
                empresa=empresa,
                variable=Variable(variable_value),
                estrato_1=float_or_none(estrato_1),
                estrato_2=float_or_none(estrato_2),
                estrato_3=float_or_none(estrato_3),
                estrato_4=float_or_none(estrato_4),
                estrato_5=float_or_none(estrato_5),
                estrato_6=float_or_none(estrato_6),
                total_residencial=float_or_none(total_residencial),
                industrial=float_or_none(industrial),
                comercial=float_or_none(comercial),
                oficial=float_or_none(oficial),
                otros=float_or_none(otros),
                total_no_residencial=float_or_none(total_no_residencial),
            )
        )
    df = pd.DataFrame([record.model_dump() for record in records])
    return df


def raw_to_tidy_dataframe(df: pd.DataFrame):
    index_cols = [
        "año",
        "período",
        "departamento",
        "municipio",
        "empresa",
        # "variable",
    ]
    activity_cols = RESIDENTIAL_ACTIVITIES + NON_RESIDENTIAL_ACTIVITIES
    dfs = []
    for key, group in df.groupby(by=["variable"]):
        df = group.melt(
            id_vars=index_cols,
            value_vars=activity_cols,
            var_name="actividad",
            value_name=key[0].name,
        ).dropna()
        dfs.append(df)
    df = multimerge(dfs, on=index_cols + ["actividad"])
    df["tipo_actividad"] = df["actividad"].map(tipo_actividad)
    df = (
        df.set_index(index_cols + ["tipo_actividad", "actividad"])
        .sort_index()
        .reset_index()
    )
    return df


def tidy_billing(content: str, sep: str = ","):
    content = fix_bad_fields(content)

    content, metadata_content = split_content(content)
    metadata = parse_metadata(metadata_content)

    df = billing_to_raw_dataframe(content=content, metadata=metadata, sep=sep)

    df = raw_to_tidy_dataframe(df)
    records = df.to_dict(orient="records", index=True)
    records = [UsageTidyRecord.model_validate(record) for record in records]
    return records


def multimerge(dfs: list[pd.DataFrame], on):
    total = dfs[0]
    for df in dfs[1:]:
        total = total.merge(df, how="outer", on=on)
    return total


def tipo_actividad(actividad: str):
    if actividad in RESIDENTIAL_ACTIVITIES:
        return TipoActividad.residencial
    elif actividad in NON_RESIDENTIAL_ACTIVITIES:
        return TipoActividad.no_residencial
    else:
        raise ValueError("Invalid activity")


if __name__ == "__main__":
    reports = []
    # for variable in Variable:
    #     print(variable)
    params = BillingReportParams(
        año=2023,
        periodo=12,
        ubicación=Ubicacion.total,
        # reporte=Reporte[Variable.consumo.name],
    )
    with httpx.Client() as client:
        billing_report = get(client, params)

    records = tidy_billing(billing_report)
    for record in records:
        print(record)
