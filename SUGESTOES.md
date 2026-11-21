# Sugestões e próximos passos

Em ordem de impacto. Os itens 1 e 2 vêm antes de qualquer modelo mais sofisticado.

## 1. Corrigir os dados na fonte (prioridade máxima)

- **Revisar as 9 capitais com taxa inconsistente** listadas em `reports/validacao_dados.md`, principalmente Porto Velho (−32,7 pontos), São Luís (−18,5), Natal (−15,0) e Recife (−14,8). É preciso descobrir qual valor foi copiado errado: contagem, população ou taxa.
- **Conferir Brasília.** 48 homicídios registrados para mais de 3 milhões de habitantes é implausível para o DF. Esse ponto sozinho distorce a estimativa da região Centro-Oeste.
- **Conferir a população.** A coluna diz "2022", mas alguns valores parecem ser estimativas anteriores ao Censo 2022 (ex.: São Paulo com 12,3 milhões, Rio com 6,8 milhões). Use uma única fonte: Censo 2022 ou estimativas do IBGE para o ano dos homicídios.
- **Documentar a origem:** link, edição do Atlas, ano de referência e data de download, num `data/raw/README.md`. Hoje não dá para saber de onde os números vieram.

## 2. Ampliar a base

Com 27 linhas e um único ano, nenhum modelo vai longe.

- **Vários anos:** o [Atlas da Violência (Ipea/FBSP)](https://www.ipea.gov.br/atlasviolencia/) e o SIM/DATASUS têm séries por município. Com 10 anos × 27 capitais você passa de 27 para ~270 observações e pode estudar tendências.
- **Todos os municípios** (ou os com mais de 100 mil habitantes), não só capitais: mais variação e mais poder estatístico.
- Automatizar o download num script `src/crime_analysis/download.py`, em vez de colar CSVs à mão.

## 3. Trazer as variáveis prometidas no README

O README fala em fatores socioeconômicos, policiamento e clima, mas nenhum está no dataset. Fontes públicas por município:

| Fator | Variáveis | Fonte |
|---|---|---|
| Socioeconômico | renda per capita, Gini, desemprego, IDH-M, escolaridade, % jovens 15–29 anos | IBGE (Censo, PNAD Contínua), Atlas do Desenvolvimento Humano (PNUD) |
| Urbano | densidade, % em favelas/comunidades urbanas, saneamento | IBGE Censo 2022 |
| Segurança | efetivo policial, gasto em segurança per capita, apreensões de armas | Anuário Brasileiro de Segurança Pública (FBSP), SINESP |
| Clima | temperatura média, precipitação | INMET (agregado anual ou mensal por estação) |

Junte tudo pelo **código IBGE do município** (7 dígitos), não pelo nome: nomes com acento ou grafia diferente quebram o merge.

## 4. Modelagem

- **Manter a binomial negativa com offset** como modelo principal. Com várias variáveis, avaliar regularização (Lasso/Ridge) para evitar overfitting.
- Com painel (cidade × ano): **efeitos fixos de município** ou modelos mistos, para separar o que é característica estável da cidade do que muda no tempo.
- Testar modelos de árvore (Random Forest, Gradient Boosting) **só depois** de ter dezenas de variáveis e centenas de linhas, sempre contra o baseline e com validação cruzada.
- Em séries temporais, validar com **split temporal** (treina até 2019, testa 2020–2022), nunca aleatório.
- Analisar **dependência espacial**: capitais vizinhas tendem a ter taxas parecidas (rotas de tráfico, facções). Índice de Moran e modelos espaciais (`pysal`/`esda`).

## 5. Engenharia e reprodutibilidade

- Pre-commit com `ruff` (lint/format) e `nbstripout` (remove saídas dos notebooks antes do commit, deixando o diff legível).
- GitHub Actions rodando `pytest` e `python -m crime_analysis process` a cada push.
- Fixar versões com `pip freeze > requirements.lock` ou usar `uv`/`poetry`.
- Um mapa coroplético (geopandas + malha do IBGE) seria a visualização mais forte para o README.

## 6. Comunicação e ética

- Trocar "prever criminalidade" por "estimar a taxa esperada e identificar capitais acima do esperado". Esse é o uso mais útil dos resíduos do modelo.
- Mencionar sempre a subnotificação: em Aracaju ~25% dos homicídios estimados são "ocultos".
- Evitar granularidade de bairro ou indivíduo com dados policiais: o modelo aprende onde a polícia registra, não necessariamente onde o crime acontece.
- Um dashboard simples (Streamlit) com ranking, mapa e resíduos facilitaria apresentar o projeto a gestores ou em portfólio.
