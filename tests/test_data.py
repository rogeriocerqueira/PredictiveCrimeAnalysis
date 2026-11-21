import pandas as pd
import pytest

from crime_analysis import config
from crime_analysis.data import clean, load_raw, validate
from crime_analysis.model import compare_models


@pytest.fixture
def raw():
    return load_raw(config.RAW_FILE)


def _linha(**kw):
    base = dict(
        municipio="Cidade", uf="XX", regiao="NE", populacao=100_000,
        homicidios_registrados=20, homicidios_ocultos=5, homicidios_estimados=25,
        taxa_informada_100k=25.0,
    )
    base.update(kw)
    return base


def test_colunas_padronizadas(raw):
    assert list(raw.columns) == list(config.COLUMN_MAP.values())
    assert len(raw) == 27


def test_dados_reais_sem_erros_estruturais(raw):
    assert validate(raw).ok


def test_detecta_taxa_inconsistente():
    df = pd.DataFrame([_linha(taxa_informada_100k=40.0)])
    rep = validate(df)
    assert rep.ok
    assert any("taxa informada" in a for a in rep.avisos)


def test_detecta_soma_errada():
    df = pd.DataFrame([_linha(homicidios_estimados=30, taxa_informada_100k=30.0)])
    assert not validate(df).ok


def test_detecta_duplicata_e_regiao_invalida():
    df = pd.DataFrame([_linha(), _linha(regiao="XX")])
    erros = " ".join(validate(df).erros)
    assert "duplicados" in erros and "Regiões inválidas" in erros


def test_clean_recalcula_taxa(raw):
    df = clean(raw)
    salvador = df.set_index("municipio").loc["Salvador"]
    assert salvador["taxa_calculada_100k"] == pytest.approx(66.39, abs=0.01)
    porto_velho = df.set_index("municipio").loc["Porto Velho"]
    assert bool(porto_velho["taxa_inconsistente"])


def test_comparacao_de_modelos_roda(raw):
    res = compare_models(clean(raw))
    assert "Baseline (média)" in res.index
    assert res["MAE"].notna().all()


def test_figuras_sao_geradas(tmp_path):
    from crime_analysis.figures import build_all

    paths = build_all(tmp_path)
    assert len(paths) == 7
    assert all(p.exists() and p.stat().st_size > 0 for p in paths)
