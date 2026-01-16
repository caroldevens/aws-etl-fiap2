import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql.functions import col, sum as _sum, count as _count, avg as _avg, year, month, dayofmonth
from awsglue.context import GlueContext
from awsglue.job import Job

# --- INICIALIZAÇÃO ---
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'REFINED_BUCKET_PATH', 'GLUE_CATALOG_DB_NAME', 'GLUE_CATALOG_TABLE_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# --- LEITURA DOS DADOS ---
# Lê os dados da zona Raw, usando as partições como colunas
input_dyf = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [args['s3_source_path']], "recurse": True},
    format="parquet",
    transformation_ctx="input_dyf"
)

# --- TRANSFORMAÇÕES OBRIGATÓRIAS ---

# Requisito 5-B: Renomear duas colunas existentes
renamed_dyf = RenameField.apply(frame=input_dyf, old_name="`Open`", new_name="abertura")
renamed_dyf = RenameField.apply(frame=renamed_dyf, old_name="`Close`", new_name="fechamento")

# Converte para DataFrame para usar funções do Spark SQL
spark_df = renamed_dyf.toDF()

# Requisito 5-C: Realizar um cálculo com base na data (Ex: variação diária)
# Garante que as colunas são do tipo double para o cálculo
spark_df = spark_df.withColumn("variacao_diaria", (col("fechamento") - col("abertura")) / col("abertura") * 100)

# Requisito 5-A: Agrupamento numérico, sumarização, contagem ou soma.
# Exemplo: Agregando por ticker e calculando o volume médio diário
aggregated_df = spark_df.groupBy("ticker").agg(
    _avg("Volume").alias("volume_medio")
)
# Nota: Esta agregação de exemplo reduz os dados a um único valor por ticker.
# Para um caso de uso real, você pode querer juntar isso de volta ou fazer a agregação de outra forma.
# Para este desafio, vamos usar o dataframe com a variação diária, que mantém a granularidade.

# --- ESCRITA DOS DADOS REFINADOS ---
# Converte de volta para DynamicFrame
output_dyf = DynamicFrame.fromDF(spark_df, glueContext, "output_dyf")

# Escreve os dados refinados no S3 em formato Parquet
glueContext.write_dynamic_frame.from_options(
    frame=output_dyf,
    connection_type="s3",
    connection_options={
        "path": args['REFINED_BUCKET_PATH'],
        "partitionKeys": ["ticker", "year", "month", "day"]
    },
    format="parquet",
    transformation_ctx="output_dyf"
)

# --- ATUALIZAÇÃO DO CATÁLOGO DE DADOS ---
# Requisito 7: Catalogar os dados automaticamente
# O S3 sink do Glue pode catalogar os dados automaticamente se a tabela já existir.
# Vamos garantir que a tabela seja criada/atualizada.
s3_sink = glueContext.getSink(
    connection_type="s3",
    path=args['REFINED_BUCKET_PATH'],
    enableUpdateCatalog=True,
    updateBehavior="UPDATE_IN_DATABASE",
    partitionKeys=["ticker", "year", "month", "day"]
)
s3_sink.setCatalogInfo(
    catalogDatabase=args['GLUE_CATALOG_DB_NAME'],
    catalogTableName=args['GLUE_CATALOG_TABLE_NAME']
)
s3_sink.setFormat("parquet")
s3_sink.writeFrame(output_dyf)


job.commit()
