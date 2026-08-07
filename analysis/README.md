# Análise

A camada `analytics` (star schema) fica pronta para consumo em qualquer
ferramenta de BI. Este projeto sobe o **Metabase** via Docker para isso.
Sem código, o cliente monta seus próprios painéis em cima dos dados já
limpos.

## Acessando o Metabase

```bash
docker compose up -d metabase
```

Acesse http://localhost:3000 (porta configurável em `METABASE_PORT` no
`.env`), crie a conta de administrador na primeira execução e conecte o
Postgres como fonte de dados:

| Campo | Valor |
|---|---|
| Database type | PostgreSQL |
| Host | `postgres` (nome do serviço na rede Docker) |
| Port | `5432` |
| Database name | valor de `POSTGRES_DB` no `.env` |
| Username / Password | valores de `POSTGRES_USER` / `POSTGRES_PASSWORD` no `.env` |

A partir daí, todas as tabelas de `analytics.*` (e `raw.*`, `audit.*`)
ficam disponíveis para construir perguntas, gráficos e dashboards direto
na interface do Metabase.

## Perguntas de negócio de partida

`sql/*.sql` traz consultas prontas. Cole qualquer uma delas em uma
"Native Query" do Metabase para começar um dashboard, ou use como
referência para montar as mesmas métricas no editor visual:

| Arquivo | Pergunta |
|------|----------|
| `01_revenue_overview.sql` | KPIs gerais: pedidos, clientes, unidades, receita líquida, descontos, ticket médio |
| `02_revenue_by_category.sql` | Quais categorias de produto geram mais receita? |
| `03_top_products.sql` | Quais produtos individuais vendem mais? |
| `04_customer_segments.sql` | Como a receita se distribui por segmento de idade do cliente? |
| `05_geography.sql` | Quais países geram mais receita? |

## Nota sobre análise temporal

Os carrinhos do DummyJSON não têm data de pedido real (ver seção
"premissas documentadas" no README raiz), então `fact_orders.order_date_key`
reflete a `ingestion_date` do pipeline, não uma data de compra real. Um
único run do pipeline produz um dia de pedidos. Rodar `--date` várias
vezes (`uv run python main.py --date YYYY-MM-DD`) acumula histórico e
habilita gráficos de tendência dia a dia no Metabase.
