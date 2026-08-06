"""Case 1 bad run: a hot join key creates one straggler task."""

import time

from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()

TRIP_TABLE = "nyc_yellow_trips"
OUTPUT_PATH = "Files/nyc_taxi/demo_outputs/case1/bad"
DEMO_YEARS = (2022, 2023, 2024)
SHUFFLE_PARTITIONS = 256

spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "false")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "false")
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
spark.conf.set("spark.sql.adaptive.autoBroadcastJoinThreshold", "-1")
spark.conf.set("spark.sql.shuffle.partitions", str(SHUFFLE_PARTITIONS))
spark.sparkContext.setJobDescription("CASE 1 BAD: standard-rate hot join key")

trips = (spark.table(TRIP_TABLE)
         .where(F.col("pickup_year").isin(*DEMO_YEARS))
         .where(F.col("tpep_pickup_datetime").isNotNull())
         .select("VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime",
                 "PULocationID", "DOLocationID", "RatecodeID", "payment_type",
                 "fare_amount", "tip_amount", "total_amount"))

fare_rule = F.when(F.col("RatecodeID") == 1, F.lit("STANDARD")).otherwise(
    F.concat(F.lit("SPECIAL:"),
             F.coalesce(F.col("RatecodeID").cast("string"), F.lit("UNKNOWN")))
)
extract = trips.withColumn("fare_rule", fare_rule)
rules = spark.createDataFrame([
    ("STANDARD", "Standard rate"),
    ("SPECIAL:2", "JFK"),
    ("SPECIAL:3", "Newark"),
    ("SPECIAL:4", "Nassau or Westchester"),
    ("SPECIAL:5", "Negotiated fare"),
    ("SPECIAL:6", "Group ride"),
    ("SPECIAL:99", "Other"),
    ("SPECIAL:UNKNOWN", "Unknown"),
], ["fare_rule", "rule_description"])

enriched = extract.hint("merge").join(rules.hint("merge"), "fare_rule", "left")

started = time.perf_counter()
(enriched.write.mode("overwrite").option("compression", "snappy").parquet(OUTPUT_PATH))
print(f"CASE 1 BAD: {time.perf_counter() - started:.1f}s")
