"""Gera as figuras e GIFs usados no README (`python -m crime_analysis figures`).

Tudo sai de `data/processed`, então basta rodar de novo após corrigir os dados.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402

from . import config  # noqa: E402
from .data import load_processed  # noqa: E402
from .model import compare_models, loocv  # noqa: E402

FIG_DIR = config.PROJECT_ROOT / "docs" / "img"

CORES = {"N": "#2a9d8f", "NE": "#e76f51", "CO": "#e9c46a", "SE": "#264653", "S": "#8ab17d"}
NOMES = {"N": "Norte", "NE": "Nordeste", "CO": "Centro-Oeste", "SE": "Sudeste", "S": "Sul"}
TEXTO = "#222222"
CINZA = "#8a8a8a"

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#cccccc",
    "axes.labelcolor": TEXTO,
    "axes.titleweight": "bold",
    "axes.titlesize": 14,
    "axes.titlelocation": "left",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": "#ececec",
    "xtick.color": TEXTO,
    "ytick.color": TEXTO,
    "font.size": 11,
})


def _legenda_regioes(ax, loc="lower right"):
    handles = [plt.Line2D([], [], marker="s", ls="", color=c, markersize=10) for c in CORES.values()]
    ax.legend(handles, [NOMES[k] for k in CORES], loc=loc, frameon=False, title="Região")


def _subtitulo(fig, texto):
    fig.text(0.012, 0.005, texto, color=CINZA, fontsize=9, ha="left", va="bottom")


# ---------------------------------------------------------------- GIF 1
def gif_ranking(df: pd.DataFrame, path: Path, frames: int = 40, hold: int = 30):
    """Barras do ranking crescendo até a taxa final."""
    d = df.sort_values("taxa_calculada_100k")
    labels = d["municipio"] + " (" + d["uf"] + ")"
    valores = d["taxa_calculada_100k"].to_numpy()
    cores = d["regiao"].map(CORES).to_numpy()
    mediana = np.median(valores)

    fig, ax = plt.subplots(figsize=(8, 8.4), dpi=90)
    bars = ax.barh(labels, np.zeros_like(valores), color=cores)
    textos = [ax.text(0, i, "", va="center", fontsize=8.5, color=TEXTO) for i in range(len(valores))]
    ax.set_xlim(0, valores.max() * 1.12)
    ax.set_title("Homicídios por 100 mil habitantes nas capitais")
    ax.set_xlabel("Taxa (homicídios registrados + ocultos)")
    ax.tick_params(axis="y", labelsize=9)
    ax.grid(axis="y", visible=False)
    _legenda_regioes(ax)
    linha = ax.axvline(mediana, color=CINZA, ls="--", lw=1, alpha=0, zorder=0)
    txt_med = ax.text(mediana + 0.8, -0.9, f"mediana {mediana:.1f}", color=CINZA, fontsize=9, alpha=0)
    fig.tight_layout()

    def update(f):
        t = min(f / frames, 1.0)
        t = 1 - (1 - t) ** 3  # ease-out
        for b, tx, v, i in zip(bars, textos, valores, range(len(valores))):
            w = v * t
            b.set_width(w)
            tx.set_position((w + 0.8, i))
            tx.set_text(f"{w:.1f}")
        alpha = 1.0 if f >= frames else 0
        linha.set_alpha(alpha)
        txt_med.set_alpha(alpha)
        return [*bars, *textos, linha, txt_med]

    anim = FuncAnimation(fig, update, frames=frames + hold, blit=False)
    anim.save(path, writer=PillowWriter(fps=20))
    plt.close(fig)


# ---------------------------------------------------------------- GIF 2
def gif_correcao(df: pd.DataFrame, path: Path, frames: int = 36, hold: int = 26):
    """Pontos saem da taxa informada na fonte e deslizam até a taxa recalculada."""
    d = df.sort_values("taxa_calculada_100k", ascending=False).reset_index(drop=True)
    y = np.arange(len(d))
    ini = d["taxa_informada_100k"].to_numpy()
    fim = d["taxa_calculada_100k"].to_numpy()
    inc = d["taxa_inconsistente"].to_numpy()
    cores = np.where(inc, "#e76f51", "#264653")

    fig, ax = plt.subplots(figsize=(8, 8.4), dpi=90)
    ax.set_yticks(y, d["municipio"] + " (" + d["uf"] + ")", fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, max(ini.max(), fim.max()) * 1.1)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Homicídios por 100 mil habitantes")
    titulo = ax.set_title("Taxa como veio na fonte")
    ax.scatter(ini, y, s=40, facecolors="none", edgecolors="#bbbbbb", zorder=2)
    segs = [ax.plot([a, a], [i, i], color="#e76f51", lw=2, alpha=0.6, zorder=1)[0] for i, a in enumerate(ini)]
    pts = ax.scatter(ini, y, s=60, c=cores, zorder=3)
    handles = [
        plt.Line2D([], [], marker="o", ls="", mfc="none", mec="#bbbbbb", markersize=8),
        plt.Line2D([], [], marker="o", ls="", color="#264653", markersize=8),
        plt.Line2D([], [], marker="o", ls="", color="#e76f51", markersize=8),
    ]
    ax.legend(handles, ["informada na fonte", "confere com as contagens", "inconsistente (> 0,5 pt)"],
              loc="lower right", frameon=False)
    fig.tight_layout()

    def update(f):
        if f < 10:
            t = 0.0
        else:
            t = min((f - 10) / frames, 1.0)
            t = 0.5 - 0.5 * np.cos(np.pi * t)  # ease-in-out
        x = ini + (fim - ini) * t
        pts.set_offsets(np.column_stack([x, y]))
        for s, a, xi, i in zip(segs, ini, x, y):
            s.set_data([a, xi], [i, i])
        if t >= 1:
            titulo.set_text(f"Recalculada: {int(inc.sum())} de {len(d)} capitais não batiam")
        elif t > 0:
            titulo.set_text("Recalculando: homicídios ÷ população × 100 mil")
        return [pts, *segs, titulo]

    anim = FuncAnimation(fig, update, frames=10 + frames + hold, blit=False)
    anim.save(path, writer=PillowWriter(fps=18))
    plt.close(fig)


# ---------------------------------------------------------------- PNGs
def png_regioes(df: pd.DataFrame, path: Path):
    ordem = df.groupby("regiao")["taxa_calculada_100k"].median().sort_values(ascending=False).index
    fig, ax = plt.subplots(figsize=(9, 5), dpi=130)
    rng = np.random.default_rng(0)
    for i, r in enumerate(ordem):
        v = df.loc[df["regiao"] == r, "taxa_calculada_100k"]
        ax.boxplot(v, positions=[i], widths=0.5, patch_artist=True, showfliers=False,
                   boxprops=dict(facecolor=CORES[r], alpha=0.35, edgecolor=CORES[r]),
                   medianprops=dict(color=CORES[r], lw=2.5),
                   whiskerprops=dict(color=CORES[r]), capprops=dict(color=CORES[r]))
        ax.scatter(i + rng.uniform(-0.12, 0.12, len(v)), v, color=CORES[r], s=45, zorder=3, edgecolor="white")
    ax.set_xticks(range(len(ordem)), [NOMES[r] for r in ordem])
    ax.set_ylabel("Homicídios por 100 mil")
    ax.set_title("Norte e Nordeste concentram as taxas mais altas")
    ax.grid(axis="x", visible=False)
    _subtitulo(fig, "Cada ponto é uma capital. Linha grossa = mediana da região.")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path)
    plt.close(fig)


def png_populacao(df: pd.DataFrame, path: Path):
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=130)
    ax.scatter(df["populacao"], df["taxa_calculada_100k"], c=df["regiao"].map(CORES), s=70, edgecolor="white", zorder=3)
    destaque = {"Porto Velho", "Salvador", "Recife", "São Paulo", "Brasília", "Rio de Janeiro", "Florianópolis", "Manaus"}
    for _, r in df[df["municipio"].isin(destaque)].iterrows():
        ax.annotate(r["municipio"], (r["populacao"], r["taxa_calculada_100k"]), xytext=(6, 3),
                    textcoords="offset points", fontsize=9, color=TEXTO)
    ax.set_xscale("log")
    ax.set_xticks([3e5, 1e6, 3e6, 1e7], ["300 mil", "1 milhão", "3 milhões", "10 milhões"])
    ax.minorticks_off()
    ax.set_xlabel("População (escala log)")
    ax.set_ylabel("Homicídios por 100 mil")
    corr = df["log_populacao"].corr(df["taxa_calculada_100k"])
    ax.set_title("Tamanho da cidade quase não explica a taxa")
    _legenda_regioes(ax, loc="upper right")
    _subtitulo(fig, f"Correlação (log população × taxa): {corr:.2f}")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path)
    plt.close(fig)


def png_modelos(df: pd.DataFrame, path: Path):
    res = compare_models(df)
    nomes = {
        "Baseline (média)": "Baseline: prever a média",
        "OLS: taxa ~ log(pop)": "Regressão: só população",
        "OLS: taxa ~ log(pop) + região": "Regressão: população + região",
        "Bin. Negativa: homicídios ~ log(pop) + região": "Binomial negativa: população + região",
    }
    r = res.loc[list(nomes)][::-1]
    base = res.loc["Baseline (média)", "MAE"]
    cores = [CINZA if "Baseline" in i else ("#e76f51" if v > base else "#2a9d8f") for i, v in zip(r.index, r["MAE"])]
    fig, ax = plt.subplots(figsize=(9, 4), dpi=130)
    ax.barh([nomes[i] for i in r.index], r["MAE"], color=cores, height=0.6)
    ax.axvline(base, color=CINZA, ls="--", lw=1)
    for i, (v, r2) in enumerate(zip(r["MAE"], r["R² (LOOCV)"])):
        ax.text(v + 0.2, i, f"{v:.1f}   (R² {r2:+.2f})", va="center", fontsize=10)
    ax.set_xlim(0, r["MAE"].max() * 1.35)
    ax.set_xlabel("Erro médio absoluto na validação cruzada (menor é melhor)")
    ax.set_title("Só população erra mais que a média; região ajuda")
    ax.grid(axis="y", visible=False)
    _subtitulo(fig, "Leave-one-out: cada capital é prevista por um modelo que não a viu.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path)
    plt.close(fig)


def png_residuos(df: pd.DataFrame, path: Path):
    cv = loocv(df, "Bin. Negativa: homicídios ~ log(pop) + região")
    d = df.assign(res=df["taxa_calculada_100k"] - cv.predicoes).sort_values("res")
    fig, ax = plt.subplots(figsize=(9, 8), dpi=130)
    cores = np.where(d["res"] > 0, "#e76f51", "#2a9d8f")
    ax.barh(d["municipio"], d["res"], color=cores, height=0.7)
    for i, (_, r) in enumerate(d.iterrows()):
        if r["taxa_inconsistente"]:
            x = r["res"] + (1 if r["res"] > 0 else -1)
            ax.text(x, i, "⚠", va="center", ha="left" if r["res"] > 0 else "right", fontsize=10, color=CINZA)
    ax.axvline(0, color=TEXTO, lw=0.8)
    ax.set_xlabel("Observado − previsto (homicídios por 100 mil)")
    ax.set_title("Capitais acima e abaixo do esperado para porte e região")
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", labelsize=9.5)
    _subtitulo(fig, "⚠ = taxa inconsistente na fonte. Vermelho = mais violenta do que o modelo previa.")
    fig.tight_layout(rect=(0, 0.025, 1, 1))
    fig.savefig(path)
    plt.close(fig)


def png_ocultos(df: pd.DataFrame, path: Path):
    d = df.sort_values("pct_ocultos", ascending=False).head(10)[::-1]
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=130)
    ax.barh(d["municipio"], d["pct_ocultos"], color=d["regiao"].map(CORES), height=0.65)
    for i, (v, n) in enumerate(zip(d["pct_ocultos"], d["homicidios_ocultos"])):
        ax.text(v + 0.3, i, f"{v:.1f}%  ({n} ocultos)", va="center", fontsize=9.5)
    ax.set_xlim(0, d["pct_ocultos"].max() * 1.3)
    ax.set_xlabel("% dos homicídios estimados que não aparecem nos registros")
    ax.set_title("Subnotificação: onde os registros oficiais mais escondem")
    ax.grid(axis="y", visible=False)
    _subtitulo(fig, "10 capitais com maior proporção de homicídios ocultos.")
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(path)
    plt.close(fig)


def build_all(out_dir: Path = FIG_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = load_processed()
    jobs = {
        "ranking.gif": gif_ranking,
        "correcao_taxas.gif": gif_correcao,
        "regioes.png": png_regioes,
        "populacao.png": png_populacao,
        "ocultos.png": png_ocultos,
        "modelos.png": png_modelos,
        "residuos.png": png_residuos,
    }
    paths = []
    for nome, fn in jobs.items():
        p = out_dir / nome
        fn(df, p)
        paths.append(p)
    return paths
