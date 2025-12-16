from pyspark.sql import SparkSession

spark = SparkSession.builder.remote("sc://localhost:15002").getOrCreate()
df = spark.createDataFrame([("2022-11-12",)], ["ts"])
print(df.toPandas())
