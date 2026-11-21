"""Carga, limpeza e validação dos dados de homicídios.

O fluxo é: CSV bruto -> renomeia colunas -> valida -> cria variáveis derivadas
-> CSV processado. Nada é corrigido silenciosamente: inconsistências na fonte
ficam marcadas em colunas próprias e no relatório de validação.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import config


@dataclass
class ValidationReport:
    n_linhas: int = 0
    erros: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.erros

    def to_markdown(self) -> str:
        linhas = [
            "# Relatório de validação dos dados",
            "",
            f"Linhas analisadas: **{self.n_linhas}**",
            "",
            f"## Erros ({len(self.erros)})",
            "",
        ]
        linhas += [f"- {e}" for e in self.erros] or ["Nenhum."]
        linhas += ["", f"## Avisos ({len(self.avisos)})", ""]
        linhas += [f"- {a}" for a in self.avisos] or ["Nenhum."]
        return "\n".join(linhas) + "\n"


def load_raw(path: Path | str = config.RAW_FILE) -> pd.DataFrame:
    """Lê o CSV bruto e padroniza os nomes das colunas."""
    df = pd.read_csv(path, encoding="utf-8")
    faltando = set(config.COLUMN_MAP) - set(df.columns)
    if faltando:
        raise ValueError(f"Colunas ausentes no arquivo bruto: {sorted(faltando)}")
    return df.rename(columns=config.COLUMN_MAP)[list(config.COLUMN_MAP.values())]


def validate(df: pd.DataFrame, tolerancia: float = config.TOLERANCIA_TAXA) -> ValidationReport:
    """Verifica integridade e coerência interna. Espera colunas já padronizadas."""
    rep = ValidationReport(n_linhas=len(df))

    nulos = df.isna().sum()
    for col, n in nulos[nulos > 0].items():
        rep.erros.append(f"Coluna `{col}` tem {n} valor(es) nulo(s).")

    dup = df[df.duplicated(["municipio", "uf"], keep=False)]
    if not dup.empty:
        rep.erros.append(f"Municípios duplicados: {sorted(set(dup['municipio']))}")

    regioes_invalidas = set(df["regiao"]) - config.REGIOES_VALIDAS
    if regioes_invalidas:
        rep.erros.append(f"Regiões inválidas: {sorted(regioes_invalidas)}")

    numericas = ["populacao", "homicidios_registrados", "homicidios_ocultos", "homicidios_estimados"]
    for col in numericas:
        neg = df[df[col] < 0]
        if not neg.empty:
            rep.erros.append(f"`{col}` negativo em: {list(neg['municipio'])}")

    soma_errada = df[df["homicidios_registrados"] + df["homicidios_ocultos"] != df["homicidios_estimados"]]
    for _, r in soma_errada.iterrows():
        rep.erros.append(f"{r['municipio']}: registrados + ocultos != estimados.")

    taxa_calc = df["homicidios_estimados"] / df["populacao"] * 1e5
    diff = df["taxa_informada_100k"] - taxa_calc
    for (_, r), tc, d in zip(df.iterrows(), taxa_calc, diff):
        if abs(d) > tolerancia:
            rep.avisos.append(
                f"{r['municipio']}/{r['uf']}: taxa informada {r['taxa_informada_100k']:.1f} "
                f"≠ calculada {tc:.1f} (diferença {d:+.1f}). Conferir na fonte original."
            )

    # Outliers por IQR na taxa recalculada: não é erro, mas merece revisão.
    q1, q3 = taxa_calc.quantile([0.25, 0.75])
    iqr = q3 - q1
    for (_, r), tc in zip(df.iterrows(), taxa_calc):
        if tc < q1 - 1.5 * iqr or tc > q3 + 1.5 * iqr:
            rep.avisos.append(
                f"{r['municipio']}/{r['uf']}: taxa {tc:.1f} é outlier (IQR). "
                f"Verificar se o número de homicídios ({r['homicidios_estimados']}) está correto."
            )
    return rep


def clean(df: pd.DataFrame, tolerancia: float = config.TOLERANCIA_TAXA) -> pd.DataFrame:
    """Cria variáveis derivadas. Mantém a taxa original e a recalculada lado a lado."""
    out = df.copy()
    out["municipio"] = out["municipio"].str.strip()
    out["uf"] = out["uf"].str.strip().str.upper()
    out["regiao"] = out["regiao"].str.strip().str.upper()

    out["taxa_calculada_100k"] = (out["homicidios_estimados"] / out["populacao"] * 1e5).round(2)
    out["taxa_inconsistente"] = (out["taxa_informada_100k"] - out["taxa_calculada_100k"]).abs() > tolerancia
    out["pct_ocultos"] = (out["homicidios_ocultos"] / out["homicidios_estimados"] * 100).round(2)
    out["log_populacao"] = np.log(out["populacao"]).round(4)

    return out.sort_values("taxa_calculada_100k", ascending=False).reset_index(drop=True)


def run_pipeline(
    raw_path: Path | str = config.RAW_FILE,
    out_path: Path | str = config.PROCESSED_FILE,
    report_path: Path | str = config.VALIDATION_REPORT,
) -> tuple[pd.DataFrame, ValidationReport]:
    """Executa bruto -> processado e grava CSV e relatório. Falha se houver erros."""
    raw = load_raw(raw_path)
    rep = validate(raw)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(rep.to_markdown(), encoding="utf-8")
    if not rep.ok:
        raise ValueError("Validação falhou:\n" + "\n".join(rep.erros))
    df = clean(raw)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8")
    return df, rep


def load_processed(path: Path | str = config.PROCESSED_FILE) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8")
