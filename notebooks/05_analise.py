# Databricks notebook source
# MAGIC %md
# MAGIC %md
# MAGIC ## Análise de Dados
# MAGIC
# MAGIC ### Pergunta 1 — Correlação e defasagem (curto prazo, jan/2024-abr/2026)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT corr(selic_mensal_pct, rj_requeridas) AS correlacao_sem_defasagem
# MAGIC FROM mvp_juros_rj.gold.fato_indicadores_mensais;

# COMMAND ----------

# MAGIC %md
# MAGIC Correlação com defasagem (lag), usando LAG() do SQL

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH base AS (
# MAGIC   SELECT
# MAGIC     mes_referencia,
# MAGIC     rj_requeridas,
# MAGIC     LAG(selic_mensal_pct, 1) OVER (ORDER BY mes_referencia) AS selic_lag1,
# MAGIC     LAG(selic_mensal_pct, 2) OVER (ORDER BY mes_referencia) AS selic_lag2,
# MAGIC     LAG(selic_mensal_pct, 3) OVER (ORDER BY mes_referencia) AS selic_lag3,
# MAGIC     LAG(selic_mensal_pct, 6) OVER (ORDER BY mes_referencia) AS selic_lag6
# MAGIC   FROM mvp_juros_rj.gold.fato_indicadores_mensais
# MAGIC )
# MAGIC SELECT
# MAGIC   corr(selic_lag1, rj_requeridas) AS corr_lag1,
# MAGIC   corr(selic_lag2, rj_requeridas) AS corr_lag2,
# MAGIC   corr(selic_lag3, rj_requeridas) AS corr_lag3,
# MAGIC   corr(selic_lag6, rj_requeridas) AS corr_lag6
# MAGIC FROM base;

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC **Visualização das séries**
# MAGIC
# MAGIC Para complementar os coeficientes de correlação calculados acima,
# MAGIC visualização das duas séries ao longo do tempo, evidenciando o
# MAGIC descompasso entre a tendência suave da Selic e a maior volatilidade
# MAGIC mensal dos pedidos de RJ.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT mes_referencia, selic_mensal_pct, rj_requeridas
# MAGIC FROM mvp_juros_rj.gold.fato_indicadores_mensais
# MAGIC ORDER BY mes_referencia;

# COMMAND ----------

# MAGIC %md
# MAGIC Dentro da janela de dados com metodologia consistente (jan/2024 a
# MAGIC abr/2026), a correlação entre a Selic mensal e os pedidos de RJ é
# MAGIC fraca em todos os cenários testados: sem defasagem (r de
# MAGIC aproximadamente 0,21), com defasagem de 1 mês (r de 0,01), 2 meses
# MAGIC (0,04), 3 meses (-0,01) e 6 meses (-0,22, na direção oposta à
# MAGIC esperada). Com apenas 28 observações, nenhum desses coeficientes chega
# MAGIC perto de ser estatisticamente significativo.
# MAGIC
# MAGIC Isso sugere que o efeito da Selic sobre RJ, se existir, não aparece
# MAGIC como uma resposta rápida mês a mês dentro de um período de 28 meses. A
# MAGIC próxima pergunta investiga se esse efeito aparece numa escala de tempo
# MAGIC mais longa.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Pergunta 2: Padrão histórico (2016-2024, dados de contexto)
# MAGIC
# MAGIC Esta análise usa a fato_contexto_anual, construída a partir de dados
# MAGIC institucionais anuais, na metodologia anterior à atualização de 2026
# MAGIC do indicador Serasa Experian. Ela foi mantida separada de propósito da
# MAGIC tabela mensal usada na Pergunta 1 (a justificativa está na seção de
# MAGIC Modelagem).

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   CASE
# MAGIC     WHEN ano BETWEEN 2016 AND 2018 THEN '1. Juros altos (2016-2018)'
# MAGIC     WHEN ano BETWEEN 2019 AND 2021 THEN '2. Juros baixos (2019-2021)'
# MAGIC     WHEN ano BETWEEN 2022 AND 2024 THEN '3. Juros altos (2022-2024)'
# MAGIC   END AS periodo,
# MAGIC   ROUND(AVG(pedidos_rj), 0)        AS media_pedidos_rj,
# MAGIC   ROUND(AVG(selic_media_anual), 2) AS selic_media
# MAGIC FROM mvp_juros_rj.gold.fato_contexto_anual
# MAGIC GROUP BY 1
# MAGIC ORDER BY 1;

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC **Visualização do padrão histórico**
# MAGIC
# MAGIC Gráfico combinando volume anual de pedidos de RJ (barras) e Selic média
# MAGIC anual (linha), 2016-2024, evidenciando visualmente o padrão cíclico em
# MAGIC "U" discutido na análise: RJ acompanha o movimento da Selic entre os
# MAGIC dois ciclos de alta (2016-2018 e 2022-2024) e o intervalo de juros
# MAGIC baixos entre eles (2019-2021).

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT ano, pedidos_rj, selic_media_anual
# MAGIC FROM mvp_juros_rj.gold.fato_contexto_anual
# MAGIC ORDER BY ano;

# COMMAND ----------

# MAGIC %md
# MAGIC **Resultado**: o padrão em três períodos revela um formato em "U". No
# MAGIC primeiro bloco de juros altos (2016-2018, Selic média de 10,21%), o
# MAGIC volume médio anual de RJ foi de 1.564. No período intermediário de
# MAGIC juros baixos (2019-2021, Selic média de 4,38%), essa média caiu para
# MAGIC 1.152. Já no bloco mais recente de juros altos (2022-2024, Selic média
# MAGIC de 12,16%), o volume voltou a subir, chegando a 1.504, um aumento de
# MAGIC 30,6% em relação ao período de juros baixos.
# MAGIC
# MAGIC Esse padrão cíclico, em que RJ sobe e desce acompanhando o mesmo
# MAGIC movimento da Selic, reforça a hipótese de que juros sustentadamente
# MAGIC elevados por vários anos acabam se refletindo em mais recuperações
# MAGIC judiciais. Não é possível afirmar causalidade com os dados disponíveis
# MAGIC (as limitações estão descritas no objetivo do projeto), mas o padrão é
# MAGIC consistente. Um detalhe importante: a resposta não é imediata. O ano
# MAGIC de 2022, mesmo já com Selic elevada em 12,43%, teve o menor volume de
# MAGIC RJ de toda a série, apenas 833 pedidos. O aumento expressivo só
# MAGIC aparece em 2023 e 2024, o que reforça a ideia de uma defasagem de 1 a
# MAGIC 2 anos entre o início do ciclo de alta e a resposta em RJ. O mesmo
# MAGIC parece valer no sentido inverso: a queda de RJ observada em 2019-2021
# MAGIC acontece depois da queda de juros que já vinha desde 2017.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Síntese geral
# MAGIC
# MAGIC As duas perguntas de negócio, analisadas em escalas de tempo
# MAGIC diferentes, contam histórias complementares. No curto prazo (mês a
# MAGIC mês, entre 2024 e 2026), não há evidência de correlação forte entre
# MAGIC Selic e RJ; os coeficientes calculados ficaram fracos ou próximos de
# MAGIC zero em todos os lags testados. Já no longo prazo (comparando três
# MAGIC períodos de três anos, de 2016 a 2024), aparece um padrão cíclico em
# MAGIC "U": RJ acompanha o movimento da Selic subindo, descendo e subindo de
# MAGIC novo, o que é consistente com a hipótese de um efeito acumulado de
# MAGIC juros elevados, com uma defasagem de 1 a 2 anos entre o início do
# MAGIC ciclo e a resposta em RJ.
# MAGIC
# MAGIC Esses dois resultados podem parecer contraditórios à primeira vista,
# MAGIC mas na verdade são o próprio achado deste projeto: se o efeito da
# MAGIC Selic sobre recuperações judiciais existe, ele parece operar numa
# MAGIC escala de tempo mais longa do que meses. Por isso não aparece num
# MAGIC teste de curto prazo, mesmo estando presente quando se compara ciclos
# MAGIC de vários anos.
# MAGIC
# MAGIC A principal limitação deste projeto é não conseguir testar essa
# MAGIC defasagem de longo prazo com o mesmo rigor estatístico usado na
# MAGIC análise mensal, já que a fonte de dados anual segue uma metodologia
# MAGIC diferente e tem granularidade mais grosseira. Um trabalho futuro
# MAGIC poderia buscar uma fonte de dados judiciais mais granular e de longo
# MAGIC prazo, como o CNJ/DataJud, e assim testar essa defasagem com mais
# MAGIC precisão, unificando as duas análises numa única série temporal
# MAGIC contínua.