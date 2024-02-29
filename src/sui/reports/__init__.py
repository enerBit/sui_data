import enum

BASE_URL = "http://reportes.sui.gov.co/fabricaReportes/reporte"


class SUIReport(str, enum.Enum):
    billing = "ele_com_096"
    tc1_validated = "ele_com_133"


class OutputFormat(str, enum.Enum):
    csv = "CSV"
    excel = "EXCEL"
    raw = "RAW"
    html = "HTML"
