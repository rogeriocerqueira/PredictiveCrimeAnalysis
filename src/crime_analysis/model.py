"""Modelos para a taxa de homicídios.

Com apenas 27 observações (capitais), um split treino/teste único é instável.
Por isso todos os modelos são avaliados com validação cruzada leave-one-out
(LOOCV) e comparados com um baseline ingênuo (média). Um modelo que não bate o
baseline não tem poder preditivo, por mais bonito que seja o R² no treino.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

TARGET = "taxa_calculada_100k"


@dataclass
class CVResult:
    modelo: str
    mae: float
    rmse: float
    r2_cv: float
    predicoes: np.ndarray

    def as_dict(self) -> dict:
        return {"modelo": self.modelo, "MAE": self.mae, "RMSE": self.rmse, "R² (LOOCV)": self.r2_cv}


def _metrics(nome: str, y: np.ndarray, pred: np.ndarray) -> CVResult:
    err = y - pred
    ss_res = float((err**2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return CVResult(
        modelo=nome,
        mae=float(np.abs(err).mean()),
        rmse=float(np.sqrt((err**2).mean())),
        r2_cv=1 - ss_res / ss_tot,
        predicoes=pred,
    )


def _fit_predict(formula: str, family: str, train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Ajusta no treino e devolve a taxa prevista por 100 mil no teste."""
    if family == "ols":
        fit = smf.ols(formula, data=train).fit()
        return np.asarray(fit.predict(test))
    fam = sm.families.Poisson() if family == "poisson" else sm.families.NegativeBinomial(alpha=_alpha(train, formula))
    fit = smf.glm(formula, data=train, family=fam, offset=np.log(train["populacao"] / 1e5)).fit()
    # Prevê contagem por 100 mil habitantes (offset = 0)
    return np.asarray(fit.predict(test, offset=np.zeros(len(test))))


def _alpha(train: pd.DataFrame, formula: str) -> float:
    """Estima a sobredispersão (alpha) da binomial negativa via método dos momentos sobre um Poisson."""
    pois = smf.glm(formula, data=train, family=sm.families.Poisson(), offset=np.log(train["populacao"] / 1e5)).fit()
    mu = pois.mu
    y = train["homicidios_estimados"].to_numpy()
    alpha = (((y - mu) ** 2 - y) / mu**2).mean()
    return float(max(alpha, 1e-6))


MODELOS = {
    # nome: (fórmula, família)
    "OLS: taxa ~ log(pop)": (f"{TARGET} ~ log_populacao", "ols"),
    "OLS: taxa ~ log(pop) + região": (f"{TARGET} ~ log_populacao + C(regiao)", "ols"),
    "Bin. Negativa: homicídios ~ log(pop) + região": ("homicidios_estimados ~ log_populacao + C(regiao)", "negbin"),
}


def loocv(df: pd.DataFrame, nome: str) -> CVResult:
    """Avalia um modelo (ou 'Baseline (média)') por leave-one-out."""
    y = df[TARGET].to_numpy()
    preds = np.empty(len(df))
    for i in range(len(df)):
        train = df.drop(index=df.index[i])
        test = df.iloc[[i]]
        if nome == "Baseline (média)":
            preds[i] = train[TARGET].mean()
        else:
            formula, family = MODELOS[nome]
            preds[i] = _fit_predict(formula, family, train, test)[0]
    return _metrics(nome, y, preds)


def compare_models(df: pd.DataFrame) -> pd.DataFrame:
    df = df.reset_index(drop=True)
    resultados = [loocv(df, "Baseline (média)")] + [loocv(df, n) for n in MODELOS]
    return pd.DataFrame([r.as_dict() for r in resultados]).set_index("modelo").round(3)


def fit_full(df: pd.DataFrame, nome: str):
    """Ajusta um modelo em todos os dados (para interpretar coeficientes)."""
    formula, family = MODELOS[nome]
    if family == "ols":
        return smf.ols(formula, data=df).fit()
    fam = sm.families.NegativeBinomial(alpha=_alpha(df, formula))
    return smf.glm(formula, data=df, family=fam, offset=np.log(df["populacao"] / 1e5)).fit()
