# The Spark Detective

A Microsoft Fabric talk and demo repo for diagnosing slow Apache Spark jobs with the Spark UI.

The repository contains:

- a [Slidev](https://sli.dev/) presentation in [`slidev/`](slidev/);
- four Fabric Spark performance investigations in [`case0_data_growth_regression/`](case0_data_growth_regression/), [`case1_data_skew/`](case1_data_skew/), [`case2_executor_memory/`](case2_executor_memory/), and [`case3_poor_parallelism/`](case3_poor_parallelism/);
- the NYC TLC Yellow Taxi ingestion script in [`ingest_nyc_taxi.py`](ingest_nyc_taxi.py).

## Prerequisites

### Slides

- Node.js 22 or newer
- npm

### Demo cases

- A Microsoft Fabric workspace with Spark enabled
- A default Lakehouse attached to the notebook or Spark Job Definition
- Enough Lakehouse storage for the 2019–2024 NYC TLC data, normalized Delta tables, and demo outputs
- Network access from Fabric to the NYC TLC download URLs

## Build and present the slide deck

```bash
cd slidev
npm ci
npm run dev
```

`npm run dev` starts the local Slidev server and opens the deck in a browser.

Build the static deck with:

```bash
npm run build
```

The static output is written to `slidev/dist/`. To build it for the repository's GitHub Pages URL:

```bash
npm run build -- --base /spark-ui-detective/
```

Export a PDF with:

```bash
npm run export
# or choose the output filename used by CI:
npm run export -- --output the-spark-detective.pdf
```

The GitHub Actions workflow deploys `slidev/dist/` to GitHub Pages on pushes to `main`. A tag matching `slides-v*` creates a downloadable PDF release. See [`slidev/README.md`](slidev/README.md) for the short Slidev-specific reference.

## Prepare and run the Fabric cases

The cases are intended to run as separate Fabric Spark applications so each History Server entry has a clean SQL plan, stage timeline, and task view. They are not local Python programs: upload each script as the main file of its own Fabric Spark Job Definition (or paste it into a Fabric Spark notebook).

### 1. Ingest the demo data

Attach the default Lakehouse, then run [`ingest_nyc_taxi.py`](ingest_nyc_taxi.py) once. It downloads the 2019–2024 Yellow Taxi files and writes:

- `/lakehouse/default/Tables/nyc_yellow_trips`
- `/lakehouse/default/Tables/nyc_taxi_zones`

Do not include ingestion in case timings. The source data is downloaded from the [NYC TLC trip data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) distribution URL and requires several GB of storage.

### 2. Run each case separately

For every run, attach the same default Lakehouse and submit the script as a separate Spark application. Run the bad and fixed versions independently, then open the application in the Fabric Spark History Server.

| Investigation | Bad run | Fixed run | Main clue |
| --- | --- | --- | --- |
| Data growth and spill | [`case0.../bad.py`](case0_data_growth_regression/bad.py) | [`case0.../fixed.py`](case0_data_growth_regression/fixed.py) | Too few shuffle partitions for the full history |
| Data skew | [`case1.../bad.py`](case1_data_skew/bad.py) | [`case1.../fixed.py`](case1_data_skew/fixed.py) | One hot join key creates a straggler task |
| Executor memory exhaustion | [`case2.../bad.py`](case2_executor_memory/bad.py) | [`case2.../fixed.py`](case2_executor_memory/fixed.py) | Partition-sized Python lists exhaust worker/container memory; streaming fixes it |
| Poor parallelism | [`case3.../bad.py`](case3_poor_parallelism/bad.py) | [`case3.../fixed.py`](case3_poor_parallelism/fixed.py) | `coalesce(1)` serializes a gzip CSV export |

Case 0 also has [`baseline.py`](case0_data_growth_regression/baseline.py), which processes only October–December 2024 for comparison with the full-history run.

**Case 2 is an intentional memory-failure demo.** Use a non-production Fabric application without important concurrent workloads. Start with the default pool, full history, and eight partitions; follow the calibration and failure-diagnosis instructions in [`CASES.md`](CASES.md). The replacement has not yet been validated on Fabric. Existing Case 2 slides, logs, and video cover the retired broadcast-join scenario and need a new capture.

In the History Server, inspect stages, task metrics, SQL plans, shuffle read/write, spill, executor activity, and the relevant Diagnosis view. The expected evidence and suggested timing targets are documented in [`CASES.md`](CASES.md).

All demo outputs are written below:

```text
/lakehouse/default/Files/nyc_taxi/demo_outputs
```

Delete that folder after a capture if the outputs are no longer needed. Adjust the year/month constants near the top of a case script to calibrate runtime for the available Fabric capacity; change input periods before adding artificial data.
