from pyspark.sql import SparkSession
from pyspark.sql.functions import col, row_number, upper, trim, when, year, month, quarter, concat_ws, to_date, lit, lower,lpad
from pyspark.sql.functions import monotonically_increasing_id
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType
import unicodedata
import re
from pyspark.sql.functions import regexp_replace
from pyspark.sql.window import Window
import os
from dotenv import load_dotenv
load_dotenv()

server = os.getenv("DB_HOST")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
database_dw = os.getenv("DW_NAME")
database = os.getenv("DB_NAME")


spark = SparkSession.builder \
    .appName("DW_Credit") \
    .config("spark.jars", "/opt/airflow/jars/mssql-jdbc-13.4.0.jre11.jar") \
    .getOrCreate()

df = spark.read \
    .format("jdbc") \
    .option(
    "url",
    f"jdbc:sqlserver://{server}:1433;databaseName={database};encrypt=true;trustServerCertificate=true"
    ) \
    .option("dbtable", "stg_credit") \
    .option("user", os.getenv("DB_USER")) \
    .option("password", os.getenv("DB_PASSWORD")) \
    .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver") \
    .load()

df.show()
df_clean = df.dropna()

# 🔹 1. NORMALISATION de la colonne region
df_clean = df_clean.withColumn(
    "region_clean",
    upper(trim(col("region")))
)

# 🔹 2. SUPPRIMER les valeurs invalides
df_clean = df_clean.filter(
    col("region_clean").isNotNull() &
    (~col("region_clean").isin("TOTAL", "TOTAL NATIONAL")) &
    (~col("region_clean").rlike("^[0-9\\.]+$"))
)

# 🔹 3. CORRECTION des erreurs d'écriture (accents / variantes)
df_clean = df_clean.withColumn(
    "region_clean",
    regexp_replace("region_clean", "HOCEIMA", "HOCEÏMA")
)

df_clean = df_clean.withColumn(
    "region_clean",
    regexp_replace("region_clean", "KHENIFRA", "KHÉNIFRA")
)

df_clean = df_clean.withColumn(
    "region_clean",
    regexp_replace("region_clean", "BENI", "BÉNI")
)

df_clean = df_clean.withColumn(
    "region_clean",
    regexp_replace("region_clean", "FES", "FÈS")
)

# 🔹 4. LISTE OFFICIELLE DES RÉGIONS (filtrage final)
valid_regions = [
    "TANGER-TÉTOUAN-AL HOCEÏMA",
    "L'ORIENTAL",
    "FÈS-MEKNÈS",
    "RABAT-SALÉ-KÉNITRA",
    "BÉNI MELLAL-KHÉNIFRA",
    "CASABLANCA-SETTAT",
    "MARRAKECH-SAFI",
    "DRÂA-TAFILALET",
    "SOUSS-MASSA",
    "GUELMIM-OUED NOUN",
    "LAÂYOUNE-SAKIA EL HAMRA",
    "DAKHLA-OUED ED-DAHAB"
]

df_clean = df_clean.filter(col("region_clean").isin(valid_regions))

# 🔹 5. CRÉATION DIMENSION REGION
dim_region = df_clean.select("region_clean").dropDuplicates()

# 🔹 6. GÉNÉRATION CLÉ PRIMAIRE (PROPRE)
window_spec = Window.orderBy("region_clean")

dim_region = dim_region.withColumn(
    "RegionKey",
    row_number().over(window_spec)
)

# 🔹 7. ORDRE FINAL DES COLONNES
dim_region = dim_region.select(
    "RegionKey",
    col("region_clean").alias("region")
)




# Nettoyer mois AVANT mapping
df_clean = df_clean.withColumn("mois", lower(trim(col("mois"))))

df_clean = df_clean.withColumn("mois_num",
    when(col("mois") == "janvier", 1)
    .when(col("mois") == "février", 2)
    .when(col("mois") == "mars", 3)
    .when(col("mois") == "avril", 4)
    .when(col("mois") == "mai", 5)
    .when(col("mois") == "juin", 6)
    .when(col("mois") == "juillet", 7)
    .when(col("mois") == "août", 8)
    .when(col("mois") == "septembre", 9)
    .when(col("mois") == "octobre", 10)
    .when(col("mois") == "novembre", 11)
    .when(col("mois") == "décembre", 12)
)
df_clean = df_clean.filter(col("mois_num").isNotNull())
df_clean = df_clean.withColumn(
    "mois_num_str",
    lpad(col("mois_num").cast("string"), 2, "0")
)

df_clean = df_clean.withColumn(
    "date",
    to_date(
        concat_ws("-", col("annee"), col("mois_num_str"), lit("01")),
        "yyyy-MM-dd"
    )
)

df_clean = df_clean.withColumn("annee_calc", year("date")) \
                   .withColumn("mois_calc", month("date")) \
                   .withColumn("trimestre", quarter("date"))
dim_temps = df_clean.select(
    col("date"),
    col("annee_calc").alias("annee"),
    col("mois_calc").alias("mois"),
    col("trimestre")
).dropDuplicates()



dim_temps = dim_temps.withColumn("DateKey", monotonically_increasing_id())

dim_genre = df_clean.select("genre").dropDuplicates()

dim_genre = dim_genre.withColumn("GenreKey", monotonically_increasing_id())

dim_region = df_clean.select("region_clean").dropDuplicates()

dim_region = dim_region.withColumn("RegionKey", monotonically_increasing_id())

dim_credit = df_clean.select("type_credit").dropDuplicates()

dim_credit = dim_credit.withColumn("CreditKey", monotonically_increasing_id())

fact = df_clean \
    .join(dim_temps, ["date"]) \
    .join(dim_genre, ["genre"]) \
    .join(dim_region, df_clean["region_clean"] == dim_region["region_clean"]) \
    .join(dim_credit, ["type_credit"])

fact_credit = fact.select(
    "DateKey",
    "GenreKey",
    "RegionKey",
    "CreditKey",
    col("nb_menages"),
    col("montant_mdhs")
)

url = f"jdbc:sqlserver://{server}:1433;databaseName={database_dw};encrypt=true;trustServerCertificate=true"

properties = {
    "user": user,
    "password": password,
    "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver"
}

dim_temps.write.jdbc(url=url, table="DimTemps", mode="overwrite", properties=properties)

dim_genre.write.jdbc(url=url, table="DimGenre", mode="overwrite", properties=properties)

dim_region.write.jdbc(url=url, table="DimRegion", mode="overwrite", properties=properties)

dim_credit.write.jdbc(url=url, table="DimTypeCredit", mode="overwrite", properties=properties)
fact_credit.write.jdbc(url=url, table="FactCredit", mode="overwrite", properties=properties)
spark.stop()
