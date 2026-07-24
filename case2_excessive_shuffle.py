"""Case 2: a small route dimension is shuffled instead of broadcast."""

import sys
import time

from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()

TRIP_TABLE = "/lakehouse/default/Tables/nyc_yellow_trips"
ZONE_TABLE = "/lakehouse/default/Tables/nyc_taxi_zones"
OUTPUT_ROOT = "/lakehouse/default/Files/nyc_taxi/demo_outputs/case2"
DEMO_YEARS = (2019, 2020, 2021, 2022, 2023, 2024)
SHUFFLE_PARTITIONS = max(256, spark.sparkContext.defaultParallelism * 4)
VALID_MODES = {"bad", "fixed", "all"}
MODE = next((arg.lower() for arg in sys.argv[1:] if arg.lower() in VALID_MODES), "all")


def route_dimension():
    zones = spark.read.format("delta").load(ZONE_TABLE)
    pickup = zones.select(
        F.col("LocationID").alias("PULocationID"),
        F.col("Borough").alias("pickup_borough"),
    )
    dropoff = zones.select(
        F.col("LocationID").alias("DOLocationID"),
        F.col("Borough").alias("dropoff_borough"),
    )
    return pickup.crossJoin(dropoff)


def run(label, broadcast_routes):
    spark.conf.set("spark.sql.adaptive.enabled", "true")
    spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "false")
    spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "false")
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
    spark.conf.set("spark.sql.adaptive.autoBroadcastJoinThreshold", "-1")
    spark.conf.set("spark.sql.shuffle.partitions", str(SHUFFLE_PARTITIONS))
    spark.sparkContext.setJobDescription(f"CASE 2 {label}: route enrichment join")

    trips = (spark.read.format("delta").load(TRIP_TABLE)
             .where(F.col("pickup_year").isin(*DEMO_YEARS))
             .select("PULocationID", "DOLocationID", "passenger_count", "trip_distance",
                     "fare_amount", "tip_amount", "tolls_amount", "total_amount")
             .where(F.col("PULocationID").isNotNull() & F.col("DOLocationID").isNotNull()))
    routes = route_dimension()

    if broadcast_routes:
        joined = trips.join(F.broadcast(routes), ["PULocationID", "DOLocationID"])
    else:
        joined = trips.hint("merge").join(routes.hint("merge"), ["PULocationID", "DOLocationID"])

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
     .save(f"{OUTPUT_ROOT}/{label.lower()}"))
    print(f"CASE 2 {label}: {time.perf_counter() - started:.1f}s")


if __name__ == "__main__":
    if MODE in {"bad", "all"}:
        run("BAD", broadcast_routes=False)
    if MODE in {"fixed", "all"}:
        run("FIXED", broadcast_routes=True)
