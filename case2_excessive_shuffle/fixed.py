"""Case 2 fixed run: broadcast the small route dimension."""

import time

from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()

TRIP_TABLE = "nyc_yellow_trips"
ZONE_TABLE = "nyc_taxi_zones"
OUTPUT_PATH = "Files/nyc_taxi/demo_outputs/case2/fixed"
DEMO_YEARS = (2019, 2020, 2021, 2022, 2023, 2024)
SHUFFLE_PARTITIONS = max(256, spark.sparkContext.defaultParallelism * 4)

spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "false")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "false")
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
spark.conf.set("spark.sql.adaptive.autoBroadcastJoinThreshold", "-1")
spark.conf.set("spark.sql.shuffle.partitions", str(SHUFFLE_PARTITIONS))
spark.sparkContext.setJobDescription("CASE 2 FIXED: route enrichment join")

trips = (spark.table(TRIP_TABLE)
         .where(F.col("pickup_year").isin(*DEMO_YEARS))
         .select("PULocationID", "DOLocationID", "passenger_count", "trip_distance",
                 "fare_amount", "tip_amount", "tolls_amount", "total_amount")
         .where(F.col("PULocationID").isNotNull() & F.col("DOLocationID").isNotNull()))
zones = spark.table(ZONE_TABLE)
pickup = zones.select(
    F.col("LocationID").alias("PULocationID"),
    F.col("Borough").alias("pickup_borough"),
)
dropoff = zones.select(
    F.col("LocationID").alias("DOLocationID"),
    F.col("Borough").alias("dropoff_borough"),
)
routes = pickup.crossJoin(dropoff)
joined = trips.join(F.broadcast(routes), ["PULocationID", "DOLocationID"])
summary = (joined.groupBy("pickup_borough", "dropoff_borough")
           .agg(F.count("*").alias("trips"),
                F.sum("passenger_count").alias("passengers"),
                F.sum("fare_amount").alias("fares"),
                F.sum("tip_amount").alias("tips"),
                F.sum("tolls_amount").alias("tolls"),
                F.sum("total_amount").alias("revenue"),
                F.avg("trip_distance").alias("average_distance")))

started = time.perf_counter()
(summary.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
 .save(OUTPUT_PATH))
print(f"CASE 2 FIXED: {time.perf_counter() - started:.1f}s")
