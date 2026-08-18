# Prumo Engenharia — Painel de Obras

Dashboard de demonstração para construtoras. Base 100% sintética, gerada por script,
com eventos reais de canteiro embutidos (chuva, ruptura de estoque, embargo, acidente,
retrabalho) e as respectivas ações de resolução.

## Rodar

```bash
pip install -r requirements.txt
python gerar_dados_prumo.py     # cria prumo.db, prumo.xlsx e /csv
streamlit run app.py
```

## Estrutura

| Arquivo | O que é |
|---|---|
| `gerar_dados_prumo.py` | Gerador da base. Toda a narrativa está na lista `EVENTOS` |
| `app.py` | Dashboard Streamlit (5 painéis) |
| `prumo.db` | SQLite — fonte do dashboard |
| `prumo.xlsx` | Mesma base em Excel, 1 aba por tabela |
| `csv/` | Exportação avulsa |

## Modelo de dados

Estrela: 4 dimensões (`dim_obra`, `dim_etapa`, `dim_calendario`, `dim_fornecedor`)
e 8 fatos. A tabela `fato_eventos` é o motor: cada evento tem um
`fator_produtividade` e um `fator_custo` que distorcem as demais tabelas no mês
correspondente, com decaimento ao longo da janela de efeito.

Avanço real = avanço previsto × índice de produtividade, onde o índice combina
os fatores dos eventos, a sazonalidade de chuva (dez–mar) e um ruído AR(1) —
que faz um mês ruim contaminar o seguinte, como acontece no canteiro.

## Personalizar

Para mudar a narrativa, edite a lista `EVENTOS` em `gerar_dados_prumo.py` e rode
o script de novo. O dashboard lê os eventos direto do banco e se ajusta sozinho.
