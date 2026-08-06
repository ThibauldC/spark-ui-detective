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

Cases 0 and 1 are split into standalone scripts so each can be uploaded as its own Fabric Spark Job Definition. Cases 2–3 still accept a mode as a positional script argument; with no recognized mode, they run every mode in order.

| Script | Run |
|---|---|
| `case0_data_growth_regression/baseline.py` | 2024 October–December baseline |
| `case0_data_growth_regression/bad.py` | Full history with eight shuffle partitions |
| `case0_data_growth_regression/fixed.py` | Full history with at least 256 shuffle partitions |
| `case1_data_skew/bad.py` | Sort-merge join on the standard-rate hot key |
| `case1_data_skew/fixed.py` | Sort-merge join with a salted key |
| `case2_excessive_shuffle.py` | `bad`, `fixed`, `all` |
| `case3_poor_parallelism.py` | `bad`, `fixed`, `all` |

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

Broadcasting the tiny rule dimension is deliberately disabled: that would remove this join shuffle entirely and turn the demo into Case 2. Here the comparison isolates skew within a required shuffled join.

### Evidence

- Most join tasks finish while one task continues.
- One task reads and writes far more data than the median.
- Fabric History Server Diagnosis should flag data and time skew.
- The SQL plan contains exchanges and a sort-merge join on `fare_rule`.

### Fix

The fixed run adds one of 8,192 deterministic salts to every trip and replicates the eight-row rule dimension across those salts. Hashing thousands of salt values across 256 shuffle partitions balances the large side while preserving the same joined rows and output schema.

### Where to look

The sort-merge join stage, task duration and shuffle read distribution, SQL plan, and Diagnosis > Data Skew.

## Case 2: excessive shuffle

### Scenario

The pipeline enriches trips with pickup and drop-off boroughs. It builds a 70,225-row route dimension from the public 265-zone lookup. The bad run forces a sort-merge join, reproducing a missed broadcast caused by absent statistics or a disabled threshold.

### Evidence

- The bad SQL plan shows `SortMergeJoin`.
- Exchanges appear on both join inputs.
- The fact-side exchange moves the full trip history.
- Tasks should remain much more balanced than Case 1.

### Fix

The fixed run explicitly broadcasts the route dimension. The large-side exchange disappears and the plan uses a broadcast hash join.

### Where to look

SQL plan, DAG exchange boundaries, and stage shuffle read and write.

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
| 2 | Fixed plan removes the fact-side exchange and cuts join-stage time by at least 3× |
| 3 | One output task becomes 64 or more tasks and write time drops by at least 5× |

Demo outputs are written below `/lakehouse/default/Files/nyc_taxi/demo_outputs` and can be deleted after captures.
