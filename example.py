import logging

from sui.scrap import scrap

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger("SUI_scrapper")
logger.setLevel(logging.INFO)


def main():
    query = {
        "periodo_ini": {"año": 2017, "mes": 9},
        "periodo_fin": {"año": 2018, "mes": 2},
        "valores": [
            "Consumo",
            "Valor Consumo",
            "Total Facturado",
            "Factura Promedio",
            "Consumo Promedio",
            "Suscriptores",
            "Tarifa Media",
        ],
        "ubicaciones": [
            "Rural",
            "Urbano",
            "Centro Poblado",
            #         "Total",
        ],
    }

    for data, specs in scrap(query, output_type="pandas"):
        print(specs)
        print(data.head(5))

    return None


if __name__ == "__main__":
    main()
