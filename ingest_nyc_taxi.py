"""Download NYC TLC Yellow Taxi data and normalize it in the default Fabric Lakehouse.

Attach a default Lakehouse before running this script. The download is untimed demo setup.
"""

from concurrent.futures import ThreadPoolExecutor
from functools import reduce
from pathlib import Path
from shutil import copyfileobj
from urllib.request import urlopen

from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()

YEARS = range(2019, 2025)
MONTHS = range(1, 13)
DOWNLOAD_WORKERS = 4
LAKEHOUSE = Path("/lakehouse/default")
RAW_DIR = LAKEHOUSE / "Files/nyc_taxi/raw"
TRIP_TABLE = LAKEHOUSE / "Tables/nyc_yellow_trips"
ZONE_TABLE = LAKEHOUSE / "Tables/nyc_taxi_zones"
TRIP_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet"
ZONE_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

COLUMN_TYPES = (
    ("VendorID", "int"),
    ("tpep_pickup_datetime", "timestamp"),
    ("tpep_dropoff_datetime", "timestamp"),
    ("passenger_count", "int"),
    ("trip_distance", "double"),
    ("RatecodeID", "int"),
    ("store_and_fwd_flag", "string"),
    ("PULocationID", "int"),
    ("DOLocationID", "int"),
    ("payment_type", "int"),
    ("fare_amount", "double"),
    ("extra", "double"),
    ("mta_tax", "double"),
    ("tip_amount", "double"),
    ("tolls_amount", "double"),
    ("improvement_surcharge", "double"),
    ("total_amount", "double"),
    ("congestion_surcharge", "double"),
    ("airport_fee", "double"),
)


def download(item):
    url, destination = item
    if destination.exists() and destination.stat().st_size:
        return destination

    temporary = destination.with_name(destination.name + ".part")
    temporary.unlink(missing_ok=True)
    print(f"Downloading {url}")
    try:
        with urlopen(url, timeout=120) as source, temporary.open("wb") as target:
            expected_size = int(source.headers.get("Content-Length", 0))
            copyfileobj(source, target, length=1024 * 1024)
        if expected_size and temporary.stat().st_size != expected_size:
            raise IOError(f"Incomplete download: {destination.name}")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def normalized_trip(path, year, month):
    source = spark.read.parquet(str(path))
    names = {name.lower(): name for name in source.columns}
    columns = []
    for name, data_type in COLUMN_TYPES:
        actual_name = names.get(name.lower())
        value = F.col(actual_name) if actual_name else F.lit(None)
        columns.append(value.cast(data_type).alias(name))
    return source.select(*columns).withColumn("pickup_year", F.lit(year)).withColumn("pickup_month", F.lit(month))


if __name__ == "__main__":
    if not (LAKEHOUSE / "Files").exists():
        raise RuntimeError("Attach a default Fabric Lakehouse before running this script")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    trip_files = [
        (year, month, RAW_DIR / f"yellow_tripdata_{year}-{month:02d}.parquet")
        for year in YEARS
        for month in MONTHS
    ]
    downloads = [
        (TRIP_URL.format(year=year, month=month), path)
        for year, month, path in trip_files
    ] + [(ZONE_URL, RAW_DIR / "taxi_zone_lookup.csv")]

    with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as pool:
        list(pool.map(download, downloads))

    assert len(trip_files) == 72 and all(path.stat().st_size for _, _, path in trip_files)

    frames = [normalized_trip(path, year, month) for year, month, path in trip_files]
    trips = reduce(lambda left, right: left.unionByName(right), frames)
    (trips.write.format("delta")
     .mode("overwrite")
     .option("overwriteSchema", "true")
     .partitionBy("pickup_year", "pickup_month")
     .save(str(TRIP_TABLE)))

    zones = (spark.read.option("header", "true").csv(str(RAW_DIR / "taxi_zone_lookup.csv"))
             .select(F.col("LocationID").cast("int").alias("LocationID"),
                     F.col("Borough"), F.col("Zone"), F.col("service_zone")))
    assert zones.count() == 265
    zones.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(str(ZONE_TABLE))

    print(f"Trips: {TRIP_TABLE}")
    print(f"Zones: {ZONE_TABLE}")
