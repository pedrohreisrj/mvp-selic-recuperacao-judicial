# Databricks notebook source
# MAGIC %md
# MAGIC **Transformação: Selic mensal**
# MAGIC
# MAGIC Conversão de tipos (string para date/decimal) e filtro de período,
# MAGIC reduzindo a série completa da API, que tem histórico desde 1986, ao
# MAGIC intervalo que interessa pro projeto (2012 em diante).
# MAGIC
# MAGIC **Achado de qualidade**: o registro mais recente retornado pela API na
# MAGIC hora da ingestão (set/2026) veio com valor de apenas 0,10%, bem abaixo
# MAGIC do padrão mensal. Isso indica um mês corrente incompleto, já que a
# MAGIC Selic acumulada de um mês só fecha no final dele. Corrigido com um
# MAGIC filtro de data (<= 2026-04-01), limitando a série ao fim da janela de
# MAGIC análise definida no objetivo do projeto.

# COMMAND ----------

from pyspark.sql.functions import to_date, col

df_selic_bronze = spark.table("mvp_juros_rj.bronze.selic_mensal")

df_selic_silver = (
    df_selic_bronze
    .withColumn("data_referencia", to_date(col("data"), "dd/MM/yyyy"))
    .withColumn("selic_mensal_pct", col("valor").cast("decimal(6,4)"))
    .filter(col("data_referencia") >= "2012-01-01")
    .filter(col("data_referencia") <= "2026-04-01")  # exclui meses incompletos/fora do escopo do projeto
    .select("data_referencia", "selic_mensal_pct")
)

df_selic_silver.write.mode("overwrite").saveAsTable("mvp_juros_rj.silver.selic_mensal")

df_selic_silver.orderBy("data_referencia", ascending=False).limit(5).display()

# COMMAND ----------

# MAGIC %md
# MAGIC **Transformação: Falências e RJ mensal**
# MAGIC
# MAGIC Antes de qualquer conversão de tipo, checagem de qualidade: contagem
# MAGIC total de linhas, quantidade de meses distintos e verificação de
# MAGIC duplicatas por mês.

# COMMAND ----------

from pyspark.sql.functions import to_date, col, count

df_rj_bronze = spark.table("mvp_juros_rj.bronze.rj_falencias_mensal")

# checagem de qualidade: duplicatas de mês e nulos, antes de qualquer transformação
print("Total de linhas:", df_rj_bronze.count())
print("Meses distintos:", df_rj_bronze.select("mes_referencia").distinct().count())

df_rj_bronze.groupBy(
    to_date(col("mes_referencia")).alias("mes")
).agg(count("*").alias("qtd")).filter(col("qtd") > 1).display()

# COMMAND ----------

# MAGIC %md
# MAGIC **Achado de qualidade**: contagem retornou 36 linhas, 8 a mais que o esperado (28 meses, jan/24-abr/26). Investigando o intervalo real de datas presentes na tabela.

# COMMAND ----------

from pyspark.sql.functions import min as spark_min, max as spark_max

df_rj_bronze.select(
    spark_min("mes_referencia").alias("primeiro_mes"),
    spark_max("mes_referencia").alias("ultimo_mes")
).display()

# COMMAND ----------

# MAGIC %md
# MAGIC Identificado que o arquivo de origem já vem pré-formatado com linhas para meses futuros (até dez/2026), todas com valores nulos, provavelmente um "molde" da planilha da Serasa, atualizado mês a mês pela própria empresa.

# COMMAND ----------

df_rj_bronze.orderBy("mes_referencia", ascending=False).limit(10).display()

# COMMAND ----------

# MAGIC %md
# MAGIC **Correção**: filtro removendo as linhas com valores nulos (os meses
# MAGIC "molde" sem dado real) e conversão dos tipos numéricos de float pra
# MAGIC inteiro, já que não existe "meio pedido de RJ". O resultado esperado é
# MAGIC 28 linhas.

# COMMAND ----------

from pyspark.sql.functions import to_date, col

df_rj_silver = (
    df_rj_bronze
    .withColumn("mes_referencia", to_date(col("mes_referencia")))
    .filter(col("falencias_requeridas").isNotNull())  # remove os 8 meses "molde" sem dado real
    .withColumn("falencias_requeridas", col("falencias_requeridas").cast("int"))
    .withColumn("falencias_decretadas", col("falencias_decretadas").cast("int"))
    .withColumn("rj_requeridas", col("rj_requeridas").cast("int"))
    .withColumn("rj_deferidas", col("rj_deferidas").cast("int"))
    .withColumn("rj_concedidas", col("rj_concedidas").cast("int"))
    .select("mes_referencia", "falencias_requeridas", "falencias_decretadas",
            "rj_requeridas", "rj_deferidas", "rj_concedidas")
)

print("Total de linhas após limpeza:", df_rj_silver.count())  # deveria dar 28

df_rj_silver.write.mode("overwrite").saveAsTable("mvp_juros_rj.silver.rj_falencias_mensal")

df_rj_silver.orderBy("mes_referencia", ascending=False).limit(5).display()

# COMMAND ----------

# MAGIC %md
# MAGIC **Transformação: Contexto histórico anual**
# MAGIC
# MAGIC Essa tabela já veio estruturada desde a Bronze, então aqui é só
# MAGIC confirmar e converter os tipos. Não precisou de nenhum tratamento
# MAGIC adicional.

# COMMAND ----------

from pyspark.sql.functions import col

df_contexto_bronze = spark.table("mvp_juros_rj.bronze.rj_contexto_anual")

df_contexto_silver = (
    df_contexto_bronze
    .withColumn("ano", col("ano").cast("int"))
    .withColumn("pedidos_rj", col("pedidos_rj").cast("int"))
    .withColumn("selic_media_anual", col("selic_media_anual").cast("decimal(5,2)"))
    .select("ano", "pedidos_rj", "selic_media_anual", "tipo_valor")
)

df_contexto_silver.write.mode("overwrite").saveAsTable("mvp_juros_rj.silver.rj_contexto_anual")

df_contexto_silver.orderBy("ano").display()