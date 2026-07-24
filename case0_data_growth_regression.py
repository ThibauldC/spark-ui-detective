"""Case 0: unchanged deduplication starts spilling after the taxi history grows."""

import sys
import time

from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()

TRIP_TABLE = "/lakehouse/default/Tables/nyc_yellow_trips"
OUTPUT_ROOT = "/lakehouse/default/Files/nyc_taxi/demo_outputs/case0"
BAD_SHUFFLE_PARTITIONS = 8
FIXED_SHUFFLE_PARTITIONS = max(256, spark.sparkContext.defaultParallelism * 4)
VALID_MODES = {"baseline", "bad", "fixed", "all"}
MODE = next((arg.lower() for arg in sys.argv[1:] if arg.lower() in VALID_MODES), "all")


def run(label, full_history, shuffle_partitions):
    spark.conf.set("spark.sql.adaptive.enabled", "true")
    spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "false")
    spark.conf.set("spark.sql.shuffle.partitions", str(shuffle_partitions))
    spark.sparkContext.setJobDescription(f"CASE 0 {label}: data growth and spill")

    trips = spark.read.format("delta").load(TRIP_TABLE)
    if not full_history:
        trips = trips.where((F.col("pickup_year") == 2024) & F.col("pickup_month").between(10, 12))

    trips = (trips
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
     .save(f"{OUTPUT_ROOT}/{label.lower()}"))
    print(f"CASE 0 {label}: {time.perf_counter() - started:.1f}s, {shuffle_partitions} shuffle partitions")


if __name__ == "__main__":
    if MODE in {"baseline", "all"}:
        run("BASELINE", full_history=False, shuffle_partitions=BAD_SHUFFLE_PARTITIONS)
    if MODE in {"bad", "all"}:
        run("BAD", full_history=True, shuffle_partitions=BAD_SHUFFLE_PARTITIONS)
    if MODE in {"fixed", "all"}:
        run("FIXED", full_history=True, shuffle_partitions=FIXED_SHUFFLE_PARTITIONS)
