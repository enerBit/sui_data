import io

import pydantic


class TC1TidyRecord(pydantic.BaseModel):
    id_mercado: str
    niu: str
    mes: int
    año: int


def tidy_tc1(content: io.StringIO, sep: str = "-"):
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
    import pathlib

    with open(pathlib.Path("data/info")) as file:
        content = file.read()

    records = tidy_tc1(content)
    for record in records:
        print(record)
