# PredictiveCrimeAnalysis

Análise exploratória e preditiva da **taxa de homicídios nas 27 capitais brasileiras**, considerando homicídios registrados e ocultos (subnotificados). Inspirado no *Atlas da Violência*.

Objetivo de longo prazo: estimar a taxa de homicídios a partir de fatores socioeconômicos, de policiamento e de clima, para apoiar a priorização de políticas de prevenção. A versão atual trabalha só com população e região; veja [SUGESTOES.md](SUGESTOES.md) para o roteiro.

## Principais resultados até agora

| | |
|---|---|
| **Qualidade dos dados** | Em 9 das 27 capitais a taxa informada na fonte não bate com `homicídios ÷ população`. Porto Velho: 54,9 informado contra 87,6 calculado. Brasília (48 homicídios, taxa 1,8) parece subestimada. Detalhes em [`reports/validacao_dados.md`](reports/validacao_dados.md). |
| **Região domina** | As 7 capitais do quartil de maior risco são todas do Norte ou Nordeste. Capitais do Norte têm ≈3× a taxa do Centro-Oeste para a mesma população. |
| **População não prevê** | Um modelo só com população erra **mais** que prever a média (R² fora da amostra = −0,14). |
| **Melhor modelo atual** | Binomial negativa com população + região: R² fora da amostra ≈ 0,18, erro médio ≈ 13 homicídios por 100 mil. |

## Estrutura

```
├── data/
│   ├── raw/                  # dados originais (não editar à mão)
│   └── processed/            # gerado por `python -m crime_analysis process`
├── notebooks/
│   ├── 01_analise_exploratoria.ipynb
│   └── 02_modelagem.ipynb
├── reports/
│   └── validacao_dados.md    # gerado pela validação
├── src/crime_analysis/
│   ├── config.py             # caminhos e constantes
│   ├── data.py               # carga, validação e limpeza
│   ├── model.py              # modelos + validação cruzada leave-one-out
│   └── __main__.py           # CLI
├── tests/
├── SUGESTOES.md              # próximos passos
└── pyproject.toml
```

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

python -m crime_analysis process   # valida data/raw e gera data/processed + relatório
python -m crime_analysis models    # compara modelos por validação cruzada
pytest                             # roda os testes

jupyter lab notebooks/
```

## Dicionário de dados (`data/processed`)

| Coluna | Descrição |
|---|---|
| `municipio`, `uf`, `regiao` | Identificação (regiões: N, NE, CO, SE, S) |
| `populacao` | População usada na fonte |
| `homicidios_registrados` | Homicídios registrados oficialmente (A) |
| `homicidios_ocultos` | Mortes violentas de causa indeterminada estimadas como homicídio (B) |
| `homicidios_estimados` | A + B |
| `taxa_informada_100k` | Taxa como veio na fonte (pode estar errada) |
| `taxa_calculada_100k` | `homicidios_estimados ÷ populacao × 100.000`; **usada nas análises** |
| `taxa_inconsistente` | `True` se informada e calculada diferem mais de 0,5 ponto |
| `pct_ocultos` | % de homicídios ocultos sobre o total estimado |
| `log_populacao` | Logaritmo natural da população |

## Metodologia

- **Nada é corrigido em silêncio.** A taxa original é preservada ao lado da recalculada, e cada divergência vai para o relatório de validação.
- **Validação cruzada leave-one-out**, porque com 27 linhas um único split treino/teste é instável.
- **Baseline obrigatório:** todo modelo é comparado com "prever a média".
- **GLM de contagem (binomial negativa) com offset log(população)**, mais adequado a homicídios do que regressão linear sobre a taxa.

## Uso responsável

Os resultados são associações, não causas. Modelos de "crime preditivo" podem reforçar vieses quando usados para direcionar vigilância a pessoas ou bairros. Este projeto trabalha no nível de município e foi pensado para orientar políticas de prevenção.
