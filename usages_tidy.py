import enum

import pandas as pd
import pydantic


def value_or_none(value):
    return None if value in ["ND", ""] else float(value)


class UsageRawRecord(pydantic.BaseModel):
    departamento: str
    municipio: str
    empresa: str
    variable: str
    estrato_1: int | None
    estrato_2: int | None
    estrato_3: int | None
    estrato_4: int | None
    estrato_5: int | None
    estrato_6: int | None
    total_residencial: int | None
    industrial: int | None
    comercial: int | None
    oficial: int | None
    otros: int | None
    total_no_residencial: int | None


class Metadata(pydantic.BaseModel):
    año: int
    periodo: int
    ubicacion: str
    reporte_a_consultar: str


class Variable(str, enum.Enum):
    suscriptores = 1
    consumo = 2
    valor_consumo = 3
    factura_promedio = 4
    consumo_promedio = 5
    tarifa_media = 6
    total_facturado = 7


class Actividad(str, enum.Enum):
    estrato_1 = "estrato_1"
    estrato_2 = "estrato_2"
    estrato_3 = "estrato_3"
    estrato_4 = "estrato_4"
    estrato_5 = "estrato_5"
    estrato_6 = "estrato_6"
    industrial = "industrial"
    comercial = "comercial"
    oficial = "oficial"
    otros = "otros"


class UsageTidyRecord(pydantic.BaseModel, use_enum_values=True):
    año: int
    mes: int
    departamento: str
    municipio: str
    empresa: str
    actividad: Actividad
    variable: str
    valor: int


def tidy_usages(content: str, year: int, month: int, sep: str = ","):
    content = content.replace("BOGOTÁ, D.C.", "BOGOTÁ D.C.").replace(
        "BOGOTA, D.C.", "BOGOTÁ D.C."
    )
    content_lines = content.splitlines()
    content_lines, metadata = content_lines[:-5], content_lines[-4:]
    metadata = Metadata(
        año=int(metadata[0].split(",")[1].strip()),
        periodo=int(metadata[1].split(",")[1].strip()),
        ubicacion=metadata[2].split(",")[1].strip(),
        reporte_a_consultar=metadata[3].split(",")[1].strip(),
    )

    records = []
    for i, line in enumerate(content_lines):
        if i == 0:
            continue
        (
            departamento,
            municipio,
            empresa,
            variable,
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
            UsageRawRecord(
                año=year,
                mes=month,
                departamento=departamento,
                municipio=municipio,
                empresa=empresa,
                variable=variable,
                estrato_1=value_or_none(estrato_1),
                estrato_2=value_or_none(estrato_2),
                estrato_3=value_or_none(estrato_3),
                estrato_4=value_or_none(estrato_4),
                estrato_5=value_or_none(estrato_5),
                estrato_6=value_or_none(estrato_6),
                total_residencial=value_or_none(total_residencial),
                industrial=value_or_none(industrial),
                comercial=value_or_none(comercial),
                oficial=value_or_none(oficial),
                otros=value_or_none(otros),
                total_no_residencial=value_or_none(total_no_residencial),
            )
        )
    df = pd.DataFrame([record.model_dump() for record in records])
    df["año"] = metadata.año
    df["mes"] = metadata.periodo

    index_cols = ["año", "mes", "departamento", "municipio", "empresa", "variable"]
    activity_cols = [a.value for a in Actividad]

    df = df.melt(
        id_vars=index_cols,
        value_vars=activity_cols,
        var_name="actividad",
        value_name="valor",
    ).dropna()
    records = df.to_dict(orient="records")
    records = [UsageTidyRecord.model_validate(record) for record in records]

    return records


if __name__ == "__main__":
    import pathlib

    with open(pathlib.Path("data/reporte.csv"), encoding="cp1252") as file:
        content = file.read()

    records = tidy_usages(content, 2024, 1)
    for record in records:
        print(record)
