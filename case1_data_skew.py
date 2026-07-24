"""Case 1: the dominant standard-rate fare rule creates one straggler task."""

import sys
import time

from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()

TRIP_TABLE = "/lakehouse/default/Tables/nyc_yellow_trips"
OUTPUT_ROOT = "/lakehouse/default/Files/nyc_taxi/demo_outputs/case1"
DEMO_YEARS = (2022, 2023, 2024)
SHUFFLE_PARTITIONS = max(200, spark.sparkContext.defaultParallelism * 2)
STANDARD_RATE_BUCKETS = 32
VALID_MODES = {"bad", "fixed", "all"}
MODE = next((arg.lower() for arg in sys.argv[1:] if arg.lower() in VALID_MODES), "all")


def fare_extract():
    trips = (spark.read.format("delta").load(TRIP_TABLE)
             .where(F.col("pickup_year").isin(*DEMO_YEARS))
             .where(F.col("tpep_pickup_datetime").isNotNull())
             .select("VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime",
                     "PULocationID", "DOLocationID", "RatecodeID", "payment_type",
                     "fare_amount", "tip_amount", "total_amount"))

    special_rule = F.concat(
        F.lit("SPECIAL:"), F.coalesce(F.col("RatecodeID").cast("string"), F.lit("UNKNOWN")),
        F.lit(":"), F.coalesce(F.col("PULocationID").cast("string"), F.lit("UNKNOWN")),
        F.lit(":"), F.coalesce(F.col("DOLocationID").cast("string"), F.lit("UNKNOWN")),
    )
    return trips.withColumn(
        "fare_rule", F.when(F.col("RatecodeID") == 1, F.lit("STANDARD")).otherwise(special_rule)
    )


def write_extract(label, salted):
    spark.conf.set("spark.sql.adaptive.enabled", "true")
    spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "false")
    spark.conf.set("spark.sql.shuffle.partitions", str(SHUFFLE_PARTITIONS))
    spark.sparkContext.setJobDescription(f"CASE 1 {label}: standard-rate hot key")

    extract = fare_extract()
    if salted:
        extract = extract.withColumn(
            "salt",
            F.when(
                F.col("fare_rule") == "STANDARD",
                F.pmod(F.xxhash64("tpep_pickup_datetime", "VendorID", "PULocationID", "DOLocationID"),
                       F.lit(STANDARD_RATE_BUCKETS)),
            ).otherwise(F.lit(0)),
        )
        extract = extract.repartition(SHUFFLE_PARTITIONS, "fare_rule", "salt").drop("salt")
    else:
        extract = extract.repartition(SHUFFLE_PARTITIONS, "fare_rule")

    started = time.perf_counter()
    (extract.write.mode("overwrite").option("compression", "snappy")
     .partitionBy("fare_rule").parquet(f"{OUTPUT_ROOT}/{label.lower()}"))
    print(f"CASE 1 {label}: {time.perf_counter() - started:.1f}s")


if __name__ == "__main__":
    if MODE in {"bad", "all"}:
        write_extract("BAD", salted=False)
    if MODE in {"fixed", "all"}:
        write_extract("FIXED", salted=True)
