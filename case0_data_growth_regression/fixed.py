"""Case 0 fixed run: full taxi history with enough shuffle partitions."""

import time

from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()

TRIP_TABLE = "nyc_yellow_trips"
OUTPUT_PATH = "Files/nyc_taxi/demo_outputs/case0"
SHUFFLE_PARTITIONS = max(256, spark.sparkContext.defaultParallelism * 4)

spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "false")
spark.conf.set("spark.sql.shuffle.partitions", str(SHUFFLE_PARTITIONS))
spark.sparkContext.setJobDescription("CASE 0 FIXED: data growth and spill")

trips = (spark.table(TRIP_TABLE)
         .where(F.col("tpep_pickup_datetime").isNotNull()
                & F.col("PULocationID").isNotNull()
                & F.col("DOLocationID").isNotNull())
         .select("VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime",
                 "PULocationID", "DOLocationID", "passenger_count", "trip_distance",
                 "fare_amount", "tip_amount", "total_amount", "pickup_year", "pickup_month"))

deduplicated = trips.dropDuplicates([
    "VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime",
    "PULocationID", "DOLocationID", "total_amount",
])
summary = (deduplicated.groupBy("pickup_year", "pickup_month", "PULocationID", "DOLocationID")
           .agg(F.count("*").alias("trips"),
                F.sum("total_amount").alias("revenue"),
                F.avg("trip_distance").alias("average_distance")))

started = time.perf_counter()
(summary.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
 .save(OUTPUT_PATH))
print(f"CASE 0 FIXED: {time.perf_counter() - started:.1f}s, {SHUFFLE_PARTITIONS} shuffle partitions")
