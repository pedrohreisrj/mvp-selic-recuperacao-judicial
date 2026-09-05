# Databricks notebook source
# MAGIC %md
# MAGIC ## Setup do ambiente
# MAGIC Criação do catálogo do projeto (`mvp_juros_rj`) e dos três schemas que
# MAGIC representam a arquitetura medalhão (`bronze`, `silver`, `gold`), além de
# MAGIC um Volume (`bronze.arquivos_brutos`) para armazenar arquivos brutos que
# MAGIC não vêm de API (como o export da Serasa Experian).

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS mvp_juros_rj;
# MAGIC CREATE SCHEMA IF NOT EXISTS mvp_juros_rj.bronze;
# MAGIC CREATE SCHEMA IF NOT EXISTS mvp_juros_rj.silver;
# MAGIC CREATE SCHEMA IF NOT EXISTS mvp_juros_rj.gold;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE VOLUME IF NOT EXISTS mvp_juros_rj.bronze.arquivos_brutos;