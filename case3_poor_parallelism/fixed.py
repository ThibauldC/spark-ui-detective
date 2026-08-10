"""Case 3 fixed run: write gzip CSV output in parallel."""

import time

from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()

TRIP_TABLE = "nyc_yellow_trips"
OUTPUT_PATH = "Files/nyc_taxi/demo_outputs/case3/fixed"
DEMO_YEARS = (2023, 2024)
OUTPUT_PARTITIONS = max(64, spark.sparkContext.defaultParallelism * 2)

spark.conf.set("spark.sql.shuffle.partitions", str(OUTPUT_PARTITIONS))
spark.sparkContext.setJobDescription("CASE 3 FIXED: gzip CSV export")

rows = (
    spark.table(TRIP_TABLE)
    .where(F.col("pickup_year").isin(*DEMO_YEARS))
    .where(F.col("tpep_pickup_datetime").isNotNull())
    .select(
        F.col("VendorID").alias("vendor_id"),
        F.date_format("tpep_pickup_datetime", "yyyy-MM-dd HH:mm:ss").alias("pickup_at"),
        F.date_format("tpep_dropoff_datetime", "yyyy-MM-dd HH:mm:ss").alias(
            "dropoff_at"
        ),
        F.col("PULocationID").alias("pickup_location_id"),
        F.col("DOLocationID").alias("dropoff_location_id"),
        "passenger_count",
        "trip_distance",
        "fare_amount",
        "tip_amount",
        "total_amount",
    )
    .repartition(OUTPUT_PARTITIONS)
)

started = time.perf_counter()
(
    rows.write.mode("overwrite")
    .option("header", "true")
    .option("compression", "gzip")
    .csv(OUTPUT_PATH)
)
print(
    f"CASE 3 FIXED: {time.perf_counter() - started:.1f}s, {OUTPUT_PARTITIONS} output tasks"
)
