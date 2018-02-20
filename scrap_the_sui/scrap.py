import os
import io
import pandas as pd
import json
import requests

import logging

logger = logging.getLogger(__name__)


__VALID_OUTPUT_TYPES__ = ['raw', 'pandas']
__THIS_DIR__ = os.path.dirname(os.path.abspath(__file__))

# logger.info(f"Dir: {__THIS_DIR__}")

with open(os.path.join(__THIS_DIR__, 'api_constants.json')) as src:
    __API_CONSTANTS__ = json.load(src)

with open(os.path.join(__THIS_DIR__, 'default_params.json')) as src:
    __DEFAULT_PARAMS__ = json.load(src)


def month_iter(start_year, start_month, end_year, end_month, asc=True):
    """Return a generator of orderd tuples (year, month).

    """
    ym_start = 12*start_year + start_month - 1
    ym_end = 12*end_year + end_month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield (y, m+1)


def scrap(query, output_type='raw'):
    """Returns agenerator of tuples (data, specs) of data from the SUI.

    """
    if not output_type in __VALID_OUTPUT_TYPES__:
        raise ValueError(f"'output_type' mus be one of {__VALID_OUTPUT_TYPES__}")
    
    url = __API_CONSTANTS__["url"] + __API_CONSTANTS__["endpoints"]["reporte"]
    params = __DEFAULT_PARAMS__
    for variable in query["valores"]:
        params["ele_com_096.valor"] = __API_CONSTANTS__["variables"][variable]
        for año, mes in month_iter(query["periodo_ini"]["año"], query["periodo_ini"]["mes"], query["periodo_fin"]["año"], query["periodo_fin"]["mes"]):
            params["ele_com_096.agno"] = str(año)
            params["ele_com_096.periodo"] = str(mes)
            for ubicacion in query["ubicaciones"]:
                params["ele_com_096.ubic"] = __API_CONSTANTS__["ubicaciones"][ubicacion]

                spec = {
                    "Variable": variable,
                    "Ubicación": ubicacion,
                    "Periodo": f"{año:04d}-{mes:02d}"
                }
                
                logger.info(f"Preparing request of {spec['Variable']} {spec['Periodo']} {spec['ubicación']}")

                r = requests.get(url, params=params)
                logger.info(f"Request to {r.url}")

                try:
                    r.raise_for_status()
                except requests.HTTPError:
                    logger.exception(f"Request to {r.url} failed")
                    continue

                r.encoding = 'ANSI'
                text = r.text
                text = text.replace("BOGOTA, D.C.", "BOGOTA D.C.")

                logger.info(f"Preparing output as '{output_type}'")
                if output_type == 'raw':
                    res = text
                elif output_type == 'pandas':
                    res = pd.read_csv(io.StringIO(text), sep=',', encoding='ANSI', na_values='ND', error_bad_lines=False, skipfooter=4, engine='python')
                else:
                    raise NotImplementedError(f"Output type '{output_type}' not implemented")

                logger.info(f"Yielding result of {spec['valor']} {spec['periodo']} {spec['ubicación']}")
                yield res, spec
