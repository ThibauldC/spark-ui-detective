---
theme: light-icons
title: The Spark Detective
info: |
  The Spark Detective: Diagnosing Spark Performance in Microsoft Fabric.
class: text-left
drawings:
  persist: false
transition: slide-left
mdc: true
---

# The Spark detective

## The curious case of the slow Spark job: a detective's toolbox

<div class="title-visual mt-10">
  <img src="./images/spark_ui_fabric.png" alt="Microsoft Fabric Spark UI" class="title-visual-ui" />
  <img src="./images/crime-scene-tape.png" alt="Crime scene tape" class="title-visual-tape" />
</div>

<style>
.title-visual {
  position: relative;
  width: 94%;
  margin-inline: auto;
}
.title-visual-ui {
  display: block;
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 1rem;
  box-shadow: 0 0.75rem 1.5rem rgb(15 23 42 / 0.15);
}
.title-visual-tape {
  position: absolute;
  top: 20%;
  left: 30%;
  z-index: 1;
  width: 42%;
  transform: rotate(-8deg);
  filter: drop-shadow(0 0.35rem 0.25rem rgb(15 23 42 / 0.25));
}
</style>

<!--
This is a practical investigation, not a Spark UI tour.
Set expectations that the first part of the talk covers the mystery and the mental model needed to read Spark UI evidence.
-->

---

# The Mystery

> The notebook finished yesterday in **12 minutes**. Today it runs for **55 minutes**.
>
> Nothing obvious changed. Where do we look?

<div class="mt-24 grid grid-cols-3 gap-4 text-center">
  <div class="metric-card">
    <div class="metric">12m</div>
    <div class="label">Yesterday</div>
  </div>
  <div class="metric-card suspect">
    <div class="metric">55m</div>
    <div class="label">Today</div>
  </div>
  <div class="metric-card">
    <div class="metric">?</div>
    <div class="label">Root cause</div>
  </div>
</div>

<img src="./images/detective.jpg" class="absolute top-6 right-6 w-36 rounded-xl shadow-lg" />

<style>
blockquote {
  max-width: calc(100% - 11rem);
}
</style>

<!--
Use this slide to create tension. Do not explain the answer yet.
Emphasize that Spark performance problems often do not fail loudly; they leave clues in runtime, stages, tasks, shuffle, spill, and executor behavior.
The audience should feel the common pain: same notebook, same code, very different runtime.
-->

---
hide:true
---

# We Are Not Memorizing Tabs

<div class="grid grid-cols-2 gap-8 mt-10">
<div class="rounded-2xl bg-red-50 p-6 border border-red-100">

## Avoid

- Opening random Spark UI tabs
- Changing tuning knobs first
- Treating every slow job as CPU-bound
- Stopping at job-level progress

</div>
<div class="rounded-2xl bg-emerald-50 p-6 border border-emerald-100">

## Do Instead

- Start from the right run
- Move from symptom to evidence
- Localize the expensive stage
- Build a testable hypothesis

</div>
</div>

<div class="mt-10 text-2xl font-semibold text-center">
We are here to learn <span class="text-emerald-700">where to look first</span>.
</div>

<!--
Make the main promise of the talk explicit: a repeatable debugging workflow.
This slide prevents the talk from becoming a feature tour of Spark UI.
The key contrast is random tuning versus evidence-driven diagnosis.
-->

---
zoom: 0.85
---

# Spark architecture: driver to workers

<div class="mental-eyebrow text-blue-700">A hierarchy of coordination, execution, and data movement</div>

<div class="architecture-topology">
  <div class="notebook-card">
    <div class="architecture-label">NOTEBOOK / APPLICATION</div>
    <div class="notebook-row">
      <span class="notebook-mark">▤</span>
      <b>groupBy("zone").count()</b>
    </div>
    <span class="notebook-caption">An action plugs into the driver.</span>
  </div>

  <div class="topology-arrow">→ <span>submit</span></div>

  <div class="architecture-driver">
    <div class="driver-kicker">DRIVER NODE</div>
    <div class="driver-title">Application coordinator</div>
    <div class="driver-copy">Plans the work, schedules it, and tracks progress.</div>
    <div class="driver-note">The driver coordinates; executors process the data.</div>
  </div>
</div>

<div class="driver-branch"><span>schedule work to the cluster</span></div>

<div class="workers-area">
  <div class="workers-heading">
    <b>WORKER NODES</b>
    <span>three shown · more can be added</span>
  </div>

  <div class="worker-grid">
    <div class="worker-node">
      <div class="worker-heading">
        <span class="worker-icon"><i></i><i></i><i></i><i></i></span>
        <span><b>Worker 1</b><small>node-01</small></span>
      </div>
      <div class="executor-box">
        <div class="executor-heading"><b>EXECUTOR</b><span>parallel slots</span></div>
        <div class="slot-strip"><i></i><i></i><i></i><i></i></div>
      </div>
      <div class="worker-caption">runs partitions</div>
    </div>
    <div class="worker-node">
      <div class="worker-heading">
        <span class="worker-icon"><i></i><i></i><i></i><i></i></span>
        <span><b>Worker 2</b><small>node-02</small></span>
      </div>
      <div class="executor-box">
        <div class="executor-heading"><b>EXECUTOR</b><span>parallel slots</span></div>
        <div class="slot-strip"><i></i><i></i><i></i><i></i></div>
      </div>
      <div class="worker-caption">runs partitions</div>
    </div>
    <div class="worker-node">
      <div class="worker-heading">
        <span class="worker-icon"><i></i><i></i><i></i><i></i></span>
        <span><b>Worker 3</b><small>node-03</small></span>
      </div>
      <div class="executor-box">
        <div class="executor-heading"><b>EXECUTOR</b><span>parallel slots</span></div>
        <div class="slot-strip"><i></i><i></i><i></i><i></i></div>
      </div>
      <div class="worker-caption">runs partitions</div>
    </div>
  </div>

  <div class="shuffle-lane">
    <span class="shuffle-word">SHUFFLE (wide transformation)</span>
    <span class="shuffle-arrows">↔ &nbsp; ↔ &nbsp; ↔</span>
    <span class="shuffle-caption">data crosses worker boundaries before the next phase</span>
  </div>
</div>

<!--
Spark cluster

The Spark cluster is created as follows: 1 driver, 1 or more workers or nodes

Start on the left: the notebook submits an action to the driver. The driver is the coordinator. It plans the work, schedules it, and tracks progress; it is not where all the rows are processed. Notebook asks SparkSession this is a driver process. SparkSession manages Spark application (1-to-1 relation)

The driver fans work out to multiple worker nodes. Each worker hosts an executor with several parallel slots, so partitions can be processed at the same time. More workers mean more possible parallelism.

The shuffle is the important exception to the simple fan-out picture: records cross worker boundaries so that equal keys meet before the next phase. That data movement is why a shuffle becomes a stage boundary in the Spark UI. Shuffles are triggered by something called wide transformations. Wide vs narrow transformation (will not go further into this)

Narrow: transformations for which each input partition will contribute to only one output partition (filter)
Wide: input partitions will contribute to many output partitions
-->

<style>
.architecture-topology {
  display: grid;
  grid-template-columns: 18rem 2.5rem minmax(0, 1fr);
  gap: 0.8rem;
  align-items: stretch;
  margin-top: 0.8rem;
}
.notebook-card,
.architecture-driver {
  min-height: 8rem;
  border: 1px solid #cbd5e1;
  border-radius: 1rem;
  background: #f8fafc;
  padding: 1rem 1.1rem;
}
.architecture-label,
.driver-kicker,
.workers-heading b {
  color: #64748b;
  font-size: 0.68rem;
  font-weight: 900;
  letter-spacing: 0.1em;
}
.notebook-row {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  margin-top: 0.7rem;
  color: #334155;
  font-family: monospace;
  font-size: 0.85rem;
}
.notebook-mark {
  display: grid;
  width: 1.8rem;
  height: 1.8rem;
  place-items: center;
  border-radius: 0.45rem;
  background: #dbeafe;
  color: #2563eb;
  font-family: sans-serif;
  font-size: 1.1rem;
}
.notebook-caption,
.driver-copy {
  display: block;
  margin-top: 0.65rem;
  color: #64748b;
  font-size: 0.72rem;
}
.topology-arrow {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2563eb;
  font-size: 1.8rem;
  font-weight: 800;
}
.topology-arrow span {
  position: absolute;
  margin-top: 2.2rem;
  color: #64748b;
  font-size: 0.62rem;
  font-weight: 500;
}
.architecture-driver {
  border-color: #2563eb;
  background: #eff6ff;
  color: #1e3a8a;
}
.driver-title {
  margin-top: 0.35rem;
  font-size: 1.4rem;
  font-weight: 800;
}
.driver-copy { color: #334155; font-size: 0.82rem; }
.driver-note {
  margin-top: 0.9rem;
  color: #475569;
  font-size: 0.7rem;
  font-weight: 700;
}
.driver-branch {
  position: relative;
  width: calc(100% - 22.1rem);
  height: 2rem;
  margin-left: 22.1rem;
  border-bottom: 2px solid #93c5fd;
}
.driver-branch::before {
  position: absolute;
  bottom: 0;
  left: 50%;
  height: 100%;
  border-left: 2px solid #93c5fd;
  content: '';
}
.driver-branch span {
  position: absolute;
  bottom: 0.15rem;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  padding: 0 0.5rem;
  color: #64748b;
  font-size: 0.62rem;
  white-space: nowrap;
}
.workers-area {
  width: calc(100% - 22.1rem);
  margin-left: 22.1rem;
}
.workers-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 0.55rem;
}
.workers-heading b { color: #166534; }
.workers-heading span { color: #64748b; font-size: 0.7rem; }
.worker-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.7rem; }
.worker-node {
  border: 1px solid #86efac;
  border-radius: 0.85rem;
  background: #f0fdf4;
  padding: 0.75rem;
}
.worker-heading {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  color: #334155;
  font-size: 0.8rem;
}
.worker-heading small {
  display: block;
  margin-top: 0.15rem;
  color: #64748b;
  font-size: 0.62rem;
  font-weight: 500;
}
.worker-icon {
  display: grid;
  grid-template-columns: repeat(2, 0.35rem);
  gap: 0.18rem;
  padding: 0.35rem;
  border-radius: 0.45rem;
  background: #dcfce7;
}
.worker-icon i {
  width: 0.35rem;
  height: 0.35rem;
  border-radius: 999px;
  background: #16a34a;
}
.executor-box {
  margin-top: 0.7rem;
  border: 1px solid #bbf7d0;
  border-radius: 0.6rem;
  background: white;
  padding: 0.55rem;
}
.executor-heading {
  display: flex;
  justify-content: space-between;
  color: #166534;
  font-size: 0.62rem;
  letter-spacing: 0.08em;
}
.executor-heading span { color: #64748b; letter-spacing: 0; }
.slot-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.3rem;
  margin-top: 0.55rem;
}
.slot-strip i {
  height: 0.65rem;
  border-radius: 999px;
  background: #4ade80;
}
.worker-caption {
  margin-top: 0.55rem;
  color: #64748b;
  font-size: 0.68rem;
  text-align: center;
}
.shuffle-lane {
  display: grid;
  grid-template-columns: auto auto 1fr;
  align-items: center;
  gap: 0.7rem;
  margin-top: 0.75rem;
  border-top: 2px dashed #f59e0b;
  border-bottom: 2px dashed #f59e0b;
  padding: 0.5rem 0.6rem;
  color: #92400e;
}
.shuffle-word { font-size: 0.7rem; font-weight: 900; letter-spacing: 0.1em; }
.shuffle-arrows { color: #f59e0b; font-size: 1.15rem; font-weight: 800; white-space: nowrap; }
.shuffle-caption { color: #78716c; font-size: 0.68rem; }
</style>

---

# Spark UI mental model

<div class="mental-eyebrow text-blue-700">1 application &rarr; # jobs &rarr; # stages &rarr; tasks</div>

<div class="mental-hierarchy">
  <div class="hierarchy-topline"><b>APPLICATION</b><span>SparkSession</span></div>
  <div class="hierarchy-layout">
    <div class="hierarchy-job">
      <div class="hierarchy-job-head"><b>JOB</b><span>action: save()</span></div>
      <div class="hierarchy-stage">
        <div class="hierarchy-stage-head"><b>STAGE 0</b><span>4 tasks</span></div>
        <div class="hierarchy-tasks four"><span>task</span><span>task</span><span>task</span><span>task</span></div>
      </div>
      <div class="hierarchy-shuffle">↕ &nbsp; shuffle &nbsp; ↕</div>
      <div class="hierarchy-stage">
        <div class="hierarchy-stage-head"><b>STAGE 1</b><span>3 tasks</span></div>
        <div class="hierarchy-tasks three"><span>task</span><span>task</span><span>task</span></div>
      </div>
    </div>
    <div class="hierarchy-other-jobs"><div>JOB</div><div>JOB</div><div>JOB</div></div>
  </div>
</div>

<!--
Notebook creates SparkSession, or Spark application.

Stage: groups operations that Spark can pipeline without redistributing data. Shuffle is the boundary. Talk about wide vs narrow transformations?
An application can contain multiple jobs. An action triggers a job, a shuffle separates stages, and each stage runs one task per partition.
-->

---

# Spark UI in practice

<div class="mental-eyebrow text-blue-700">The same hierarchy, in a real Fabric run</div>

<div class="screenshot-placeholder">
  <div>
    <div class="text-3xl font-bold text-slate-700">Screenshot goes here</div>
    <div class="mt-3 text-lg text-slate-500">Replace this panel with a Spark UI screenshot.</div>
  </div>
</div>

<!--
Add the Spark UI screenshot here before moving into the individual tabs.
Keep this slide as the visual bridge from the mental model to the practical walkthrough.
-->

<style>
@import './styles/index.css';
</style>

---
zoom: 0.85
---

# Job

<div class="mental-eyebrow text-blue-700">Concept 1 of 5 · the unit that gets triggered</div>

<div class="mental-grid">
  <div class="mental-copy">
    <div class="mental-kicker text-blue-700">A job is…</div>
    <div class="mental-definition">One <b>user action</b> or <b>SQL execution</b>—the thing you asked Spark to do.</div>
    <div class="mental-detail">
      <b>Where it lives in the UI</b>
      <span>The <code>Jobs</code> tab: one row per action, with its trigger, duration, stages, and tasks.</span>
    </div>
    <div class="mental-detail">
      <b>Triggered by</b>
      <span><code>count()</code> · <code>collect()</code> · <code>write…</code> · <code>show()</code> · a SQL query</span>
    </div>
  </div>
  <div class="mental-panel job-table">
    <div class="mental-panel-title">Completed Jobs (4)</div>
    <div class="mental-row header"><span>Id</span><span>Description</span><span>Duration</span><span>Tasks</span></div>
    <div class="mental-row"><span>9</span><span>show at console:24</span><span>0.4 s</span><span>1 / 1</span></div>
    <div class="mental-row"><span>8</span><span>count at orders.scala:38</span><span>2.1 s</span><span>208 / 208</span></div>
    <div class="mental-row focus-blue"><span><b>7</b></span><span><b>parquet at writer.scala:91</b></span><span><b>1m 12s</b></span><span>812 / 812</span></div>
    <div class="mental-row"><span>6</span><span>collect at repl.scala:11</span><span>0.8 s</span><span>4 / 4</span></div>
  </div>
</div>

<!--
A job is the unit Spark creates when an action asks it to produce a result. Transformations remain lazy; actions such as count, collect, show, or write trigger work.

In the Jobs tab, one row represents that request. A single application can contain many jobs, and one SQL execution can create more than one job.

Use the description to connect the row back to notebook code, then open the job to see the stages Spark needed.
-->

<style>
@import './styles/index.css';
</style>

---
zoom: 0.85
---

# Stage

<div class="mental-eyebrow text-violet-700">Concept 2 of 5 · the boundary that matters</div>

<div class="mental-grid">
  <div class="mental-copy">
    <div class="mental-kicker text-violet-700">A stage is…</div>
    <div class="mental-definition">A run of work Spark can do <b>without moving data</b>. A <b>shuffle</b> creates the next stage.</div>
    <div class="mental-detail">
      <b>The rule</b>
      <span><code>groupBy</code>, <code>join</code>, <code>repartition</code>, and windows often create a shuffle—and therefore a stage boundary.</span>
    </div>
    <div class="mental-detail">
      <b>Where it lives in the UI</b>
      <span>The <code>Stages</code> tab, or the DAG visualisation inside a job.</span>
    </div>
  </div>
  <div class="mental-panel">
    <div class="mental-panel-title">DAG · Job 7</div>
    <div class="stage-flow">
      <div class="mental-stage-card">
        <div class="stage-card-head"><b>Stage 12</b><span>200 tasks</span></div>
        <div class="stage-op">Scan parquet [orders]</div>
        <div class="stage-op">Filter status = paid</div>
        <div class="stage-op">HashAggregate (partial)</div>
      </div>
      <div class="shuffle-boundary">
        <div class="shuffle-lines">⇄</div>
        <b>SHUFFLE</b>
        <small>data moves</small>
      </div>
      <div class="mental-stage-card">
        <div class="stage-card-head"><b>Stage 13</b><span>200 tasks</span></div>
        <div class="stage-op">HashAggregate (final)</div>
        <div class="stage-op">Sort</div>
        <div class="stage-op">WriteFiles</div>
      </div>
    </div>
  </div>
</div>

<!--
A stage groups operations that Spark can pipeline without redistributing data. The important boundary is the shuffle.

Here Spark scans, filters, and performs a partial aggregation in Stage 12. The shuffle redistributes records by key. Stage 13 can then finish the aggregation and write the result.

That is why joins, aggregations, repartitioning, and windows matter during an investigation: they often create the boundaries where data moves, waits, or spills.
-->

<style>
@import './styles/index.css';
</style>

---
zoom: 0.85
---

# Task

<div class="mental-eyebrow text-rose-700">Concept 3 of 5 · the atom of execution</div>

<div class="mental-grid">
  <div class="mental-copy">
    <div class="mental-kicker text-rose-700">A task is…</div>
    <div class="mental-definition"><b>One partition’s</b> unit of work within a stage.</div>
    <div class="mental-detail">
      <b>The relationship</b>
      <span><code>tasks per stage</code> = <code>partitions in that stage</code>. The tasks run the same code on different data.</span>
    </div>
    <div class="mental-detail">
      <b>Where it lives in the UI</b>
      <span>Stage detail → task table and timeline. Skew, slow tasks, GC, and spill become visible here.</span>
    </div>
  </div>
  <div class="mental-panel task-table">
    <div class="mental-panel-title">Stage 12 · 6 of 200 tasks shown</div>
    <div class="mental-row header"><span>Partition</span><span>Task</span><span>Duration</span><span>Time</span></div>
    <div class="mental-row"><span>P0</span><span>0</span><span><i style="width:18%"></i></span><span>0.41 s</span></div>
    <div class="mental-row"><span>P1</span><span>1</span><span><i style="width:20%"></i></span><span>0.47 s</span></div>
    <div class="mental-row focus-rose"><span><b>P2</b></span><span><b>2</b></span><span><i style="width:100%"></i></span><span><b>8.2 s</b></span></div>
    <div class="mental-row"><span>P3</span><span>3</span><span><i style="width:17%"></i></span><span>0.39 s</span></div>
    <div class="mental-row"><span>P4</span><span>4</span><span><i style="width:19%"></i></span><span>0.44 s</span></div>
    <div class="mental-row"><span>P5</span><span>5</span><span><i style="width:19%"></i></span><span>0.45 s</span></div>
  </div>
</div>

<!--
A task is the same stage logic applied to one partition. Two hundred partitions produce two hundred tasks for that stage.

That relationship makes the task table diagnostic. Most tasks here finish in under half a second, but Task 2 takes more than eight seconds. The stage cannot finish until its slowest task does.

Job-level progress hides this shape. Stage detail reveals skew, stragglers, spill, GC, retries, and shuffle fetch wait at the level where they happen.
-->

<style>
@import './styles/index.css';
</style>

---
zoom: 0.85
---

# Executor

<div class="mental-eyebrow text-emerald-700">Concept 4 of 5 · where the work runs</div>

<div class="mental-grid">
  <div class="mental-copy">
    <div class="mental-kicker text-emerald-700">An executor is…</div>
    <div class="mental-definition">A worker <b>JVM process</b> that runs tasks in parallel slots and holds cached data.</div>
    <div class="mental-detail">
      <b>The math</b>
      <span><code>parallel tasks</code> ≈ <code>executors × cores</code>. With 12 cores available, only about 12 tasks run at once.</span>
    </div>
    <div class="mental-detail">
      <b>Where it lives in the UI</b>
      <span>The <code>Executors</code> tab: active tasks, memory, GC time, shuffle, and executor logs.</span>
    </div>
  </div>
  <div class="mental-panel executor-table">
    <div class="mental-panel-title">Active Executors</div>
    <div class="mental-row header"><span>Executor</span><span>Host</span><span>Slots</span><span>Memory</span></div>
    <div class="mental-row"><span>driver</span><span>node-00</span><span class="slots idle">● ● ● ●</span><span>1.1 GB</span></div>
    <div class="mental-row focus-emerald"><span><b>exec-01</b></span><span>node-01</span><span class="slots busy">● ● ● ●</span><span>5.8 / 8 GB</span></div>
    <div class="mental-row"><span>exec-02</span><span>node-02</span><span class="slots mixed">● ● ● ●</span><span>4.2 / 8 GB</span></div>
    <div class="mental-row"><span>exec-03</span><span>node-03</span><span class="slots busy">● ● ● ●</span><span>6.1 / 8 GB</span></div>
    <div class="mental-row"><span>exec-04</span><span>node-04</span><span class="slots mixed two">● ● ● ●</span><span>3.7 / 8 GB</span></div>
    <div class="mental-row"><span>exec-05</span><span>node-05</span><span class="slots busy">● ● ● ●</span><span>6.4 / 8 GB</span></div>
  </div>
</div>

<!--
Executors are the worker processes that perform tasks. Their cores determine how many tasks can run concurrently; the rest wait for a slot.

The Executors tab shows where pressure lands. Compare active tasks, memory use, GC time, shuffle traffic, and failed tasks across executors.

An imbalance can support a skew hypothesis. Pressure across every executor points instead toward a cost shared by the stage, such as broad memory or shuffle pressure.
-->

<style>
@import './styles/index.css';
</style>

---
zoom: 0.85
---

# SQL tab

<div class="mental-eyebrow text-amber-700">Concept 5 of 5 · why those stages exist</div>

<div class="mental-grid">
  <div class="mental-copy">
    <div class="mental-kicker text-amber-700">The SQL tab is…</div>
    <div class="mental-definition">The <b>physical plan</b> Spark actually chose for a SQL or DataFrame query.</div>
    <div class="mental-detail">
      <b>Read it like this</b>
      <span>Every <code>Exchange</code> is a shuffle—and therefore a stage boundary. Metrics hang from each operator.</span>
    </div>
    <div class="mental-detail">
      <b>Why it matters</b>
      <span>Jobs and stages show <i>what</i> ran. The SQL plan explains <b>why</b>.</span>
    </div>
  </div>
  <div class="mental-panel plan-panel">
    <div class="mental-panel-title">Physical plan · orders JOIN customers</div>
    <div class="mental-plan">
      <div class="mental-plan-node">WriteFiles <small>812 rows · 3.4 MB</small></div>
      <div class="plan-line"></div>
      <div class="mental-plan-node">SortMergeJoin <small>inner · customer_id</small></div>
      <div class="plan-line"></div>
      <div class="plan-branches">
        <div class="plan-branch">
          <div class="mental-plan-node exchange">Exchange (hash)<small>shuffle · 18 MB</small></div>
          <div class="plan-line"></div>
          <div class="mental-plan-node compact">HashAggregate</div>
          <div class="plan-line"></div>
          <div class="mental-plan-node compact">Scan orders</div>
        </div>
        <div class="plan-branch">
          <div class="mental-plan-node exchange">Exchange (hash)<small>shuffle · 4 MB</small></div>
          <div class="plan-line"></div>
          <div class="mental-plan-node compact">Filter active</div>
          <div class="plan-line"></div>
          <div class="mental-plan-node compact">Scan customers</div>
        </div>
      </div>
    </div>
  </div>
</div>

<!--
The SQL tab connects the runtime evidence back to the physical work Spark chose.

Read this plan from the scans upward. Both sides pass through an Exchange, so Spark redistributes both datasets before the sort-merge join. Those exchanges explain the stage boundaries visible elsewhere in the UI.

Use operator metrics to connect an expensive stage to a join, aggregation, scan, or write. The metrics tell you what hurts; the plan explains why that work exists.
-->

<style>
@import './styles/index.css';
</style>

---

# Tiny Fabric Orientation

In Fabric, you usually do not start by typing a Spark UI URL.

<div class="mt-8">

| Situation | Use |
|---|---|
| The Spark application is still running | **Live Spark UI** |
| The Spark application completed or failed | **Spark History Server** |
| You do not know which run to inspect | **Monitor hub / Recent runs** |

</div>

<div class="mt-8 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-500">
Placeholder: screenshot of Fabric Monitor hub, Recent runs, or notebook run details
</div>

<!--
Keep this orientation deliberately short. The goal is just to anchor Spark UI inside the Fabric experience.
Explain that live Spark UI is for active applications, while History Server is for completed or failed applications.
If the audience does not know which run is relevant, they should start in Monitor hub or Recent runs before drilling into Spark internals.
-->

---

# The First Decision

```mermaid
flowchart LR
    A[Fabric Monitor hub<br/>or Recent runs] --> B{Application state?}
    B -->|Running| C[Live Spark UI]
    B -->|Completed or failed| D[Spark History Server]
    B -->|Unknown run| A
    C --> E[Stage and task evidence]
    D --> E
```

<div class="mt-8 text-xl text-center opacity-80">
Find the run, choose live or post-mortem, then read the Spark evidence.
</div>

<!--
Use the diagram to make the Fabric entry path memorable.
The important point is that Fabric gives the starting point and operational context, while Spark UI and History Server provide detailed execution evidence.
Transition from here into the mental model: once we reach Spark evidence, we need enough vocabulary to interpret what we see.
-->
---
layout: default
clicks: 6
---

# The Detective's Field Guide

<div class="text-xl opacity-70">One path. Every case.</div>

<DetectiveFieldGuide :active="$clicks" />

<div class="mt-8 text-center text-2xl font-semibold">
  <span v-if="$clicks === 0">A slow job is a symptom. Walk the evidence.</span>
  <span v-else-if="$clicks < 6">Do not skip ahead to a favorite tuning knob.</span>
  <span v-else>A case ends with one testable hypothesis.</span>
</div>

<!--
We have enough Spark vocabulary now. We need a route through the evidence.

I will use this field guide for every case in the rest of the session. The data and symptoms will change, but these six moves stay fixed.

[click] Find the right run. Check the application, attempt, input volume, and timing before opening low-level metrics.

[click] Choose the right lens. Use the live Spark UI while the application runs. Use History Server after it completes or fails.

[click] Localize the costly stage. Sort by duration and find the stage that accounts for the wall-clock time.

[click] Inspect the task shape. Look past averages. Check whether tasks finish together, form a long tail, spill, wait, or retry.

[click] Correlate that stage with the SQL plan, executors, Fabric Diagnosis views, and logs. Each view should support or challenge the same explanation.

[click] Test one hypothesis. Change one thing, rerun, and compare the same evidence.

Say the verbs once more: Find. Choose. Localize. Inspect. Correlate. Test.
-->

---
zoom: 0.85
---

# Start with the right case

<DetectiveFieldGuide :active="2" compact />

<div class="grid grid-cols-2 gap-8 mt-2">
  <div class="rounded-2xl border border-slate-200 bg-slate-50 p-6">
    <div class="text-sm font-bold tracking-widest text-blue-700">1 · FIND</div>
    <h2 class="mt-2">Which run changed?</h2>
    <div class="mt-5 grid grid-cols-3 gap-3 text-center">
      <div class="source-card"><b>Monitor hub</b><small>across items</small></div>
      <div class="source-card"><b>Recent runs</b><small>from the workload</small></div>
      <div class="source-card"><b>App details</b><small>one application</small></div>
    </div>
    <div class="mt-5 text-lg text-slate-600">Compare duration, input volume, status, and timing before drilling down.</div>
  </div>

  <div class="rounded-2xl border border-blue-200 bg-blue-50 p-6">
    <div class="text-sm font-bold tracking-widest text-blue-700">2 · CHOOSE</div>
    <h2 class="mt-2">Which lens has the evidence?</h2>
    <div class="mt-4 space-y-3">
      <div class="lens-row"><span class="status live">RUNNING</span><b>Live Spark UI</b></div>
      <div class="lens-row"><span class="status history">DONE / FAILED</span><b>Spark History Server</b></div>
      <div class="lens-row"><span class="status context">CONTEXT</span><b>Application details & logs</b></div>
    </div>
  </div>
</div>

<div class="mt-6 text-center text-xl font-semibold">Wrong run in, wrong diagnosis out.</div>

<!--
Start with the question from the opening: yesterday took 12 minutes and today took 55. Before we diagnose Spark, we need both application records. Confirm that they ran the same notebook or job definition and identify the relevant attempt. Compare input volume, start time, status, and capacity context.

Use Monitor hub when you need to search across workspace activity. Use Recent runs when you begin from a notebook, Spark Job Definition, or pipeline. Open the application details page once you have the application.

Then choose the evidence source. A running application gives us the live Spark UI. A completed or failed application gives us the History Server. The application details page remains useful for resources, logs, and operational context.

Fabric's extended History Server also has Diagnosis views for data skew, time skew, and executor usage. We will use those views to confirm evidence later. They do not replace choosing the correct application.

Transition: now we have the right case file and the right lens. We can ask where the time went.
-->

<style>
.source-card {
  display: flex;
  min-height: 7rem;
  flex-direction: column;
  justify-content: center;
  border: 1px solid #cbd5e1;
  border-radius: 0.8rem;
  background: white;
  padding: 0.7rem;
}
.source-card small {
  display: block;
  margin-top: 0.45rem;
  color: #64748b;
  line-height: 1.2;
}
.lens-row {
  display: grid;
  grid-template-columns: 8.5rem 1fr;
  align-items: center;
  gap: 1rem;
  border-radius: 0.75rem;
  background: white;
  padding: 0.8rem;
}
.status {
  border-radius: 999px;
  padding: 0.3rem 0.55rem;
  text-align: center;
  font-size: 0.7rem;
  font-weight: 800;
}
.status.live { background: #dcfce7; color: #166534; }
.status.history { background: #ede9fe; color: #5b21b6; }
.status.context { background: #e2e8f0; color: #334155; }
</style>

---
zoom: 0.85
---

# Localize the cost

<DetectiveFieldGuide :active="3" compact />

<div class="grid grid-cols-[1.6fr_0.8fr] gap-8 mt-2">
  <div class="stage-table">
    <div class="stage-row header"><span>Stage</span><span>Duration</span><span>Tasks</span><span>Shuffle</span><span>Spill</span></div>
    <div class="stage-row"><span>3</span><span>1m 18s</span><span>200</span><span>2.1 GB</span><span>0</span></div>
    <div class="stage-row suspect-stage"><span><b>8</b></span><span><b>36m 42s</b></span><span>200</span><span>86 GB</span><span>41 GB</span></div>
    <div class="stage-row"><span>12</span><span>2m 04s</span><span>48</span><span>4.8 GB</span><span>0</span></div>
  </div>

  <div class="rounded-2xl bg-violet-50 border border-violet-200 p-6">
    <div class="text-sm font-bold tracking-widest text-violet-700">3 · LOCALIZE</div>
    <h2 class="mt-2">Ask first</h2>
    <div class="mt-5 text-2xl font-semibold leading-snug">Is the whole application slow—or does one stage explain it?</div>
    <ul class="mt-5 text-lg leading-relaxed">
      <li>Sort by duration</li>
      <li>Notice retries or failures</li>
      <li>Compare shuffle and task count</li>
    </ul>
  </div>
</div>

<div class="mt-7 rounded-xl bg-slate-900 px-6 py-4 text-center text-xl font-semibold text-white">
  Open the stage that explains the runtime.
</div>

<!--
Give the audience a few seconds to scan the table. Ask: which row would you open first?

Stage 8 took 36 minutes and 42 seconds. The other visible stages took about one or two minutes. Stage 8 accounts for most of this application's runtime, so it becomes our investigation boundary.

The row gives us early clues. It processed 86 GB of shuffle and spilled 41 GB. Those numbers deserve attention, but they do not prove a cause. A large shuffle can be expected. Spill can hurt without explaining the full delay. We need the task detail next.

Also check failed and retried stages. A stage may appear several times because Spark retried it, which can hide the true cost if you inspect only the final successful attempt. An unusual task count can expose poor parallelism before you open the stage.

The discipline here saves time: rank stages by their contribution to runtime, then open the one that can explain the symptom.
-->

<style>
.stage-table {
  overflow: hidden;
  align-self: center;
  border: 1px solid #cbd5e1;
  border-radius: 1rem;
  background: white;
}
.stage-row {
  display: grid;
  grid-template-columns: 0.7fr 1.25fr 0.8fr 1.1fr 1fr;
  border-top: 1px solid #e2e8f0;
  padding: 1rem 1.1rem;
}
.stage-row.header {
  border-top: 0;
  background: #f1f5f9;
  color: #475569;
  font-size: 0.8rem;
  font-weight: 800;
  text-transform: uppercase;
}
.stage-row.suspect-stage {
  border-left: 0.35rem solid #7c3aed;
  background: #f5f3ff;
  color: #4c1d95;
}
</style>

---

# Read the shape of the tasks

<DetectiveFieldGuide :active="4" compact />

<div class="grid grid-cols-3 gap-5 mt-2">
  <div class="task-pattern healthy">
    <div class="pattern-title">Balanced</div>
    <div class="task-bars">
      <i style="height:62%"></i><i style="height:68%"></i><i style="height:65%"></i><i style="height:71%"></i><i style="height:64%"></i>
    </div>
    <b>Tasks finish together</b>
    <small>Look elsewhere for the bottleneck.</small>
  </div>
  <div class="task-pattern skewed">
    <div class="pattern-title">Long tail</div>
    <div class="task-bars">
      <i style="height:24%"></i><i style="height:28%"></i><i style="height:22%"></i><i style="height:31%"></i><i style="height:94%"></i>
    </div>
    <b>A few tasks dominate</b>
    <small>Suspect skew or a straggler.</small>
  </div>
  <div class="task-pattern pressure">
    <div class="pattern-title">Pressure</div>
    <div class="task-bars">
      <i style="height:76%"></i><i style="height:86%"></i><i style="height:80%"></i><i style="height:91%"></i><i style="height:84%"></i>
    </div>
    <b>Many tasks are expensive</b>
    <small>Check spill, GC, fetch wait, and I/O.</small>
  </div>
</div>

<div class="mt-5 flex flex-wrap justify-center gap-3">
  <span class="clue-chip">duration</span><span class="clue-chip">shuffle read</span><span class="clue-chip">spill</span><span class="clue-chip">GC time</span><span class="clue-chip">fetch wait</span><span class="clue-chip">retries</span>
</div>

<div class="mt-5 text-center text-2xl font-semibold">The average hides the case. The distribution reveals it.</div>

<!--
Task distributions reveal what a stage average conceals.

Start on the left. These tasks finish in a narrow range. Balanced does not mean fast; it means no small group of tasks controls the stage duration. If every task is slow, investigate a cost shared across the stage, such as heavy shuffle, spill, CPU work, or external I/O.

The middle shape has a long tail. Most tasks finish, while one task keeps the stage alive. Compare shuffle read and input size per task. One task reading far more data points toward skew. Similar input with one slow task points toward a straggler, executor issue, or external delay.

On the right, many tasks consume substantial time. Check spill, GC time, shuffle fetch wait, scheduler delay, and retries. These metrics separate memory pressure, data movement, scheduling, and unstable execution.

Use medians, percentiles, and the task table where available. An average blends the fast majority with the expensive tail.

We will recall these three shapes in the cases: balanced with spill, a skewed long tail, and broad pressure from shuffle or weak parallelism.
-->

<style>
.task-pattern {
  border: 1px solid #cbd5e1;
  border-radius: 1rem;
  background: #f8fafc;
  padding: 1rem;
  text-align: center;
}
.pattern-title {
  margin-bottom: 0.5rem;
  font-size: 1.15rem;
  font-weight: 800;
}
.task-bars {
  display: flex;
  height: 9rem;
  align-items: end;
  gap: 0.55rem;
  margin-bottom: 0.8rem;
  padding: 0.8rem;
  border-radius: 0.7rem;
  background: white;
}
.task-bars i {
  flex: 1;
  border-radius: 0.35rem 0.35rem 0 0;
  background: #22c55e;
}
.skewed .task-bars i { background: #60a5fa; }
.skewed .task-bars i:last-child { background: #f43f5e; }
.pressure .task-bars i { background: #f59e0b; }
.task-pattern small {
  display: block;
  margin-top: 0.35rem;
  color: #64748b;
}
.clue-chip {
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: white;
  padding: 0.35rem 0.8rem;
  color: #475569;
  font-size: 0.85rem;
  font-weight: 700;
}
</style>

---
zoom: 0.85
---

# Corroborate before you accuse

<DetectiveFieldGuide :active="5" compact />

<div class="corroboration mt-3">
  <div class="evidence-card plan">
    <div class="evidence-label">SQL PLAN</div>
    <h2>Why does this stage exist?</h2>
    <p>Join strategy · exchanges · aggregations</p>
  </div>
  <div class="evidence-card stage">
    <div class="evidence-label">STAGE + TASKS</div>
    <h2>What hurts?</h2>
    <p>Duration · shape · shuffle · spill</p>
  </div>
  <div class="evidence-card executors">
    <div class="evidence-label">EXECUTORS</div>
    <h2>Where does pressure land?</h2>
    <p>GC · memory · workload imbalance</p>
  </div>
  <div class="evidence-card fabric">
    <div class="evidence-label">FABRIC</div>
    <h2>What confirms it?</h2>
    <p>Diagnosis · graph · application logs</p>
  </div>
</div>

<div class="mt-6 grid grid-cols-[1fr_auto_1fr] items-center gap-5 text-center">
  <div class="rounded-xl bg-amber-50 border border-amber-200 p-4 text-xl"><b>One clue</b><br><span class="text-slate-600">a suspicion</span></div>
  <div class="text-4xl text-slate-400">→</div>
  <div class="rounded-xl bg-emerald-50 border border-emerald-200 p-4 text-xl"><b>Independent clues agree</b><br><span class="text-slate-600">a hypothesis worth testing</span></div>
</div>

<!--
We have localized the stage and read its task shape. Now we need independent evidence.

Keep the stage at the center. In the SQL view, find the operator connected to that stage. Exchanges show shuffle boundaries. The join strategy or aggregation explains why Spark created the expensive work.

Move to Executors when the task metrics suggest memory pressure, GC, or uneven usage. Check whether the pressure appears across executors or concentrates on one worker. A single unhealthy executor tells a different story from every executor spilling.

Fabric adds useful post-mortem evidence. The Diagnosis tab can flag data skew, time skew, and executor usage. The Graph view helps connect jobs and stages. Application and executor logs can confirm fetch failures, repeated loss, or an external error.

Keep one identifier in your head as you move between views: the same stage, task, executor, or SQL node. Opening more tabs does not strengthen a case. Two independent clues that describe the same bottleneck do.

Transition: once the clues agree, phrase a claim that a rerun can disprove.
-->

<style>
.corroboration {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-areas: 'plan stage executors' '. fabric .';
  gap: 1rem;
}
.evidence-card {
  border: 1px solid #cbd5e1;
  border-radius: 1rem;
  background: white;
  padding: 1rem 1.2rem;
  text-align: center;
}
.evidence-card.plan { grid-area: plan; }
.evidence-card.stage { grid-area: stage; border-color: #7c3aed; background: #f5f3ff; }
.evidence-card.executors { grid-area: executors; }
.evidence-card.fabric { grid-area: fabric; border-color: #2563eb; background: #eff6ff; }
.evidence-label {
  color: #64748b;
  font-size: 0.7rem;
  font-weight: 900;
  letter-spacing: 0.12em;
}
.evidence-card h2 { margin: 0.3rem 0; font-size: 1.15rem; }
.evidence-card p { margin: 0; color: #64748b; font-size: 0.85rem; }
</style>

---
zoom: 0.85
---

# End with one testable hypothesis

<DetectiveFieldGuide :active="6" compact />

<div class="hypothesis-chain mt-4">
  <div class="hypothesis-box evidence">
    <div class="box-label">EVIDENCE</div>
    <b>Stage 8 dominates</b>
    <span>Tasks are balanced; shuffle and spill rose</span>
  </div>
  <div class="chain-arrow">→</div>
  <div class="hypothesis-box suspect">
    <div class="box-label">HYPOTHESIS</div>
    <b>The larger shuffle crossed a memory threshold</b>
    <span>Not “Spark needs more tuning”</span>
  </div>
  <div class="chain-arrow">→</div>
  <div class="hypothesis-box test">
    <div class="box-label">ONE TEST</div>
    <b>Reduce shuffle volume</b>
    <span>Rerun and compare the same stage metrics</span>
  </div>
</div>

<div class="mt-8 grid grid-cols-2 gap-6 text-center text-xl">
  <div class="rounded-xl border border-red-200 bg-red-50 p-5 text-red-800 line-through">Change five knobs and hope</div>
  <div class="rounded-xl border border-emerald-200 bg-emerald-50 p-5 font-semibold text-emerald-800">Change one thing and learn</div>
</div>

<div class="mt-8 text-center text-3xl font-bold">Evidence → hypothesis → test → compare</div>

<!--
Use a three-part sentence to close the investigation.

First, state the evidence with numbers: Stage 8 accounts for most of the runtime. Its tasks finish in a similar range. Shuffle volume and spill increased compared with the faster run.

Second, name one cause: the larger shuffle crossed a memory threshold, so tasks wrote intermediate data to disk. This claim predicts what we should see after a targeted change.

Third, define the test. Reduce the shuffle volume, pre-aggregate earlier, or adjust partitioning. Pick one change for the rerun. Then compare Stage 8 duration, spill, shuffle volume, and task distribution with the original run.

Wall-clock time alone gives weak confirmation because capacity load and external systems can vary between runs. The stage metrics tell us whether our change affected the mechanism we suspected.

If the predicted metrics stay flat, reject the hypothesis and return to the evidence. That result still teaches us more than changing several settings at once.
-->

<style>
.hypothesis-chain {
  display: grid;
  grid-template-columns: 1fr auto 1.15fr auto 1fr;
  align-items: stretch;
  gap: 0.8rem;
}
.hypothesis-box {
  display: flex;
  min-height: 12rem;
  flex-direction: column;
  justify-content: center;
  border: 2px solid #cbd5e1;
  border-radius: 1rem;
  background: #f8fafc;
  padding: 1.4rem;
  text-align: center;
}
.hypothesis-box.suspect { border-color: #f59e0b; background: #fffbeb; }
.hypothesis-box.test { border-color: #22c55e; background: #f0fdf4; }
.box-label {
  margin-bottom: 0.7rem;
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 900;
  letter-spacing: 0.12em;
}
.hypothesis-box b { font-size: 1.15rem; line-height: 1.25; }
.hypothesis-box span { margin-top: 0.65rem; color: #64748b; font-size: 0.85rem; }
.chain-arrow { align-self: center; color: #94a3b8; font-size: 2.5rem; font-weight: 800; }
</style>

---

# Same route. New evidence.

<DetectiveFieldGuide :active="0" />

<div class="mt-8 grid grid-cols-3 gap-5 text-center">
  <div class="case-card"><b>Case 1</b><span>Data grew and spilled</span></div>
  <div class="case-card"><b>Case 2</b><span>One straggler hid the skew</span></div>
  <div class="case-card"><b>Case 3</b><span>Too much moving, too few hands</span></div>
</div>

<div class="mt-10 text-center text-3xl font-bold">Reset to Find. Follow the clues.</div>

<!--
Before the cases, ask the room to recall the route. Point to each card and let them supply the verb: Find. Choose. Localize. Inspect. Correlate. Test.

Each case starts from the left again. In Case 1, data volume grows and a stage spills. In Case 2, one hot key creates a long tail. In Case 3, shuffle and low parallelism leave resources idle.

Keep this ribbon visible during each walkthrough. Move the highlight as we change views. The audience should know why we click a stage, task, SQL node, or executor before the screen changes.

Set up Case 1: return to the 12-minute run that became a 55-minute run. We already know the route. Now we will work the evidence.
-->

<style>
.case-card {
  display: flex;
  min-height: 7.5rem;
  flex-direction: column;
  justify-content: center;
  border: 1px solid #cbd5e1;
  border-radius: 1rem;
  background: #f8fafc;
  padding: 1rem;
}
.case-card b { color: #2563eb; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.08em; }
.case-card span { margin-top: 0.5rem; font-size: 1.05rem; font-weight: 700; }
</style>


---

# Case 0: writing to disk

<DetectiveFieldGuide :active="0" />

<div class="mt-8 grid grid-cols-3 gap-5 text-center">
  <div class="case-card"><b>Case 1</b><span>Data grew and spilled</span></div>
  <div class="case-card"><b>Case 2</b><span>One straggler hid the skew</span></div>
  <div class="case-card"><b>Case 3</b><span>Too much moving, too few hands</span></div>
</div>

<div class="mt-10 text-center text-3xl font-bold">Reset to Find. Follow the clues.</div>

<!--
Remember wide vs narrow transformations

narrow: performs operation called pipelining -> when you specify multiple filters they are performed in memory
wide: Spark needs to write the results to disk
-->

<style>
.case-card {
  display: flex;
  min-height: 7.5rem;
  flex-direction: column;
  justify-content: center;
  border: 1px solid #cbd5e1;
  border-radius: 1rem;
  background: #f8fafc;
  padding: 1rem;
}
.case-card b { color: #2563eb; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.08em; }
.case-card span { margin-top: 0.5rem; font-size: 1.05rem; font-weight: 700; }
</style>
