# Databricks notebook source
# MAGIC %md
# MAGIC **Ingestão 1: Falências e RJ (Serasa Experian)**
# MAGIC Instalação da dependência openpyxl, necessária para leitura de arquivos .xlsx no ambiente Databricks (não vem instalada por padrão).

# COMMAND ----------

# MAGIC %pip install openpyxl

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

import pandas as pd
from pyspark.sql.functions import lit, current_timestamp

# COMMAND ----------

# MAGIC %md
# MAGIC Leitura definitiva com base no diagnóstico acima: pula as 4 primeiras linhas (título/cabeçalho mesclado), renomeia as 6 colunas de dados e descarta a nota de rodapé via filtro de data inválida.

# COMMAND ----------

pdf = pd.read_excel(
    "/Volumes/mvp_juros_rj/bronze/arquivos_brutos/falencias-e-recuperacoes-abr26.xlsx",
    sheet_name="Total de Processos",
    header=None,
    skiprows=4
)

# mantém só as 6 colunas de dados (A até F)
pdf = pdf.iloc[:, :6]
pdf.columns = [
    "mes_referencia",
    "falencias_requeridas",
    "falencias_decretadas",
    "rj_requeridas",
    "rj_deferidas",
    "rj_concedidas",
]

# converte a coluna de data e descarta qualquer linha que não seja uma data válida
# (isso remove automaticamente a nota de rodapé "*Os dados estão sujeitos a revisões.")
pdf["mes_referencia"] = pd.to_datetime(pdf["mes_referencia"], errors="coerce")
pdf = pdf.dropna(subset=["mes_referencia"])

pdf.head()

# COMMAND ----------

# MAGIC %md
# MAGIC Gravação como tabela Bronze, mantendo os dados o mais próximo possível
# MAGIC do estado bruto. Não há conversão de tipo aqui, só a adição dos
# MAGIC metadados de rastreabilidade (data_ingestao e fonte).

# COMMAND ----------

from pyspark.sql.functions import lit, current_timestamp

df = spark.createDataFrame(pdf)
df = df.withColumn("data_ingestao", current_timestamp()) \
       .withColumn("fonte", lit("Serasa Experian - export manual"))

df.write.mode("overwrite").saveAsTable("mvp_juros_rj.bronze.rj_falencias_mensal")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM mvp_juros_rj.bronze.rj_falencias_mensal LIMIT 10;

# COMMAND ----------

# MAGIC %md
# MAGIC **Ingestão 2: Selic mensal (API BCB)**
# MAGIC
# MAGIC Chamada direta à API pública do Banco Central, série 4390 (Selic
# MAGIC acumulada mensal). Diferente da fonte anterior, não precisa de arquivo
# MAGIC intermediário nem de tratamento de estrutura.

# COMMAND ----------

import requests
import pandas as pd
from pyspark.sql.functions import lit, current_timestamp

url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.4390/dados?formato=json"
resp = requests.get(url)
dados = resp.json()

pdf_selic = pd.DataFrame(dados)  # colunas: 'data' (string dd/mm/aaaa) e 'valor' (string)
df_selic = spark.createDataFrame(pdf_selic)
df_selic = df_selic.withColumn("data_ingestao", current_timestamp()) \
                    .withColumn("fonte", lit("API BCB SGS - série 4390"))

df_selic.write.mode("overwrite").saveAsTable("mvp_juros_rj.bronze.selic_mensal")

# COMMAND ----------

# MAGIC %md
# MAGIC **Ingestão 3: Contexto histórico anual**
# MAGIC
# MAGIC Essa fonte é diferente das outras duas: não vem de um arquivo ou API
# MAGIC único, é uma compilação manual feita a partir de vários comunicados de
# MAGIC imprensa institucionais da Serasa Experian (metodologia anterior à
# MAGIC atualização de 2026 do indicador). Cada valor está marcado como
# MAGIC "primario" (veio direto de um release) ou "estimado" (calculado a
# MAGIC partir de uma variação percentual divulgada, quando o número absoluto
# MAGIC não foi encontrado).

# COMMAND ----------

contexto_anual = [
    {"ano": 2016, "pedidos_rj": 1863, "selic_media_anual": 14.08, "tipo_valor": "primario"},
    {"ano": 2017, "pedidos_rj": 1420, "selic_media_anual": 10.08, "tipo_valor": "primario"},
    {"ano": 2018, "pedidos_rj": 1408, "selic_media_anual": 6.48,  "tipo_valor": "primario"},
    {"ano": 2019, "pedidos_rj": 1387, "selic_media_anual": 5.94,  "tipo_valor": "estimado"},
    {"ano": 2020, "pedidos_rj": 1179, "selic_media_anual": 2.79,  "tipo_valor": "primario"},
    {"ano": 2021, "pedidos_rj": 891,  "selic_media_anual": 4.42,  "tipo_valor": "primario"},
    {"ano": 2022, "pedidos_rj": 833,  "selic_media_anual": 12.43, "tipo_valor": "estimado"},
    {"ano": 2023, "pedidos_rj": 1405, "selic_media_anual": 13.20, "tipo_valor": "primario"},
    {"ano": 2024, "pedidos_rj": 2273, "selic_media_anual": 10.84, "tipo_valor": "primario"},
]

pdf_contexto = pd.DataFrame(contexto_anual)
df_contexto = spark.createDataFrame(pdf_contexto) \
                    .withColumn("data_ingestao", current_timestamp()) \
                    .withColumn("fonte", lit("Comunicados institucionais Serasa Experian (metodologia anterior a 2026)"))

df_contexto.write.mode("overwrite").saveAsTable("mvp_juros_rj.bronze.rj_contexto_anual")

# COMMAND ----------

# MAGIC %md
# MAGIC Verificação final: confirma que as três tabelas Bronze foram gravadas com sucesso.

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW TABLES IN mvp_juros_rj.bronze;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM mvp_juros_rj.bronze.rj_contexto_anual ORDER BY ano;