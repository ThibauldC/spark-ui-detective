# Spark UI demo cases

These demos use official NYC Taxi and Limousine Commission Yellow Taxi records instead of generated `spark.range` data. The 2019–2024 corpus contains roughly 250 million trips. Exact counts change when TLC republishes files.

## Setup

1. Attach a default Lakehouse to the Fabric notebook or Spark Job Definition.
2. Run `ingest_nyc_taxi.py` once.
3. Allow several GB for the source Parquet files, normalized Delta table, and demo outputs.

The setup script downloads monthly files from:

```text
https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_YYYY-MM.parquet
```

It writes these normalized Delta paths:

```text
/lakehouse/default/Tables/nyc_yellow_trips
/lakehouse/default/Tables/nyc_taxi_zones
```

Do not include ingestion in recorded timings.

## Running the cases

Each scenario is a standalone script that can be uploaded as its own Fabric Spark Job Definition.

| Script | Run |
|---|---|
| `case0_data_growth_regression/baseline.py` | 2024 October–December baseline |
| `case0_data_growth_regression/bad.py` | Full history with eight shuffle partitions |
| `case0_data_growth_regression/fixed.py` | Full history with at least 256 shuffle partitions |
| `case1_data_skew/bad.py` | Sort-merge join on the standard-rate hot key |
| `case1_data_skew/fixed.py` | Sort-merge join with a salted key |
| `case2_executor_memory/bad.py` | Buffer entire partitions in executor Python memory (intentional failure) |
| `case2_executor_memory/fixed.py` | Stream the same partitions with bounded memory |
| `case3_poor_parallelism/bad.py` | One gzip CSV output task |
| `case3_poor_parallelism/fixed.py` | Parallel gzip CSV output |

Run each script as a separate Spark application when capturing the History Server. This avoids one application mixing the comparison and gives each run a clean SQL plan and timeline.

## Case 0: data growth and spill

### Scenario

A route-reporting pipeline deduplicates trips before calculating monthly route statistics. The baseline reads October through December 2024. The bad run reads the complete 2019–2024 history with the same eight shuffle partitions.

### Evidence

- One shuffle stage dominates the run.
- Task durations remain balanced.
- The bad run reports memory and disk spill.
- Shuffle read and write grow with the historical input.

### Fix

The fixed run processes the same full history with at least 256 shuffle partitions. It changes only the partition count.

### Where to look

Stages, stage task metrics, spill metrics, and the Executors tab.

## Case 1: standard-rate hot key

### Scenario

A fare extract is enriched with a pricing-rule description using a sort-merge join. Standard-rate trips share one `STANDARD` key, while exceptional fares use their rate code. Since standard fares dominate Yellow Taxi records, one join partition receives most rows.

Broadcasting the tiny rule dimension is deliberately disabled: that would remove this join shuffle entirely. Here the comparison isolates skew within a required shuffled join.

### Evidence

- Most join tasks finish while one task continues.
- One task reads and writes far more data than the median.
- Fabric History Server Diagnosis should flag data and time skew.
- The SQL plan contains exchanges and a sort-merge join on `fare_rule`.

### Fix

The fixed run adds one of 8,192 deterministic salts to every trip and replicates the eight-row rule dimension across those salts. Hashing thousands of salt values across 256 shuffle partitions balances the large side while preserving the same joined rows and output schema.

### Where to look

The sort-merge join stage, task duration and shuffle read distribution, SQL plan, and Diagnosis > Data Skew.

## Case 2: executor memory exhaustion — the partition-sized Python list

### Scenario

A Python data-quality profiler reports row counts and null counts for every column. It scans the real 2019–2024 taxi history, retaining all normalized columns. Eight round-robin partitions give each task roughly 30 million trips, without a hot business key or join.

The bad implementation first converts **every row in its partition into a Python dictionary and keeps them all in a list**. Only then does it calculate the profile. This pattern can pass a small-data test but exhaust memory on a historical backfill.

```python
# Bad: materialize an entire partition on the executor.
records = [row.asDict() for row in rows]

# Fixed: convert and process one row at a time.
records = (row.asDict() for row in rows)
```

This is executor-side `mapPartitions`, **not driver-side `collect()` or `toPandas()`**. Both versions write the same tiny report to Delta; neither collects the trips on the driver. An explicit output schema avoids running the profiler early for schema inference.

### Why a default Fabric pool can fail here

The previous `case2_logs_bad` capture used one eight-core executor with `spark.executor.memory=56g` and `spark.executor.memoryOverhead=384m`. These are observed settings from that application, not a promise about every default pool.

A Python dictionary plus its decoded values can occupy around a kilobyte per trip, depending on the Python version and values. Tens of millions of dictionaries can therefore require tens of GB **per task**, with multiple Python workers competing for the executor container's memory. Compressed Parquet size is not the in-memory size.

Spark SQL sorts and aggregations can spill managed state to disk. An ordinary Python list cannot. AQE cannot split this user-code list or make it spill. The demo disables AQE in both runs to keep the partition comparison explicit; it does not lower executor memory, change pools, add fake rows, allocate padding, or manufacture an exception.

### Run and calibrate on Fabric

**This deliberately risks killing executors and failing the application. Use a non-production workspace/capacity without other important work running. Rehearse and record it rather than relying on a live OOM.**

1. Attach the ingested Lakehouse. Keep the default pool and launch `case2_executor_memory/bad.py` as its own Spark application. The script prints the available executor memory/core settings before starting.
2. Start with all six years and `PARTITIONS = 8`. Capture failed attempts and the executor/container diagnostics. Stop the run once you have useful evidence if it keeps retrying; a successful bad run is not required.
3. If it completes, confirm it read the full corpus. Reduce `PARTITIONS` to 4, then 2, in **both** scripts and retry in a new application. Fewer partitions increase each list's size. Do not increase retry limits or shrink the pool to manufacture a failure.
4. Run `fixed.py` in a fresh application with exactly the same years, partition count, pool, and runtime. It should finish with the same report semantics and bounded profiler state.

The threshold and exact failure mode depend on executor placement, runtime, and capacity. These scripts have not yet been validated on Fabric; calibrate before promising a particular exception or failure count. With many large executors, more workers may run separately and the bad run may survive. Record the actual settings and outcome.

For a small successful comparison, temporarily filter both scripts to one source month before `repartition`. Compare their Delta reports, then restore the full-history input for the failure capture. A failed bad run produces no successful new report; an older output at that path is not evidence for the failed run.

### Evidence and where to look

- **Jobs / Stages:** the scan and round-robin exchange precede the Python profiling stage. Look for failed task attempts and retries in that stage. Retries repeat the same unbounded allocation. Completed fixed-run task record counts should be broadly balanced; failed-attempt counters can be partial or missing.
- **Executors, including dead executors:** lost executors and replacements if the container is killed. A Python-worker-only crash can fail tasks without killing the JVM executor.
- **Driver and executor stderr / Fabric application logs:** possible messages include `Python worker exited unexpectedly`, `MemoryError`, `ExecutorLostFailure`, or container exit code 137 with a memory-limit diagnostic. A worker crash or exit 137 alone is not proof of OOM; retain the accompanying memory diagnostic. Later fetch failures may be consequences of losing an executor's shuffle files.
- **Memory metrics:** Python RSS is outside the JVM heap. JVM GC time, Peak Execution Memory, and spill can stay low during the Python allocation. The Executors **Storage Memory** column measures cached blocks, not total process/container memory. Use process/container metrics when available and logs to establish the cause; do not promise a JVM GC spike.
- **SQL / DAG:** `Exchange RoundRobinPartitioning(8)` (or your calibrated count) explains the input distribution. The Python profiler is an RDD operation and is not fully represented by the final SQL aggregate plan. Use the stage DAG and task failures, not just the SQL tab.

The intended contrast is **Case 0: managed state spills; Case 1: one hot key; Case 2: balanced tasks retain unbounded Python state and fail**.

### Fix and verification

The only processing change is a list comprehension to a generator expression. Input, schema, partition count, shuffle, and pool stay the same. The profiler retains one dictionary at a time and one counter per column, rather than one dictionary per input row. Adding memory or partitions may postpone this bug; streaming removes it. For a production null-count report, native Spark SQL aggregates would usually be simpler and faster; the demo keeps the Python implementation to isolate the memory fix.

Run the small equivalence/streaming check locally (no Spark installation needed):

```bash
python3 case2_executor_memory/test_profile.py
```

After the fixed Fabric run, optionally verify its report against native Spark counts in an untimed notebook cell. Only the tiny aggregate results reach the driver:

```python
from pyspark.sql import functions as F

trips = spark.table("nyc_yellow_trips").where(
    F.col("pickup_year").isin(2019, 2020, 2021, 2022, 2023, 2024)
)  # Match the input filters used in your run.
expected = trips.agg(
    F.count("*").alias("__rows"),
    *[F.count(F.col(c)).alias(c) for c in trips.columns],
).first()
actual = spark.read.format("delta").load(
    "Files/nyc_taxi/demo_outputs/case2/fixed"
).collect()
assert len(actual) == len(trips.columns)
assert {r.column_name for r in actual} == set(trips.columns)
assert all(r.row_count == expected["__rows"] and
           r.null_count == expected["__rows"] - expected[r.column_name]
           for r in actual)
```

See Microsoft's [Fabric memory and executor failure troubleshooting guide](https://learn.microsoft.com/en-us/fabric/data-engineering/troubleshoot-spark-memory-performance). No resource configuration changes are needed here; if you do change executor settings during a separate experiment, use the Fabric Environment or first-cell `%%configure`, not runtime `spark.conf.set()`.

The existing Case 2 event logs, video, and slides still describe the retired broadcast-join demo. They are not evidence for this replacement; recapture them after a Fabric rehearsal.

## Case 3: poor parallelism

### Scenario

A consumer requests one gzip-compressed CSV. The bad run calls `coalesce(1)`, so one task formats and compresses all 2023–2024 records.

### Evidence

- The final stage contains one task.
- One executor remains busy while the others sit idle.
- The event timeline shows one long task.
- Executor Usage Analysis reports low utilization.

### Fix

The fixed run writes the same rows, columns, CSV format, and gzip compression with at least 64 tasks. The only contract change is that the dataset becomes a folder of part files.

A strict one-file requirement keeps the serial bottleneck. Spark cannot parallelize one gzip stream.

### Where to look

Stage task count, Executors, event timeline, and Diagnosis > Executor Usage Analysis.

## Calibration

Adjust the year or month constants near the top of each script if the Fabric capacity makes a case too short or too expensive. Change input periods before adding fake rows or artificial padding. Useful capture targets are:

| Case | Target signal |
|---|---|
| 0 | Bad run spills several GB and takes at least twice as long as fixed |
| 1 | Maximum task duration or input exceeds the median by at least 10× |
| 2 | Bad run has memory-related task failures/worker or executor loss; fixed completes on the same pool, input, and partition count |
| 3 | One output task becomes 64 or more tasks and write time drops by at least 5× |

Demo outputs are written below `/lakehouse/default/Files/nyc_taxi/demo_outputs` and can be deleted after captures.
