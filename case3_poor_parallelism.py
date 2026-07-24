"""Case 3: a single gzip CSV leaves the Fabric Spark pool idle."""

import sys
import time

from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()

TRIP_TABLE = "/lakehouse/default/Tables/nyc_yellow_trips"
OUTPUT_ROOT = "/lakehouse/default/Files/nyc_taxi/demo_outputs/case3"
DEMO_YEARS = (2023, 2024)
OUTPUT_PARTITIONS = max(64, spark.sparkContext.defaultParallelism * 2)
VALID_MODES = {"bad", "fixed", "all"}
MODE = next((arg.lower() for arg in sys.argv[1:] if arg.lower() in VALID_MODES), "all")


def export_rows():
    return (spark.read.format("delta").load(TRIP_TABLE)
            .where(F.col("pickup_year").isin(*DEMO_YEARS))
            .where(F.col("tpep_pickup_datetime").isNotNull())
            .select(
                F.col("VendorID").alias("vendor_id"),
                F.date_format("tpep_pickup_datetime", "yyyy-MM-dd HH:mm:ss").alias("pickup_at"),
                F.date_format("tpep_dropoff_datetime", "yyyy-MM-dd HH:mm:ss").alias("dropoff_at"),
                F.col("PULocationID").alias("pickup_location_id"),
                F.col("DOLocationID").alias("dropoff_location_id"),
                "passenger_count", "trip_distance", "fare_amount", "tip_amount", "total_amount",
            ))


def run(label, output_partitions):
    spark.conf.set("spark.sql.shuffle.partitions", str(output_partitions))
    spark.sparkContext.setJobDescription(f"CASE 3 {label}: gzip CSV export")

    rows = export_rows()
    rows = rows.coalesce(1) if output_partitions == 1 else rows.repartition(output_partitions)

    started = time.perf_counter()
    (rows.write.mode("overwrite").option("header", "true").option("compression", "gzip")
     .csv(f"{OUTPUT_ROOT}/{label.lower()}"))
    print(f"CASE 3 {label}: {time.perf_counter() - started:.1f}s, {output_partitions} output task(s)")


if __name__ == "__main__":
    if MODE in {"bad", "all"}:
        run("BAD", output_partitions=1)
    if MODE in {"fixed", "all"}:
        run("FIXED", output_partitions=OUTPUT_PARTITIONS)
