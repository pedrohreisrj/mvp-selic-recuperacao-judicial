# Databricks notebook source
# MAGIC %md
# MAGIC ## Camada Gold: Modelagem em Esquema Estrela
# MAGIC
# MAGIC **Dimensão: dim_tempo**
# MAGIC
# MAGIC Tabela dimensão construída a partir do grão real do projeto (28 meses,
# MAGIC jan/2024 a abr/2026), definido pela tabela de Falências e RJ, não pela
# MAGIC série da Selic, que tem um histórico bem mais longo e não representa a
# MAGIC janela de análise deste MVP. Contém atributos derivados (ano,
# MAGIC trimestre, nome do mês) pra facilitar agregações mais na frente, na
# MAGIC etapa de Análise.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE mvp_juros_rj.gold.dim_tempo AS
# MAGIC SELECT
# MAGIC   mes_referencia,
# MAGIC   YEAR(mes_referencia)              AS ano,
# MAGIC   QUARTER(mes_referencia)           AS trimestre,
# MAGIC   date_format(mes_referencia, 'MMMM') AS nome_mes
# MAGIC FROM mvp_juros_rj.silver.rj_falencias_mensal
# MAGIC ORDER BY mes_referencia;
# MAGIC
# MAGIC SELECT * FROM mvp_juros_rj.gold.dim_tempo LIMIT 5;

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC **Fato: `fato_indicadores_mensais`**
# MAGIC
# MAGIC Junção entre `silver.selic_mensal` e `silver.rj_falencias_mensal` pela
# MAGIC chave de mês, unindo pela primeira vez no pipeline as duas fontes de
# MAGIC metodologia atual (jan/2024–abr/2026). Utilizado `INNER JOIN` de
# MAGIC propósito: qualquer mês sem correspondência exata entre as duas tabelas
# MAGIC seria descartado silenciosamente, então a contagem final de linhas foi
# MAGIC validada manualmente contra o total esperado (28), confirmando que não
# MAGIC houve perda de dados no cruzamento.
# MAGIC
# MAGIC Esta tabela alimenta diretamente a Pergunta de negócio 1 (correlação e
# MAGIC defasagem entre Selic e pedidos de RJ, curto prazo).

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE mvp_juros_rj.gold.fato_indicadores_mensais AS
# MAGIC SELECT
# MAGIC   rj.mes_referencia,
# MAGIC   s.selic_mensal_pct,
# MAGIC   rj.falencias_requeridas,
# MAGIC   rj.falencias_decretadas,
# MAGIC   rj.rj_requeridas,
# MAGIC   rj.rj_deferidas,
# MAGIC   rj.rj_concedidas
# MAGIC FROM mvp_juros_rj.silver.rj_falencias_mensal rj
# MAGIC INNER JOIN mvp_juros_rj.silver.selic_mensal s
# MAGIC   ON rj.mes_referencia = s.data_referencia
# MAGIC ORDER BY rj.mes_referencia;
# MAGIC
# MAGIC SELECT COUNT(*) AS total_linhas FROM mvp_juros_rj.gold.fato_indicadores_mensais;

# COMMAND ----------

# MAGIC %md
# MAGIC **Fato: fato_contexto_anual**
# MAGIC
# MAGIC Promoção direta de silver.rj_contexto_anual pra camada Gold, sem
# MAGIC nenhuma junção adicional: a tabela já está no grão e no formato
# MAGIC necessários pra consumo. Foi mantida separada de
# MAGIC fato_indicadores_mensais de propósito, porque representa uma
# MAGIC metodologia diferente (anterior à atualização de 2026 do indicador
# MAGIC Serasa Experian) e um grão diferente (anual, não mensal). Não recebeu
# MAGIC uma tabela dimensão própria: o campo ano funciona aqui como dimensão
# MAGIC degenerada, já que não carrega nenhum atributo descritivo que
# MAGIC justifique criar uma tabela separada pra ele.
# MAGIC
# MAGIC Essa tabela alimenta a Pergunta de negócio 2 (padrão histórico de
# MAGIC longo prazo entre ciclos de juros e volume de pedidos de RJ).

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE mvp_juros_rj.gold.fato_contexto_anual AS
# MAGIC SELECT * FROM mvp_juros_rj.silver.rj_contexto_anual
# MAGIC ORDER BY ano;
# MAGIC
# MAGIC SELECT * FROM mvp_juros_rj.gold.fato_contexto_anual;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM mvp_juros_rj.gold.fato_contexto_anual ORDER BY ano;