"""Case 2 bad run: buffer whole partitions in executor Python workers.

Intentional memory-failure demo. Use an isolated Fabric application, not production.
"""

import time

TRIP_TABLE = "nyc_yellow_trips"
OUTPUT_PATH = "Files/nyc_taxi/demo_outputs/case2/bad"
DEMO_YEARS = (2019, 2020, 2021, 2022, 2023, 2024)
PARTITIONS = 8  # Keep identical in bad/fixed; try 4, then 2 if bad survives.


def profile_partition(rows):
    # The bug: Python dictionaries for the entire partition cannot spill to disk.
    records = [row.asDict() for row in rows]
    total = 0
    nulls = {}
    for record in records:
        total += 1
        for column, value in record.items():
            nulls[column] = nulls.get(column, 0) + (value is None)
    for column, missing in nulls.items():
        yield column, total, missing


def main():
    from pyspark.sql import SparkSession, functions as F

    spark = SparkSession.builder.getOrCreate()
    spark.conf.set("spark.sql.adaptive.enabled", "false")
    spark.conf.set("spark.sql.shuffle.partitions", str(PARTITIONS))
    spark.sparkContext.setJobDescription("CASE 2 BAD: unbounded Python partition profiling")
    conf = spark.sparkContext.getConf()
    print({key: conf.get(key, "<runtime default>") for key in (
        "spark.executor.memory", "spark.executor.memoryOverhead",
        "spark.executor.cores", "spark.executor.pyspark.memory",
    )}, flush=True)

    trips = (spark.table(TRIP_TABLE)
             .where(F.col("pickup_year").isin(*DEMO_YEARS))
             .repartition(PARTITIONS))  # Round-robin, not a hot business key.
    started = time.perf_counter()
    partials = spark.createDataFrame(
        trips.rdd.mapPartitions(profile_partition),
        "column_name string, row_count long, null_count long",
    )  # Explicit schema: no driver-side schema-inference action.
    summary = (partials.groupBy("column_name")
               .agg(F.sum("row_count").alias("row_count"),
                    F.sum("null_count").alias("null_count")))
    (summary.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
     .save(OUTPUT_PATH))  # Action must consume the profile, not merely count input rows.
    print(f"CASE 2 BAD: {time.perf_counter() - started:.1f}s, {PARTITIONS} profiling tasks")


if __name__ == "__main__":
    main()
