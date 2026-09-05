# Databricks notebook source
# MAGIC %md
# MAGIC Célula 1 — Markdown de abertura

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC ## Qualidade de Dados
# MAGIC
# MAGIC Verificação sistemática das cinco dimensões de qualidade indicadas pelo
# MAGIC enunciado (completude, consistência, unicidade, acurácia, outliers) sobre
# MAGIC as tabelas da camada Gold. Alguns problemas já foram identificados e
# MAGIC tratados durante a Silver (ver documentação daquela camada); esta seção
# MAGIC formaliza a checagem completa e verifica se algo passou despercebido.

# COMMAND ----------

# MAGIC %md
# MAGIC **Completude**: verificação de valores nulos em todas as colunas
# MAGIC numéricas da tabela mensal.
# MAGIC [célula: completude]

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   COUNT(*) AS total_linhas,
# MAGIC   SUM(CASE WHEN selic_mensal_pct    IS NULL THEN 1 ELSE 0 END) AS nulos_selic,
# MAGIC   SUM(CASE WHEN falencias_requeridas IS NULL THEN 1 ELSE 0 END) AS nulos_fal_req,
# MAGIC   SUM(CASE WHEN falencias_decretadas IS NULL THEN 1 ELSE 0 END) AS nulos_fal_dec,
# MAGIC   SUM(CASE WHEN rj_requeridas        IS NULL THEN 1 ELSE 0 END) AS nulos_rj_req,
# MAGIC   SUM(CASE WHEN rj_deferidas         IS NULL THEN 1 ELSE 0 END) AS nulos_rj_def,
# MAGIC   SUM(CASE WHEN rj_concedidas        IS NULL THEN 1 ELSE 0 END) AS nulos_rj_con
# MAGIC FROM mvp_juros_rj.gold.fato_indicadores_mensais;

# COMMAND ----------

# MAGIC %md
# MAGIC **Unicidade**: verificação de meses duplicados.
# MAGIC [célula: unicidade]

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT mes_referencia, COUNT(*) AS qtd
# MAGIC FROM mvp_juros_rj.gold.fato_indicadores_mensais
# MAGIC GROUP BY mes_referencia
# MAGIC HAVING COUNT(*) > 1;

# COMMAND ----------

# MAGIC %md
# MAGIC **Consistência**: verificação de faixa de valores (Selic) e de lógica
# MAGIC entre estágios do processo judicial (requerida/deferida/concedida,
# MAGIC requerida/decretada).
# MAGIC [célula: WHERE com as 14 linhas]

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM mvp_juros_rj.gold.fato_indicadores_mensais
# MAGIC WHERE selic_mensal_pct < 0 OR selic_mensal_pct > 5
# MAGIC    OR rj_deferidas > rj_requeridas
# MAGIC    OR rj_concedidas > rj_deferidas
# MAGIC    OR falencias_decretadas > falencias_requeridas;

# COMMAND ----------

# MAGIC %md
# MAGIC **Outliers**
# MAGIC
# MAGIC Identificação de meses em que `rj_requeridas` foge mais de 2 desvios-padrão
# MAGIC da média do período, não indicam erro no dado, mas eventos que merecem
# MAGIC atenção na etapa de Análise.

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH stats AS (
# MAGIC   SELECT AVG(rj_requeridas) AS media, STDDEV(rj_requeridas) AS desvio
# MAGIC   FROM mvp_juros_rj.gold.fato_indicadores_mensais
# MAGIC )
# MAGIC SELECT f.mes_referencia, f.rj_requeridas,
# MAGIC        ROUND(stats.media, 1) AS media_geral,
# MAGIC        ROUND(stats.desvio, 1) AS desvio_padrao
# MAGIC FROM mvp_juros_rj.gold.fato_indicadores_mensais f, stats
# MAGIC WHERE f.rj_requeridas > stats.media + 2 * stats.desvio
# MAGIC    OR f.rj_requeridas < stats.media - 2 * stats.desvio;

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC Os dois outliers identificados fazem sentido à luz do próprio objetivo
# MAGIC do projeto: jan/2024 é o primeiro mês da série (volume ainda baixo, sem
# MAGIC efeito acumulado do ciclo de juros), enquanto jul/2025 coincide com um
# MAGIC dos picos observados na fase mais elevada da Selic dentro da janela
# MAGIC analisada. Ambos serão retomados na seção de Análise.

# COMMAND ----------

# MAGIC %md
# MAGIC **Verificações complementares**
# MAGIC
# MAGIC Unicidade e consistência de domínio aplicadas também à tabela de
# MAGIC contexto histórico anual (`fato_contexto_anual`).

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Unicidade
# MAGIC SELECT ano, COUNT(*) AS qtd FROM mvp_juros_rj.gold.fato_contexto_anual GROUP BY ano HAVING COUNT(*) > 1;
# MAGIC
# MAGIC -- Consistência de domínio (tipo_valor só pode ser primario/estimado)
# MAGIC SELECT DISTINCT tipo_valor FROM mvp_juros_rj.gold.fato_contexto_anual;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   SUM(CASE WHEN rj_deferidas > rj_requeridas THEN 1 ELSE 0 END) AS casos_deferida_maior_requerida,
# MAGIC   SUM(CASE WHEN rj_concedidas > rj_deferidas THEN 1 ELSE 0 END) AS casos_concedida_maior_deferida,
# MAGIC   SUM(CASE WHEN falencias_decretadas > falencias_requeridas THEN 1 ELSE 0 END) AS casos_falencia_inconsistente,
# MAGIC   SUM(CASE WHEN selic_mensal_pct < 0 OR selic_mensal_pct > 5 THEN 1 ELSE 0 END) AS casos_selic_fora_faixa
# MAGIC FROM mvp_juros_rj.gold.fato_indicadores_mensais;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   SUM(rj_requeridas)  AS total_requeridas,
# MAGIC   SUM(rj_deferidas)   AS total_deferidas,
# MAGIC   SUM(rj_concedidas)  AS total_concedidas,
# MAGIC   SUM(falencias_requeridas) AS total_fal_requeridas,
# MAGIC   SUM(falencias_decretadas) AS total_fal_decretadas
# MAGIC FROM mvp_juros_rj.gold.fato_indicadores_mensais;

# COMMAND ----------

# MAGIC %md
# MAGIC **Achado de qualidade: falso positivo investigado**
# MAGIC
# MAGIC A checagem inicial de consistência (comparando mês a mês rj_requeridas,
# MAGIC rj_deferidas e rj_concedidas, e também falencias_requeridas com
# MAGIC falencias_decretadas) sinalizou 14 das 28 linhas como inconsistentes,
# MAGIC porque em alguns meses havia mais casos deferidos ou decretados do que
# MAGIC requeridos naquele mesmo mês.
# MAGIC
# MAGIC A investigação mostrou que isso é esperado: os estágios de um processo
# MAGIC judicial (requerimento, deferimento, concessão) não acontecem no mesmo
# MAGIC mês. Um pedido requerido em novembro pode ser deferido só em janeiro,
# MAGIC por exemplo. A comparação correta é olhar o total acumulado do
# MAGIC período, não mês a mês. E isso se confirmou: somando tudo entre
# MAGIC jan/2024 e abr/2026, requeridas (2.236) fica maior ou igual a
# MAGIC deferidas (1.873), que fica maior ou igual a concedidas (680); o mesmo
# MAGIC vale pra falências requeridas (1.760) e decretadas (1.582). Ou seja, a
# MAGIC cadeia de estágios está correta e não existe inconsistência real nos
# MAGIC dados.