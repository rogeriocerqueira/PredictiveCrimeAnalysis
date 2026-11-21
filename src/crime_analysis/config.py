"""Caminhos e constantes do projeto, centralizados para evitar caminhos relativos frágeis."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"

RAW_FILE = RAW_DIR / "raw_homicidios.csv"
PROCESSED_FILE = PROCESSED_DIR / "processed_homicidios_cleaned.csv"
VALIDATION_REPORT = REPORTS_DIR / "validacao_dados.md"

# Mapeamento: coluna original -> nome padronizado (snake_case, sem acentos)
COLUMN_MAP = {
    "Município": "municipio",
    "UF": "uf",
    "Região": "regiao",
    "População (2022)": "populacao",
    "Homicídios registrados (A)": "homicidios_registrados",
    "Homicídios ocultos (B)": "homicidios_ocultos",
    "Homicídios estimados (A+B)": "homicidios_estimados",
    "Taxa de homicídios estimados por 100 mil habitantes": "taxa_informada_100k",
}

REGIOES_VALIDAS = {"N", "NE", "CO", "SE", "S"}

# Diferença máxima aceitável (pontos por 100 mil) entre a taxa informada
# e a recalculada; acima disso a linha é marcada como inconsistente.
TOLERANCIA_TAXA = 0.5
