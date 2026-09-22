---
theme: light-icons
title: The Spark Detective
info: |
  The Spark Detective: Diagnosing Spark Performance in Microsoft Fabric.
class: emfcc-cover
drawings:
  persist: false
transition: slide-left
mdc: true
---

<div class="emfcc-visually-hidden">European Microsoft Fabric and SQL Community Conference · Barcelona · 28 September–1 October 2026</div>

<!--
Official conference opening slide. The session title follows as slide 2, as required by the EMFCC26 speaker template.
-->

---
class: emfcc-title
---

<div class="emfcc-recording-notice">Do not record or livestream this session</div>

<img src="./images/me.jpg" alt="Thibauld Croonenborghs" class="emfcc-speaker-photo" />

<div class="emfcc-title-copy">
  <h1>The Spark Detective</h1>
  <h2>The curious case of the slow Spark job: a detective's toolbox</h2>
  <div class="emfcc-speaker">Thibauld Croonenborghs</div>
  <div class="emfcc-speaker-details">
    <span>Data Architect · AE NV · Belgium</span>
    <span class="belgian-flag" aria-label="Belgium"></span>
  </div>
</div>

<!--

Who is working with Spark in Fabric?
Who has already worked with the Spark UI?
Who has already diagnosed a problem using the Spark UI?

This is a practical investigation.
I don’t want you to learn how to solve every issue in spark. Also in the practical cases I will throw some technical terms around (like sortmergejoin, broadcase join, etc.) the goal of this session is not to remember them, but the goal is to give you a reusable workflow to find possible issues using the Spark UI.
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
Emphasize that Spark performance problems often do not fail loudly; they leave clues in runtime, stages, tasks, shuffle, spill, and executor behavior.
sometimes jobs fail and it is a mystery. You will become the detective and need to follow the clues, do your due dilligence and find the culprit to the crime 
-->

---
zoom: 0.85
---

# Spark architecture: driver to workers

<div class="architecture-topology">
  <div class="notebook-card">
    <div class="architecture-label">NOTEBOOK / APPLICATION</div>
    <div class="notebook-row">
      <span class="notebook-mark">▤</span>
      <b>groupBy("zone").count()</b>
    </div>
    <span class="notebook-caption">An action plugs into the driver.</span>
  </div>

  <div class="topology-arrow" v-click="1">→ <span>submit</span></div>

  <div class="architecture-driver" v-click="1">
    <div class="driver-kicker">DRIVER NODE</div>
    <div class="driver-title">Application coordinator</div>
    <div class="driver-copy">Plans the work, schedules it, and tracks progress.</div>
    <div class="driver-note">The driver coordinates; executors process the data.</div>
  </div>
</div>

<div class="driver-branch" v-click="2"><span>schedule work to the cluster</span></div>

<div class="workers-area" v-click="2">
  <div class="workers-heading">
    <b>WORKER NODES</b>
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

</div>

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

<!--
Spark cluster

The Spark cluster is created as follows: 1 driver, 1 or more workers or nodes

Start on the left: the notebook submits an action to the driver. The driver is the coordinator. It plans the work, schedules it, and tracks progress; it is not where all the rows are processed. Notebook asks SparkSession this is a driver process. SparkSession manages Spark application (1-to-1 relation)

When an action runs—such as count(), show(), collect(), or write()—the driver:
     - analyzes and optimizes the logical plan
     - chooses a physical plan, such as Filter, Exchange, or SortMergeJoin
     - splits it into stages at shuffle boundaries
     - sends tasks to executors

The driver fans work out to multiple worker nodes. Each worker hosts an executor with several parallel slots, so partitions can be processed at the same time. More workers mean more possible parallelism.
Executors process their assigned partitions. They read data, run the pipelined operators, perform shuffles where necessary, and return results or write output.
-->

---

# One action becomes a job

<div class="mental-eyebrow text-blue-700">A concrete example of the hierarchy</div>

<div class="action-to-job">
  <div class="action-code-card">
    <div class="flow-label">NOTEBOOK</div>
    <div class="action-code"><span>trips = spark.read.table("trips")</span><span>&nbsp;</span><span>(trips.filter("fare is positive")</span><span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;.groupBy("zone")</span><span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;.count()</span><span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;.write.saveAsTable("daily"))</span></div>
    <div class="action-callout"><b><code>write()</code></b> is the action: Spark must now do the work.</div>
  </div>

  <div class="flow-arrow" v-click="1"><span>→</span><small>triggers</small></div>

  <div class="example-job" v-click="1">
    <div class="example-job-head"><span>JOB 7</span><b>write()</b></div>
    <div class="example-stage" v-click="2">
      <div class="example-stage-copy"><b>STAGE 0</b><small>read · filter · partial aggregate</small></div>
      <div class="example-tasks blue" v-click="3"><i>Task 0</i><i>Task 1</i><i>Task 2</i><i>Task 3</i></div>
    </div>
    <div class="example-shuffle" v-click="2"><b>↕ &nbsp; SHUFFLE &nbsp; ↕</b><span><code>groupBy("zone")</code> redistributes rows by zone</span></div>
    <div class="example-stage" v-click="2">
      <div class="example-stage-copy"><b>STAGE 1</b><small>final aggregate · write</small></div>
      <div class="example-tasks violet" v-click="3"><i>Task 0</i><i>Task 1</i><i>Task 2</i></div>
    </div>
  </div>
</div>

<div class="action-summary" v-click="1">
  <span v-click="1"><b>An action</b> creates a job</span><i v-click="1">→</i><span v-click="2"><b>A shuffle</b> starts a new stage</span><i v-click="2">→</i><span v-click="3"><b>Each partition</b> becomes a task</span>
</div>

<style>
.action-to-job {
  display: grid;
  grid-template-columns: 18rem 3.5rem 1fr;
  align-items: center;
  gap: 1rem;
  margin-top: 1rem;
}
.action-code-card,
.example-job {
  border: 1px solid #cbd5e1;
  border-radius: 1rem;
  background: #f8fafc;
}
.action-code-card { padding: 1rem 1.1rem; }
.flow-label {
  color: #64748b;
  font-size: 0.68rem;
  font-weight: 900;
  letter-spacing: 0.1em;
}
.action-code {
  display: flex;
  flex-direction: column;
  margin: 0.65rem 0;
  color: #1e3a8a;
  font-family: monospace;
  font-size: 0.68rem;
  line-height: 1.55;
  white-space: pre;
}
.action-callout {
  border-top: 1px solid #bfdbfe;
  padding-top: 0.65rem;
  color: #475569;
  font-size: 0.7rem;
  line-height: 1.35;
}
.action-callout b { color: #2563eb; }
.flow-arrow { color: #2563eb; text-align: center; }
.flow-arrow span { display: block; font-size: 2.2rem; font-weight: 800; }
.flow-arrow small { color: #64748b; font-size: 0.65rem; }
.example-job { overflow: hidden; border-color: #93c5fd; background: white; }
.example-job-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #eff6ff;
  padding: 0.55rem 0.8rem;
  color: #1e3a8a;
  font-size: 0.75rem;
}
.example-job-head span { font-weight: 900; letter-spacing: 0.1em; }
.example-stage {
  display: grid;
  grid-template-columns: 11rem 1fr;
  align-items: center;
  gap: 0.8rem;
  padding: 0.75rem 0.8rem;
}
.example-stage-copy b { display: block; color: #334155; font-size: 0.75rem; letter-spacing: 0.08em; }
.example-stage-copy small { display: block; margin-top: 0.2rem; color: #64748b; font-size: 0.65rem; line-height: 1.2; }
.example-tasks { display: flex; gap: 0.45rem; }
.example-tasks i {
  min-width: 3.25rem;
  border-radius: 0.45rem;
  padding: 0.6rem 0.35rem;
  color: white;
  font-size: 0.65rem;
  font-style: normal;
  font-weight: 800;
  text-align: center;
}
.example-tasks.blue i { background: #2563eb; }
.example-tasks.violet i { background: #7c3aed; }
.example-shuffle {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border-top: 2px dashed #f59e0b;
  border-bottom: 2px dashed #f59e0b;
  background: #fffbeb;
  padding: 0.45rem 0.8rem;
  color: #92400e;
  font-size: 0.68rem;
}
.example-shuffle span { color: #78716c; }
.action-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 1.2rem;
  border-radius: 0.85rem;
  background: #f1f5f9;
  padding: 0.7rem;
  color: #475569;
  font-size: 0.8rem;
}
.action-summary b { color: #0f172a; }
.action-summary > i { color: #94a3b8; font-size: 1.15rem; font-style: normal; font-weight: 800; }
</style>

<!--
spark hierarchy of execution 

2 types of building blocks in a Spark job: A transformation creates a new RDD/DataFrame from an existing one (it describes a step in your pipeline - like a select, filter, join etc) and is evaluated lazily. An action asks Spark to materialize a result (return to the driver, write to storage, or otherwise “finish” the computation), which is what triggers a job in Spark’s execution model.

Stage 0 reads, filters, and performs a partial aggregate across four partitions, so it has four tasks. 
A task processes one partition and can pipeline several narrow operations without materializing intermediate results: read → select → filter → map
groupBy redistributes rows by zone: that shuffle ends Stage 0. Stage 1 performs the final aggregate and writes its three output partitions.

Clarify the potentially confusing `count()` here: `groupBy("zone").count()` is a grouped DataFrame aggregation that returns a new DataFrame, so it is still lazy in this chain. A standalone `df.count()` is different: it is an action, materializes the result, and creates a job. In this example the final `write()` is the action that triggers the whole plan.
-->

---

# Spark UI in practice

<div class="spark-ui-jobs-frame">
  <img
    src="./images/spark_ui_jobs.png"
    alt="Spark UI Jobs tab"
    class="spark-ui-jobs-screenshot"
  />
</div>

<style>

.spark-ui-jobs-screenshot {
  display: block;
  width: 100%;
  max-height: 22rem;
  margin-top: 0.5rem;
  object-fit: contain;
  border: 1px solid #cbd5e1;
  border-radius: 1.25rem;
  box-shadow: 0 0.75rem 1.5rem rgb(15 23 42 / 0.15);
}
</style>

<!--
Fabric: extended history server. For a completed run in Fabric, the Spark History Server adds two useful investigation views:

- **Graph**: select a Job ID, then open Graph to see the job DAG and its stage flow. Switch between progress, read, and written data; select a stage node to open its stage details. Use it to understand how the stages connect and where the work is concentrated.
- **Diagnosis**: select a Job ID, then open Diagnosis. Fabric highlights Data Skew, Time Skew, and Executor Usage Analysis. These are shortcuts to patterns we could otherwise find manually in task tables and executor timelines.

Also add things like: snapshot-based loading and executor rolling logs
-->

---
zoom: 0.85
---

# Job

<div class="mental-grid">
  <div class="mental-copy">
    <div class="mental-kicker text-blue-700">A job is…</div>
    <div class="mental-definition">One <b>user action</b> or <b>SQL execution</b></div>
    <div class="mental-detail">
      <b>Where it lives in the UI</b>
      <span>The <code>Jobs</code> tab: one row per action, with its trigger, duration, stages, and tasks.</span>
    </div>
    <div class="mental-detail">
      <b>Triggered by</b>
      <span>actions, like <code>count()</code> · <code>collect()</code> · <code>write…</code> · <code>show()</code> · a SQL query</span>
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

<style>
</style>

<!--
A job is the unit Spark creates when an action asks it to produce a result. Transformations remain lazy; actions such as count, collect, show, or write trigger work.

In the Jobs tab, one row represents that request. A single application can contain many jobs, and one SQL execution can create more than one job.

Use the description to connect the row back to notebook code, then open the job to see the stages Spark needed.
-->

---
zoom: 0.85
---

# Stage

<div class="mental-grid">
  <div class="mental-copy">
    <div class="mental-kicker text-violet-700">A stage is…</div>
    <div class="mental-definition">A run of work Spark can do <b>without moving data</b>. A <b>shuffle</b> creates the next stage.</div>
    <div class="mental-detail">
      <b>Where it lives in the UI</b>
      <span>The <code>Stages</code> tab, or the DAG visualisation inside a job.</span>
    </div>
    <div class="mental-detail">
      <b>Triggered by</b>
      <span><code>groupBy</code>, <code>join</code>, <code>repartition</code>, and windows often create a shuffle</span>
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

<style>
</style>

<!--
A stage groups operations that Spark can pipeline without redistributing data. The important boundary is the shuffle. Shuffles are triggered by something called wide transformations
Narrow: transformations for which each input partition will contribute to only one output partition (filter)
Wide: input partitions will contribute to many output partitions
a join is logically a transformation, but whether it creates a wide dependency depends on the physical join strategy.

Here Spark scans, filters, and performs a partial aggregation in Stage 12. The shuffle redistributes records by key. Stage 13 can then finish the aggregation and write the result.

That is why joins, aggregations, repartitioning, and windows matter during an investigation: they often create the boundaries where data moves, waits, or spills.
-->
---
zoom: 0.85
---

# Task

<div class="mental-grid">
  <div class="mental-copy">
    <div class="mental-kicker text-rose-700">A task is…</div>
    <div class="mental-definition"><b>One partition’s</b> unit of work within a stage.</div>
    <div class="mental-detail">
      <b>Where it lives in the UI</b>
      <span>Stage detail → task table and timeline. Skew, slow tasks, GC, and spill become visible here.</span>
    </div>
    <div class="mental-detail">
      <b>The relationship</b>
      <span><code>tasks per stage</code> = <code>partitions in that stage</code>. The tasks run the same code on different data.</span>
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

<style>
</style>

<!--
why does this view matter? They say a chain is only as strong as its weakest link. Well, a stage is only as fast as its slowest task.
 The Task view is useful because job-level or stage-level averages can hide the actual bottleneck.

A task is the same stage logic applied to one partition. Two hundred partitions produce two hundred tasks for that stage.

That relationship makes the task table diagnostic. Most tasks here finish in under half a second, but Task 2 takes more than eight seconds. The stage cannot finish until its slowest task does.

Job-level progress hides this shape. Stage detail reveals skew, stragglers, spill, GC, retries, and shuffle fetch wait at the level where they happen.
-->

---
zoom: 0.85
---

# Executor

<div class="mental-grid">
  <div class="mental-copy">
    <div class="mental-kicker text-emerald-700">An executor is…</div>
    <div class="mental-definition">A worker <b>JVM process</b> that runs tasks in parallel slots</div>
    <div class="mental-detail">
      <b>Where it lives in the UI</b>
      <span>The <code>Executors</code> tab: active tasks, memory, GC time, shuffle, and executor logs.</span>
    </div>
    <div class="mental-detail">
      <b>The math</b>
      <span><code>parallel tasks</code> ≈ <code>executors × cores</code>. With 12 cores available, only about 12 tasks run at once.</span>
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

<style>
</style>

<!--
Executors are the worker processes that perform tasks. Their cores determine how many tasks can run concurrently; the rest wait for a slot.

The Executors tab shows where pressure lands. Compare active tasks, memory use, GC time, shuffle traffic, and failed tasks across executors.

An imbalance can support a skew hypothesis. Pressure across every executor points instead toward a cost shared by the stage, such as broad memory or shuffle pressure.
-->

---
zoom: 0.85
---

# SQL tab

<div class="mental-grid sql-tab-grid">
  <div class="mental-copy">
    <div class="mental-kicker text-amber-700">The SQL tab is…</div>
    <div class="mental-definition">The <b>physical plan</b> Spark actually chose for a SQL or DataFrame query.</div>
    <div class="mental-detail">
      <b>Where it lives in the UI</b>
      <span>The <code>SQL</code> tab in Spark UI or Spark History Server. Select a SQL execution to inspect its physical plan and metrics.</span>
    </div>
    <div class="mental-detail">
      <b>Why useful</b>
      <span>Jobs and stages show <i>what</i> ran. The SQL plan explains <b>why</b>. Connect an expensive stage to a join, aggregation, scan, or write.</span>
    </div>
  </div>
  <div class="mental-panel plan-panel">
    <div class="mental-panel-title">Physical plan · orders JOIN customers</div>
    <div class="mental-plan">
      <div class="plan-branches">
        <div class="plan-branch">
          <div class="mental-plan-node compact">Scan orders</div>
          <div class="plan-line"></div>
          <div class="mental-plan-node compact">HashAggregate</div>
          <div class="plan-line"></div>
          <div class="mental-plan-node exchange">Exchange (hash)<small>shuffle · 18 MB</small></div>
        </div>
        <div class="plan-branch">
          <div class="mental-plan-node compact">Scan customers</div>
          <div class="plan-line"></div>
          <div class="mental-plan-node compact">Filter active</div>
          <div class="plan-line"></div>
          <div class="mental-plan-node exchange">Exchange (hash)<small>shuffle · 4 MB</small></div>
        </div>
      </div>
      <div class="plan-line"></div>
      <div class="mental-plan-node">SortMergeJoin <small>inner · customer_id</small></div>
      <div class="plan-line"></div>
      <div class="mental-plan-node">WriteFiles <small>812 rows · 3.4 MB</small></div>
    </div>
  </div>
</div>

<style>

.sql-tab-grid .mental-copy { gap: 0.7rem; }
.sql-tab-grid .mental-definition { font-size: 1.65rem; }
</style>

<!--
The SQL tab connects the runtime evidence back to the physical work Spark chose. The SQL tab is the query-level explanation of a stage: it shows the operators, exchanges, and metrics that produced the work.

Read this plan top-down. Data flows from the scans down through the Exchanges and sort-merge join to WriteFiles. Both sides pass through an Exchange, so Spark redistributes both datasets before the join; those exchanges explain the stage boundaries visible elsewhere in the UI.

You could also use Graph.

How it relates to Graph:<span>The Fabric History Server's <code>Graph</code> tab shows the job-level DAG and stage flow; SQL shows the operators and exchanges inside one SQL execution. Use Graph to locate the stage, then SQL to explain the work.</span>
-->

---

# What is available in Fabric?

<div class="mt-8">

| Situation | Use |
|---|---|
| Compare runs over time and see anomalies  | **Monitor hub / Recent runs / Monitor run series** |
| You want a first view of run details | **Spark Application detail monitoring** |
| The Spark application is still running | **Live Spark UI** |
| The Spark application completed or failed | **Spark History Server** |
</div>

<!--
-->

---

# Spark application detail monitoring

<div class="mental-eyebrow text-blue-700">A first jump into detail, but higher-level</div>

<img
  src="./images/application_detail_monitoring.png"
  alt="Fabric Spark Application detail monitoring"
  class="detail-monitoring-screenshot"
/>

<style>

.detail-monitoring-screenshot {
  display: block;
  width: 100%;
  max-height: 22rem;
  margin-top: 0.5rem;
  object-fit: contain;
  border: 1px solid #cbd5e1;
  border-radius: 1.25rem;
  box-shadow: 0 0.75rem 1.5rem rgb(15 23 42 / 0.15);
}
</style>

<!--
Effective monitoring of Spark applications enhances performance management and troubleshooting, allowing users to optimize their workflows and quickly identify issues.


Access Spark monitoring details from the Fabric Monitoring Hub or Recent runs panel.
- Jobs tab: View job runs, including Job ID, status, and code snippets.
- Resources tab: Visualize executor usage in real-time.
- Summary panel: Access application details.
- Logs tab: View and download logs for various processes, with filtering options.
- Data tab: Copy or download input/output file information and view properties.
- Item snapshots tab: Browse related items and view snapshots of code and parameters at execution time.
- Diagnostics panel: Receive real-time recommendations and error analysis from Spark Advisor.
-->

---
layout: default
clicks: 6
---

# The Detective's Field Guide

<div class="text-xl opacity-70">Follow the clues...</div>

<DetectiveFieldGuide :active="$clicks" />

<div class="mt-8 text-center text-2xl font-semibold">
  <span v-if="$clicks === 0">A crime has been committed. Follow the evidence to find the culprit.</span>
  <span v-else-if="$clicks < 6">Put each clue under a microscope.</span>
  <span v-else>A case ends with a testable hypothesis.</span>
</div>

<!--
We have enough Spark vocabulary now. We need a route through the evidence. A crime has been committed -> Your Spark job execution was killed by you.

I will use this field guide for every case in the rest of the session. The data and symptoms will change, but these six moves stay fixed.

[click] Find the right run. Check the application, attempt, input volume, and timing before opening low-level metrics.

[click] Choose the right lens. Use the live Spark UI while the application runs. Use History Server after it completes or fails.

[click] Localize the costly stage. Sort by duration and find the stage that accounts for the wall-clock time.

[click] Inspect the task shape. Look past averages. Check whether tasks finish together, form a long tail, spill, wait, or retry.

[click] Correlate that stage with the SQL plan, executors, Fabric Diagnosis views, and logs. Each view should support or challenge the same explanation.

[click] Test one hypothesis. Change one thing, rerun, and compare the same evidence.
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

<!--
Start with the question from the opening: yesterday took 12 minutes and today took 55. Before we diagnose Spark, we need both application records. Confirm that they ran the same notebook or job definition and identify the relevant attempt. Compare input volume, start time, status, and capacity context.

Use Monitor hub when you need to search across workspace activity. Use Recent runs when you begin from a notebook, Spark Job Definition, or pipeline. Open the application details page once you have the application.

Then choose the evidence source. A running application gives us the live Spark UI. A completed or failed application gives us the History Server. The application details page remains useful for resources, logs, and operational context.
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
    <div class="mt-5 text-2xl font-semibold leading-snug">Is the whole application slow or does one stage explain it?</div>
    <ul class="mt-5 text-lg leading-relaxed">
      <li>Sort by duration</li>
      <li>Notice retries or failures</li>
      <li>Look at shuffle, spill and task count</li>
    </ul>
  </div>
</div>

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


<!--
Stage 8 took 36 minutes and 42 seconds. The other visible stages took about one or two minutes. Stage 8 accounts for most of this application's runtime, so it becomes our investigation boundary.

The row gives us early clues. It processed 86 GB of shuffle and spilled 41 GB. Those numbers deserve attention (this is sus), but they do not prove a cause. A large shuffle can be expected. As with a real criminal case we need multiple pieces of evidence to prove someone is guilty. Spill can hurt without explaining the full delay. We need the task detail next.

**Also check failed and retried stages**. A stage may appear several times because Spark retried it, which can hide the true cost if you inspect only the final successful attempt. An unusual task count can expose poor parallelism before you open the stage.
-->

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

<!--
Task distributions reveal what a stage average conceals.

Start on the left. These tasks finish in a narrow range. Balanced does not mean fast; it means no small group of tasks controls the stage duration. If every task is slow, investigate a cost shared across the stage, such as heavy shuffle, spill, CPU work, or external I/O.

The middle shape has a long tail. Most tasks finish, while one task keeps the stage alive. Compare shuffle read and input size per task. One task reading far more data points toward skew. Similar input with one slow task points toward a straggler, executor issue, or external delay.

On the right, many tasks consume substantial time. Check spill, GC time, shuffle fetch wait, scheduler delay, and retries. These metrics separate memory pressure, data movement, scheduling, and unstable execution.

far left vs far right: Both can have the same root cause, such as:

 - large shuffle
 - disk spill
 - high GC
 - expensive CPU work
 - slow external I/O
 - partitions that are too large

Use medians, percentiles, and the task table where available. An average blends the fast majority with the expensive tail.
-->

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
  <div class="rounded-xl bg-amber-50 border border-amber-200 p-4 text-xl"><b>One clue</b><br><span class="text-slate-600">a suspicion and won't hold up in court</span></div>
  <div class="text-4xl text-slate-400">→</div>
  <div class="rounded-xl bg-emerald-50 border border-emerald-200 p-4 text-xl"><b>Independent clues agree</b><br><span class="text-slate-600">a hypothesis worth testing and you might be able to convince a jury</span></div>
</div>

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

<!--
We have localized the stage and read its task shape. Now we need independent evidence.

Keep the stage at the center. In the SQL view, find the operator connected to that stage. Exchanges show shuffle boundaries. The join strategy or aggregation explains why Spark created the expensive work.

Move to Executors when the task metrics suggest memory pressure, GC, or uneven usage. Check whether the pressure appears across executors or concentrates on one worker. A single unhealthy executor tells a different story from every executor spilling.

Fabric adds useful post-mortem evidence. The Diagnosis tab can flag data skew, time skew, and executor usage. The Graph view helps connect jobs and stages. Application and executor logs can confirm fetch failures, repeated loss, or an external error.

Keep one identifier in your head as you move between views: the same stage, task, executor, or SQL node. Opening more tabs does not strengthen a case. Two independent clues that describe the same bottleneck do.

Transition: once the clues agree, phrase a claim that a rerun can disprove.
-->

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
    <span>It has written to disk</span>
  </div>
  <div class="chain-arrow">→</div>
  <div class="hypothesis-box test">
    <div class="box-label">ONE TEST</div>
    <b>Reduce shuffle volume</b>
    <span>Rerun and compare the same stage metrics</span>
  </div>
</div>

<div class="mt-8 text-center text-3xl font-bold">Evidence → hypothesis → test → compare</div>

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

# Let's make this more practical

<DetectiveFieldGuide :active="0" />

<div class="mt-8 grid grid-cols-3 gap-5 text-center">
  <div class="case-card"><b>Case 0</b><span>Data grew and spilled</span></div>
  <div class="case-card"><b>Case 1</b><span>One hot key hid the skew</span></div>
  <div class="case-card"><b>Cases 2–3</b><span>Workers die, or only one works</span></div>
</div>

<div class="mt-10 text-center text-3xl font-bold">Follow the clues.</div>

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

<!--
Case 0   More data, same partitions → spill
Case 1   One hot key → skewed join
Case 2   Partition-sized Python lists → executor loss and retries
Case 3   coalesce(1) → one writer.
-->

---

# Case 0: six years of taxi trips

<div class="grid grid-cols-2 gap-6 mt-6">
  <div class="rounded-2xl border border-blue-200 bg-blue-50 p-6">
    <div class="text-sm font-bold tracking-widest text-blue-700">WHAT THE SCRIPT DOES</div>
    <ol class="mt-4 space-y-3 text-lg text-slate-700">
      <li><b>1.</b> Compare a recent three-month report with the full history.</li>
      <li><b>2.</b> Remove duplicate rides from the records.</li>
      <li><b>3.</b> Count trips and calculate revenue for each month and route.</li>
      <li><b>4.</b> Save the resulting route report.</li>
    </ol>
  </div>
  <div class="rounded-2xl border-2 border-amber-300 bg-amber-50 p-6">
    <div class="text-sm font-bold tracking-widest text-amber-700">WHY IT MIGHT FAIL</div>
    <div class="mt-3 text-2xl font-bold text-slate-900">The report grows, but the work is still split into only eight pieces.</div>
    <p class="mt-4 text-lg text-slate-700">Each piece must remember more rides while it builds the report. The larger workload can push those tasks into memory and disk spill.</p>
  </div>
</div>

<!--
Case 0 uses the official NYC TLC Yellow Taxi dataset: 72 monthly Parquet files from 2019–2024, normalized into about 250 million trips in `nyc_yellow_trips`. The baseline reads October–December 2024; the bad and fixed runs read the full history. Exact counts vary when TLC republishes files.
-->

---
clicks: 3
zoom: 0.85
---

# Case 0: the growing shuffle

<DetectiveFieldGuide :active="$clicks + 3" compact />

<div v-if="$clicks === 0" class="mt-3">
  <div class="text-sm font-bold tracking-widest text-violet-700">3 · LOCALIZE THE COST</div>
  <div class="grid grid-cols-[1.7fr_0.8fr] gap-6 mt-2">
    <div class="case0-stage-list">
      <div class="case0-stage-row header"><span>Stage</span><span>Wall time</span><span>Tasks</span><span>Shuffle</span><span>Disk spill</span></div>
      <div class="case0-stage-row"><span>Other completed stages</span><span>10.9s</span><span>172</span><span>negligible</span><span>0</span></div>
      <div class="case0-stage-row scan"><span><b>11</b> · scan + partial aggregate</span><span><b>72.9s</b></span><span>53</span><span>7.93 GB write</span><span>0</span></div>
      <div class="case0-stage-row suspect"><span><b>13</b> · final aggregate + write</span><span><b>109.7s</b></span><span><b>8</b></span><span>7.93 GB read</span><span><b>7.33 GB</b></span></div>
    </div>
    <div class="case0-verdict violet">
      <span>DOMINANT PATH</span>
      <b>182.6s</b>
      <small>of the 217.2s application runtime</small>
      <p>Open Stage 13 first. It lasts longest and is the only stage that spills to disk.</p>
    </div>
  </div>
</div>

<div v-else-if="$clicks === 1" class="mt-3">
  <div class="text-sm font-bold tracking-widest text-rose-700">4 · INSPECT THE TASK SHAPE</div>
  <div class="grid grid-cols-[1.6fr_0.75fr] gap-6 mt-2">
    <div class="case0-task-chart">
      <div class="case0-task-head"><span>Task</span><span>Duration</span><span>Shuffle read</span><span>Disk spill</span></div>
      <div class="case0-task-row"><b>0</b><span><i style="width:94%"></i>103.1s</span><span>1.01 GB</span><span>0.93 GB</span></div>
      <div class="case0-task-row"><b>1</b><span><i style="width:84%"></i>92.0s</span><span>0.84 GB</span><span>0.78 GB</span></div>
      <div class="case0-task-row"><b>2</b><span><i style="width:89%"></i>97.4s</span><span>0.92 GB</span><span>0.85 GB</span></div>
      <div class="case0-task-row"><b>3</b><span><i style="width:98%"></i>107.2s</span><span>1.10 GB</span><span>1.01 GB</span></div>
      <div class="case0-task-row"><b>4</b><span><i style="width:93%"></i>102.1s</span><span>1.00 GB</span><span>0.92 GB</span></div>
      <div class="case0-task-row"><b>5</b><span><i style="width:90%"></i>98.7s</span><span>0.95 GB</span><span>0.88 GB</span></div>
      <div class="case0-task-row"><b>6</b><span><i style="width:100%"></i>109.6s</span><span>1.11 GB</span><span>1.02 GB</span></div>
      <div class="case0-task-row"><b>7</b><span><i style="width:95%"></i>103.9s</span><span>1.01 GB</span><span>0.93 GB</span></div>
    </div>
    <div class="case0-verdict rose">
      <span>THE SHAPE</span>
      <b>92–110s</b>
      <small>all 8 tasks spill</small>
      <p>No long tail. Every reducer carries about 1 GB of shuffle input and writes temporary data to disk.</p>
    </div>
  </div>
</div>

<div v-else-if="$clicks === 2" class="mt-3">
  <div class="text-sm font-bold tracking-widest text-amber-700">5 · CORRELATE THE CLUES</div>
  <div class="case0-plan mt-3">
    <div><b>Scan</b><small>259.3M rows</small></div><i>→</i>
    <div><b>HashAggregate</b><small>partial deduplication</small></div><i>→</i>
    <div class="exchange"><b>Exchange</b><small>hashpartitioning(PU, DO, <strong>8</strong>)</small></div><i>→</i>
    <div><b>HashAggregate</b><small>final route statistics</small></div>
  </div>
  <div class="grid grid-cols-3 gap-4 mt-5">
    <div class="case0-clue"><span>SQL PLAN</span><b>25.1 GiB shuffle stage</b><small>The Exchange fixes the reducer count at 8.</small></div>
    <div class="case0-clue"><span>STAGE 13</span><b>44.44 GB memory spill</b><small>7.33 GB reaches disk; fetch wait is ~0s.</small></div>
    <div class="case0-clue"><span>EXECUTORS</span><b>1 executor · 8 cores</b><small>All eight reducers run; the work is not waiting for task slots.</small></div>
  </div>
  <div class="mt-5 text-center text-xl font-semibold">The plan creates eight oversized reducer partitions; the task metrics show the cost.</div>
</div>

<div v-else class="mt-3">
  <div class="text-sm font-bold tracking-widest text-emerald-700">6 · TEST ONE HYPOTHESIS</div>
  <div class="case0-hypothesis mt-3">
    <div class="evidence"><span>EVIDENCE</span><b>259M rows ÷ 8 reducers</b><small>≈ 1 GB shuffle input and ≈ 0.9 GB disk spill per task</small></div>
    <i>→</i>
    <div class="hypothesis"><span>HYPOTHESIS</span><b>The shuffle is under-partitioned</b><small>Each aggregation task crosses its memory threshold.</small></div>
    <i>→</i>
    <div class="test"><span>ONE CHANGE</span><b>8 → at least 256 partitions</b><small>Eight cores process the smaller tasks in waves. Same input, smaller per-task state.</small></div>
  </div>
</div>

<style>
.case0-stage-list,
.case0-task-chart {
  overflow: hidden;
  border: 1px solid #cbd5e1;
  border-radius: 0.9rem;
  background: white;
}
.case0-stage-row {
  display: grid;
  grid-template-columns: 1.75fr 0.65fr 0.5fr 0.9fr 0.7fr;
  align-items: center;
  border-top: 1px solid #e2e8f0;
  padding: 0.9rem 0.8rem;
  color: #334155;
  font-size: 0.76rem;
}
.case0-stage-row.header {
  border: 0;
  background: #f1f5f9;
  color: #64748b;
  font-size: 0.63rem;
  font-weight: 900;
  text-transform: uppercase;
}
.case0-stage-row.scan { background: #eff6ff; }
.case0-stage-row.suspect { border-left: 0.35rem solid #7c3aed; background: #faf5ff; color: #4c1d95; }
.case0-verdict {
  display: flex;
  flex-direction: column;
  justify-content: center;
  border: 1px solid;
  border-radius: 0.9rem;
  padding: 1.2rem;
  text-align: center;
}
.case0-verdict.violet { border-color: #c4b5fd; background: #f5f3ff; color: #5b21b6; }
.case0-verdict.rose { border-color: #fda4af; background: #fff1f2; color: #be123c; }
.case0-verdict > span,
.case0-clue > span,
.case0-hypothesis span,
.case0-compare > span {
  font-size: 0.65rem;
  font-weight: 900;
  letter-spacing: 0.11em;
}
.case0-verdict > b { margin-top: 0.6rem; font-size: 2rem; }
.case0-verdict small { font-size: 0.75rem; }
.case0-verdict p { margin: 1rem 0 0; color: #475569; font-size: 0.82rem; line-height: 1.3; }
.case0-task-head,
.case0-task-row {
  display: grid;
  grid-template-columns: 0.35fr 2fr 0.8fr 0.75fr;
  align-items: center;
  gap: 0.5rem;
  padding: 0.32rem 0.7rem;
  color: #334155;
  font-size: 0.68rem;
}
.case0-task-head { background: #f1f5f9; color: #64748b; font-size: 0.6rem; font-weight: 900; text-transform: uppercase; }
.case0-task-row { border-top: 1px solid #f1f5f9; }
.case0-task-row > span:first-of-type { position: relative; height: 1.1rem; border-radius: 0.25rem; background: #f1f5f9; line-height: 1.1rem; text-align: right; }
.case0-task-row i { position: absolute; inset: 0 auto 0 0; z-index: -1; max-width: calc(100% - 3.2rem); border-radius: 0.25rem; background: #fda4af; }
.case0-task-row span { isolation: isolate; }
.case0-plan {
  display: grid;
  grid-template-columns: 1fr auto 1.2fr auto 1.3fr auto 1.2fr;
  align-items: center;
  gap: 0.7rem;
}
.case0-plan > div {
  border: 1px solid #cbd5e1;
  border-radius: 0.75rem;
  background: white;
  padding: 0.75rem;
  text-align: center;
}
.case0-plan > div.exchange { border: 2px solid #f59e0b; background: #fffbeb; color: #92400e; }
.case0-plan small { display: block; margin-top: 0.25rem; color: #64748b; font-size: 0.67rem; }
.case0-plan > i { color: #94a3b8; font-size: 1.6rem; font-style: normal; font-weight: 900; }
.case0-clue { border: 1px solid #cbd5e1; border-radius: 0.8rem; background: #f8fafc; padding: 0.9rem; }
.case0-clue > span { color: #64748b; }
.case0-clue b { display: block; margin-top: 0.35rem; color: #0f172a; font-size: 1rem; }
.case0-clue small { display: block; margin-top: 0.3rem; color: #64748b; font-size: 0.72rem; }
.case0-hypothesis {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr;
  align-items: stretch;
  gap: 0.7rem;
}
.case0-hypothesis > div { display: flex; min-height: 12rem; flex-direction: column; justify-content: center; border: 2px solid #cbd5e1; border-radius: 1rem; padding: 1rem; text-align: center; }
.case0-hypothesis > i { align-self: center; color: #94a3b8; font-size: 2rem; font-style: normal; }
.case0-hypothesis .evidence { background: #f8fafc; }
.case0-hypothesis .hypothesis { border-color: #f59e0b; background: #fffbeb; }
.case0-hypothesis .test { border-color: #22c55e; background: #f0fdf4; }
.case0-hypothesis b { margin-top: 0.6rem; font-size: 1.1rem; }
.case0-hypothesis small { margin-top: 0.5rem; color: #64748b; font-size: 0.75rem; }
.case0-compare { display: grid; grid-template-columns: 1.2fr repeat(4, 1fr); gap: 0.5rem; align-items: center; border-radius: 0.75rem; background: #0f172a; padding: 0.8rem 1rem; color: white; text-align: center; }
.case0-compare > span { color: #94a3b8; text-align: left; }
.case0-compare b { font-size: 0.75rem; }
</style>

<!--

3 · LOCALIZE
Open Spark History Server → Stages. In Completed Stages, sort by Duration.
Stage 13 lasts 109.7 seconds and has only 8 tasks. Its row shows 7.93 GB shuffle read and 7.33 GB disk spill. Stage 11 lasts 72.9 seconds and writes the same 7.93 GB shuffle. Together these stages consume 182.6 seconds of the 217.2-second application runtime.

Open Stage 13 because it is the longest stage and the spill appears there.

[click]
4 · INSPECT
On the Stage 13 detail page, use Summary Metrics for Completed Tasks and the Tasks table. Sort by Duration, Shuffle Read Size, and Disk Spill.

The upstream tasks divide their output into eight shuffle partitions; Stage 13 starts one reducer task for each partition. Each reducer fetches all records assigned to its partition and runs the final deduplication and aggregation for those records.

This deduplication has many distinct keys, so the reducer must retain a large amount of aggregation state instead of processing each row and forgetting it. Eight reducers also run concurrently and share the executor's execution-memory pool.

 During an aggregation, sort, or join, Spark keeps intermediate state in the executor’s execution memory. If that state no longer fits, Spark writes part of it to temporary files on the executor’s local disk. That is disk spill. 
 That extra serialization, disk I/O, and merging makes the stage slower. This is separate from the normal shuffle files produced at the Exchange: the Disk Spill metric records extra temporary I/O caused by memory pressure.

 A small amount can be normal. A large amount usually indicates that tasks are processing too much data or have too little execution memory.

[click]
5 · CORRELATE
Open Spark History Server → SQL and select the write execution. In the final physical plan, follow the scan through HashAggregate to Exchange. The Exchange details show hashpartitioning on pickup and drop-off location with 8 partitions. The shuffle stage carries 259.3 million rows and an estimated 25.1 GiB.
Return to Stage 13 to connect that Exchange to 8 reducer tasks, 44.44 GB memory spill, and 7.33 GB disk spill
In Executors, executor 1 has 8 cores. All eight reducer tasks can run at once. 

[click]
6 · TEST
State the hypothesis: the historical input grew, but the shuffle stayed at eight partitions. Each reducer now owns too much aggregation state and spills to disk. Increasing the partition count will create smaller tasks that run in waves; it does not require more cores to reduce each task's aggregation state.

Why do more partitions help when the executor count stays the same? Executors determine how many tasks run at once; partitions determine how much data and aggregation state each task owns. With one 8-core executor and 8 partitions, all eight large tasks run together, and each competes for execution memory while holding about one eighth of the shuffle. With 256 partitions, the executor still runs only eight tasks at once, but each task owns roughly one thirty-second as much data. Spark processes the 256 smaller tasks in about 32 waves. Completed tasks release their memory before the next wave starts.

The change does not add CPU or reduce the total input. It trades extra task-scheduling overhead for a much smaller peak memory requirement per task. Avoiding repeated spill and merge I/O can save more time than those extra tasks cost. More is not always better: partitions that are too small add scheduling and file overhead. At least 256 is the hypothesis for this run, not a universal Spark setting.

Run the fixed application with the same full-history input and business logic, changing only spark.sql.shuffle.partitions from 8 to at least 256.
-->

---

# Case 0: recorded walkthrough

<video controls class="case-video" src="./videos/case0_recording.mp4"></video>

<style>
.case-video {
  display: block;
  width: 100%;
  max-height: 27rem;
  object-fit: contain;
}
</style>

---

# Case 1: enrich trips with fare rules

<div class="grid grid-cols-2 gap-6 mt-6">
  <div class="rounded-2xl border border-blue-200 bg-blue-50 p-6">
    <div class="text-sm font-bold tracking-widest text-blue-700">WHAT THE SCRIPT DOES</div>
    <ol class="mt-4 space-y-3 text-lg text-slate-700">
      <li><b>1.</b> Read 2022–2024 trips.</li>
      <li><b>2.</b> Turn <code>RatecodeID</code> into a <code>fare_rule</code>.</li>
      <li><b>3.</b> Left-join eight rule descriptions.</li>
      <li><b>4.</b> Write the enriched trips to Parquet.</li>
    </ol>
  </div>
  <div class="rounded-2xl border-2 border-amber-300 bg-amber-50 p-6">
    <div class="text-sm font-bold tracking-widest text-amber-700">WHY IT MIGHT FAIL</div>
    <div class="mt-3 text-2xl font-bold text-slate-900">A tiny dimension does not guarantee a healthy shuffled join.</div>
    <p class="mt-4 text-lg text-slate-700">The demo disables broadcast and forces a sort-merge join. Most trips share <code>STANDARD</code>, so hashing the join key can send almost all rows to one reducer.</p>
  </div>
</div>

---
clicks: 3
zoom: 0.85
---

# Case 1: the standard-rate hot key

<DetectiveFieldGuide :active="$clicks + 3" compact />

<div v-if="$clicks === 0" class="mt-3">
  <div class="text-sm font-bold tracking-widest text-violet-700">3 · LOCALIZE THE COST</div>
  <div class="grid grid-cols-[1.7fr_0.8fr] gap-6 mt-2">
    <div class="case1-stage-list">
      <div class="case1-stage-row header"><span>Evidence</span><span>Wall time</span><span>Tasks</span><span>Shuffle</span></div>
      <div class="case1-stage-row"><span>Main SQL write execution</span><span><b>186.1s</b></span><span>—</span><span>—</span></div>
      <div class="case1-stage-row scan"><span><b>Stage 4</b> · fact scan + exchange</span><span>41.8s</span><span>29</span><span>3.63 GiB write</span></div>
      <div class="case1-stage-row suspect"><span><b>Stage 8</b> · join + parquet write</span><span><b>142.3s</b></span><span><b>256</b></span><span><b>3.63 GiB read</b></span></div>
    </div>
    <div class="case1-verdict violet">
      <span>DOMINANT STAGE</span>
      <b>142.3s</b>
      <small>76% of the 186.1s SQL execution</small>
      <p>Open Stage 8. The scan finishes; the final join stage holds the application open.</p>
    </div>
  </div>
</div>

<div v-else-if="$clicks === 1" class="mt-3">
  <div class="text-sm font-bold tracking-widest text-rose-700">4 · INSPECT THE TASK SHAPE</div>
  <div class="grid grid-cols-[1.6fr_0.75fr] gap-6 mt-2">
    <div class="case1-task-chart">
      <div class="case1-task-head"><span>Partition</span><span>Duration</span><span>Shuffle read</span><span>Rows read</span></div>
      <div class="case1-task-row hot"><b>75</b><span><i style="width:100%"></i>142.23s</span><span>3.24 GiB</span><span>105.72M</span></div>
      <div class="case1-task-row"><b>96</b><span><i style="width:12%"></i>16.52s</span><span>222.4 MiB</span><span>6.77M</span></div>
      <div class="case1-task-row"><b>143</b><span><i style="width:9%"></i>12.84s</span><span>112.9 MiB</span><span>4.38M</span></div>
      <div class="case1-task-row median"><b>Median</b><span><i style="width:1%"></i>0.116s</span><span>0 B</span><span>0</span></div>
    </div>
    <div class="case1-verdict rose">
      <span>THE LONG TAIL</span>
      <b>1.226×</b>
      <small>max duration ÷ median</small>
      <p>Partition 75 receives 88.7% of all join rows. Only 8 of 256 tasks read any shuffle data.</p>
    </div>
  </div>
</div>

<div v-else-if="$clicks === 2" class="mt-3">
  <div class="text-sm font-bold tracking-widest text-amber-700">5 · CORRELATE THE CLUES</div>
  <div class="case1-plan mt-3">
    <div><b>Scan</b><small>119.14M rows</small></div><i>→</i>
    <div class="exchange"><b>Exchange</b><small>hash(fare_rule, 256)</small></div><i>→</i>
    <div><b>SortMergeJoin</b><small>LeftOuter</small></div><i>→</i>
    <div><b>WriteFiles</b><small>119.14M rows</small></div>
  </div>
  <div class="grid grid-cols-3 gap-4 mt-5">
    <div class="case1-clue"><span>DIAGNOSIS · DATA SKEW</span><b>3,319.71 MB max</b><small>versus 14.54 MB mean task data read</small></div>
    <div class="case1-clue"><span>DIAGNOSIS · TIME SKEW</span><b>142.23s max</b><small>versus 0.88s mean task duration</small></div>
    <div class="case1-clue"><span>STAGE 8</span><b>0 spill · 0 fetch wait</b><small>The straggler is processing the hot partition, not waiting on disk or network.</small></div>
  </div>
</div>

<div v-else class="mt-3">
  <div class="text-sm font-bold tracking-widest text-emerald-700">6 · TEST ONE HYPOTHESIS</div>
  <div class="case1-hypothesis mt-3">
    <div class="evidence"><span>EVIDENCE</span><b>105.72M of 119.14M rows</b><small>88.7% of join rows land in partition 75.</small></div>
    <i>→</i>
    <div class="hypothesis"><span>HYPOTHESIS</span><b><code>STANDARD</code> is the hot key</b><small>Hashing <code>fare_rule</code> alone sends it to one reducer.</small></div>
    <i>→</i>
    <div class="test"><span>ONE CHANGE</span><b>Add 8,192 deterministic salts</b><small>Replicate the 8-row rule table across salts; keep 256 shuffle partitions.</small></div>
  </div>
</div>

<style>
.case1-stage-list,
.case1-task-chart {
  overflow: hidden;
  border: 1px solid #cbd5e1;
  border-radius: 0.9rem;
  background: white;
}
.case1-stage-row {
  display: grid;
  grid-template-columns: 1.8fr 0.65fr 0.5fr 0.9fr;
  align-items: center;
  border-top: 1px solid #e2e8f0;
  padding: 0.95rem 0.85rem;
  color: #334155;
  font-size: 0.78rem;
}
.case1-stage-row.header {
  border: 0;
  background: #f1f5f9;
  color: #64748b;
  font-size: 0.63rem;
  font-weight: 900;
  text-transform: uppercase;
}
.case1-stage-row.scan { background: #eff6ff; }
.case1-stage-row.suspect { border-left: 0.35rem solid #7c3aed; background: #faf5ff; color: #4c1d95; }
.case1-verdict {
  display: flex;
  flex-direction: column;
  justify-content: center;
  border: 1px solid;
  border-radius: 0.9rem;
  padding: 1.2rem;
  text-align: center;
}
.case1-verdict.violet { border-color: #c4b5fd; background: #f5f3ff; color: #5b21b6; }
.case1-verdict.rose { border-color: #fda4af; background: #fff1f2; color: #be123c; }
.case1-verdict > span,
.case1-clue > span,
.case1-hypothesis span,
.case1-compare > span {
  font-size: 0.65rem;
  font-weight: 900;
  letter-spacing: 0.11em;
}
.case1-verdict > b { margin-top: 0.6rem; font-size: 2rem; }
.case1-verdict small { font-size: 0.75rem; }
.case1-verdict p { margin: 1rem 0 0; color: #475569; font-size: 0.82rem; line-height: 1.3; }
.case1-task-head,
.case1-task-row {
  display: grid;
  grid-template-columns: 0.55fr 2fr 0.85fr 0.75fr;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  color: #334155;
  font-size: 0.72rem;
}
.case1-task-head { background: #f1f5f9; color: #64748b; font-size: 0.6rem; font-weight: 900; text-transform: uppercase; }
.case1-task-row { border-top: 1px solid #f1f5f9; }
.case1-task-row.hot { background: #fff1f2; color: #9f1239; }
.case1-task-row.median { color: #64748b; }
.case1-task-row > span:first-of-type { position: relative; height: 1.2rem; border-radius: 0.25rem; background: #f1f5f9; line-height: 1.2rem; text-align: right; }
.case1-task-row i { position: absolute; inset: 0 auto 0 0; z-index: 0; border-radius: 0.25rem; background: #93c5fd; }
.case1-task-row.hot i { background: #fb7185; }
.case1-task-row span { isolation: isolate; }
.case1-plan {
  display: grid;
  grid-template-columns: 1fr auto 1.25fr auto 1.15fr auto 1fr;
  align-items: center;
  gap: 0.7rem;
}
.case1-plan > div {
  border: 1px solid #cbd5e1;
  border-radius: 0.75rem;
  background: white;
  padding: 0.75rem;
  text-align: center;
}
.case1-plan > div.exchange { border: 2px solid #f59e0b; background: #fffbeb; color: #92400e; }
.case1-plan small { display: block; margin-top: 0.25rem; color: #64748b; font-size: 0.67rem; }
.case1-plan > i { color: #94a3b8; font-size: 1.6rem; font-style: normal; font-weight: 900; }
.case1-clue { border: 1px solid #cbd5e1; border-radius: 0.8rem; background: #f8fafc; padding: 0.9rem; }
.case1-clue > span { color: #64748b; }
.case1-clue b { display: block; margin-top: 0.35rem; color: #0f172a; font-size: 1rem; }
.case1-clue small { display: block; margin-top: 0.3rem; color: #64748b; font-size: 0.72rem; }
.case1-hypothesis {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr;
  align-items: stretch;
  gap: 0.7rem;
}
.case1-hypothesis > div { display: flex; min-height: 12rem; flex-direction: column; justify-content: center; border: 2px solid #cbd5e1; border-radius: 1rem; padding: 1rem; text-align: center; }
.case1-hypothesis > i { align-self: center; color: #94a3b8; font-size: 2rem; font-style: normal; }
.case1-hypothesis .evidence { background: #f8fafc; }
.case1-hypothesis .hypothesis { border-color: #f59e0b; background: #fffbeb; }
.case1-hypothesis .test { border-color: #22c55e; background: #f0fdf4; }
.case1-hypothesis b { margin-top: 0.6rem; font-size: 1.1rem; }
.case1-hypothesis small { margin-top: 0.5rem; color: #64748b; font-size: 0.75rem; }
.case1-compare { display: grid; grid-template-columns: 1.2fr repeat(4, 1fr); gap: 0.5rem; align-items: center; border-radius: 0.75rem; background: #0f172a; padding: 0.8rem 1rem; color: white; text-align: center; }
.case1-compare > span { color: #94a3b8; text-align: left; }
.case1-compare b { font-size: 0.75rem; }
</style>

<!--
3 · LOCALIZE
The event log records a 186.1-second write execution and a final physical plan ending in WriteFiles.
Open Stages and sort Completed Stages by Duration. Stage 8 is the parquet join-and-write stage: 256 tasks, 142.3 seconds, and 3.63 GiB of shuffle read. It consumes about 76% of the SQL execution. Stage 4 scans 119,136,044 fact rows and writes the same 3.63 GiB shuffle in 41.8 seconds, so the scan completes; the final stage explains the long tail.

[click]
4 · INSPECT

**Only eight of the 256 tasks have nonzero shuffle read because the join key has only eight rule values. That alone is not the diagnosis. The decisive clue is that one partition owns 88.7% of all shuffle records; the next largest partitions read only 6.77 million and 4.38 million rows.**

Open Stage 8. First look at the event timeline: Task 89, for partition 75, starts with the first wave and extends almost to the end of the stage while the other task bars disappear.
In Summary Metrics for Completed Tasks, compare maximum, mean, and median duration. Then use the Tasks table and sort by Duration and Shuffle Read Size. Partition 75 lasts 142.23 seconds, reads 3.24 GiB and 105,720,908 records, and writes 105,720,907 output rows. The median task lasts 0.116 seconds, making the maximum 1,226 times the median.

[click]
5 · CORRELATE
In SQL, open the final physical plan for execution 1. Follow the fact scan to Exchange hashpartitioning(fare_rule, 256), Sort, SortMergeJoin LeftOuter, and WriteFiles. The final plan reports 119.14 million rows on the fact-side ShuffleQueryStage and only eight rows on the rule side. Broadcasting is disabled in this demo, so both sides pass through an Exchange and the shuffled join remains visible.
Now open Diagnosis for job 5. Data Skew flags Stage 8 with 3,319.71 MB maximum task data read versus 14.54 MB mean. Time Skew flags the same stage with 142.23 seconds maximum versus 0.88 seconds mean. These values are persisted as Fabric advice events in case1_logs_bad; they independently confirm what the task table shows.
Return to Stage 8 and check spill and shuffle fetch wait. Both total zero. The hot task spends 125.4 seconds of CPU time during its 142.2-second duration. In Executors, the application has one eight-core executor; after the short tasks finish, one core remains occupied by the hot partition while the other slots have no comparable work. This rules out disk spill and network wait and supports data skew at the join.

[click]
6 · TEST
State one hypothesis: the STANDARD fare rule is shared by most Yellow Taxi rows. Hashing fare_rule alone sends all STANDARD records to one of the 256 reducer partitions, producing the 105.72-million-row task.

Explain the solution in plain language: a **salt** is an extra deterministic bucket number added to the join key. Give each trip a salt from 0 to 8,191, then copy the eight-row rule table once for every salt and join on `(fare_rule, salt)`. The STANDARD trips are now spread across many `(STANDARD, salt)` partitions instead of one hot `STANDARD` partition. This is not password encryption; it is a partitioning trick to break up a hot key.

8192 = 256 (shuffle partitions) × 32  8192 is explicitly specified and the exact value is somewhat arbitrary. It is just a tuning parameter

Be upfront that broadcasting the eight-row rule table would work even better here, and would remove the skew problem entirely rather than just spreading it out: with a broadcast join there is no shuffle on the fact side at all, so no single reducer can ever become a hot spot.

It adds one of 8,192 deterministic salts to each trip, replicates the eight-row rule dimension across those salts, and joins on fare_rule plus salt.
-->

---

# Case 1: recorded walkthrough

<video controls class="case-video" src="./videos/case1_recording.mp4"></video>

<style>
.case-video {
  display: block;
  width: 100%;
  max-height: 27rem;
  object-fit: contain;
}
</style>

---

# Case 2: a tiny report, a huge Python list

<div class="grid grid-cols-2 gap-6 mt-6">
  <div class="rounded-2xl border border-blue-200 bg-blue-50 p-6">
    <div class="text-sm font-bold tracking-widest text-blue-700">WHAT THE SCRIPT DOES</div>
    <ol class="mt-4 space-y-3 text-lg text-slate-700">
      <li><b>1.</b> Read 259.29 million trips from 2019–2024.</li>
      <li><b>2.</b> Spread them across eight round-robin partitions.</li>
      <li><b>3.</b> Profile every column in Python on the executors.</li>
      <li><b>4.</b> Write 21 rows: row count and null count per column.</li>
    </ol>
  </div>
  <div class="rounded-2xl border-2 border-amber-300 bg-amber-50 p-6">
    <div class="text-sm font-bold tracking-widest text-amber-700">WHY IT MIGHT FAIL</div>
    <div class="mt-3 text-2xl font-bold text-slate-900">Each worker keeps its entire partition before counting anything.</div>
    <p class="mt-4 text-lg text-slate-700">About 32.4 million Python dictionaries per task. An ordinary Python list cannot spill to disk like Spark's managed operators.</p>
  </div>
</div>

<!--
The business output is a null-count profile: 21 normalized columns become 21 report rows. The bad mapPartitions function first evaluates [row.asDict() for row in rows], retaining every dictionary. The fixed function uses a generator expression and retains only the current record and column counters. This is executor-side Python, NOT a driver collect() or toPandas(). The 21-row output is observed in the fixed run; the bad captures never reach a completed report.

t means Spark can automatically move some of its own intermediate data from memory to local disk, but it cannot do that for arbitrary Python objects your code creates. Python code creates millions of dictionaries of all rows.

 A Python list is just an in-memory object. Spark does not inspect it and decide which elements to write to disk. The Python worker owns it, outside Spark’s managed aggregation/sort/join memory structures. If
 memory becomes exhausted, the Python process or executor may be killed.

 Spark-managed operators such as hash aggregation, sorting, and shuffling use spill-aware data structures:

PREPARE THE UI
Open Fabric Recent runs / Monitor hub → the bad Spark Job Definition run → application details → Spark History Server. Confirm application_1790060503449_0001 and choose application attempt 2. Keep attempt 1 available to show recurrence, but do not mix their task IDs or timelines. Open the fixed application_1790065465428_0001, attempt 1, in another tab. Stage IDs 10, 11, and 12 happen to match across these captures; identify their work, not just their numbers.

Start with Jobs → job 5, labelled CASE 2 BAD: unbounded Python partition profiling. Its DAG connects the completed scan/shuffle Stage 10 to Python profiling Stage 11 and the final aggregate/write Stage 12. The stage call site says save; expand the Stage 11 DAG to find PythonRDD and ShuffledRowRDD. SQL alone does not expose the body of the Python function.

The rehearsal reported the bad workload still running after roughly an hour; that is not a completed runtime. The supplied bad event logs have no ApplicationEnd or final job outcome. If the run was subsequently cancelled, label it cancelled, not completed. Do not present the hour as an event-log-measured duration or compute a speedup against it.
-->

---
clicks: 3
zoom: 0.85
---

# Case 2: the executor keeps disappearing

<DetectiveFieldGuide :active="$clicks + 3" compact />

<div v-if="$clicks === 0" class="mt-3">
  <div class="text-sm font-bold tracking-widest text-violet-700">3 · LOCALIZE THE COST · BAD APPLICATION ATTEMPT 2</div>
  <div class="grid grid-cols-[1.7fr_0.8fr] gap-6 mt-2">
    <div class="case2-stage-list">
      <div class="case2-stage-row header"><span>Stage / work</span><span>Duration</span><span>Tasks</span><span>Evidence</span></div>
      <div class="case2-stage-row scan"><span><b>10</b> · scan + repartition</span><span>187.4s</span><span>53</span><span>13.74 GiB write</span></div>
      <div class="case2-stage-row suspect"><span><b>11</b> · Python profiling</span><span>unfinished</span><span>8</span><span><b>16 failed attempts</b></span></div>
      <div class="case2-stage-row"><span><b>12</b> · aggregate + write</span><span>not started</span><span>8 planned</span><span>No report yet</span></div>
    </div>
    <div class="case2-verdict violet">
      <span>PROFILING PROGRESS</span>
      <b>0 of 8</b>
      <small>partitions completed in this capture</small>
      <p>The scan succeeds. The Python stage loses its workers instead of finishing.</p>
    </div>
  </div>
</div>

<div v-else-if="$clicks === 1" class="mt-3">
  <div class="text-sm font-bold tracking-widest text-rose-700">4 · INSPECT THE TASK SHAPE · BAD APPLICATION ATTEMPT 2</div>
  <div class="grid grid-cols-[1.6fr_0.75fr] gap-6 mt-2">
    <div class="case2-task-chart">
      <div class="case2-task-head"><span>Stage 11</span><span>Task attempt</span><span>Time running</span><span>Outcome</span></div>
      <div class="case2-task-row"><b>Executor 1</b><span>0 · all 8 tasks</span><span>189.8s</span><span>Exit 137</span></div>
      <div class="case2-task-row"><b>Executor 2</b><span>1 · all 8 tasks</span><span>350.8s</span><span>Exit 137</span></div>
      <div class="case2-task-row"><b>Retry again</b><span>2 · all 8 tasks</span><span>08:15:51 UTC</span><span>Driver log</span></div>
    </div>
    <div class="case2-verdict rose">
      <span>FAIL TOGETHER</span>
      <b>8 → 0 → 8</b>
      <small>running tasks disappear, then restart</small>
      <p>Two executor kills cause 16 failed task attempts. Not 16 independent OOMs.</p>
    </div>
  </div>
  <div class="mt-4 text-sm text-slate-600">Attempt 1 repeats the pattern: two executor kills and 16 failed task attempts.</div>
</div>

<div v-else-if="$clicks === 2" class="mt-3">
  <div class="text-sm font-bold tracking-widest text-amber-700">5 · CORRELATE THE CLUES</div>
  <pre class="mt-3 rounded-xl bg-slate-900 p-4 text-base text-white"><code>ExecutorLostFailure · Exit status: 137
Container killed on request. Killed by external signal.</code></pre>
  <div class="grid grid-cols-3 gap-4 mt-4">
    <div class="case2-clue"><span>EXECUTORS + ENVIRONMENT</span><b>8 tasks share one executor</b><small>56 GiB JVM heap + 384 MiB overhead. Python memory is outside the JVM heap.</small></div>
    <div class="case2-clue"><span>FABRIC ADVICE / DRIVER LOG</span><b>Memory-related diagnosis</b><small>Spark_System_Executor_ExitCode137BadNode. No measured Python RSS in these logs.</small></div>
    <div class="case2-clue"><span>EVIDENCE LIMIT</span><b>Exit 137 ≠ proof of OOM</b><small>Same host, “bad node” diagnostics. Failed-task memory metrics are missing, not zero.</small></div>
  </div>
  <div class="mt-4 text-center text-xl font-semibold">Confirmed: repeated container kills. Suspect: the partition-sized Python list.</div>
</div>

<div v-else class="mt-3">
  <div class="text-sm font-bold tracking-widest text-emerald-700">6 · TEST ONE HYPOTHESIS</div>
  <div class="case2-hypothesis mt-3">
    <div class="evidence"><span>EVIDENCE</span><b>The Python stage repeatedly loses executors</b><small>The upstream scan and shuffle complete.</small></div>
    <i>→</i>
    <div class="hypothesis"><span>HYPOTHESIS</span><b>Unbounded Python state exhausts memory</b><small>Millions of dictionaries per worker; no automatic list spill.</small></div>
    <i>→</i>
    <div class="test"><span>CODE CHANGE</span><b>Stream instead of buffer</b><small>Keep eight partitions and the same input. Retain only a row and column counters.</small></div>
  </div>
</div>

<style>
.case2-stage-list,
.case2-task-chart {
  overflow: hidden;
  border: 1px solid #cbd5e1;
  border-radius: 0.9rem;
  background: white;
}
.case2-stage-row {
  display: grid;
  grid-template-columns: 1.8fr 0.65fr 0.5fr 0.9fr;
  align-items: center;
  border-top: 1px solid #e2e8f0;
  padding: 0.72rem 0.85rem;
  color: #334155;
  font-size: 0.75rem;
}
.case2-stage-row.header {
  border: 0;
  background: #f1f5f9;
  color: #64748b;
  font-size: 0.63rem;
  font-weight: 900;
  text-transform: uppercase;
}
.case2-stage-row.scan { background: #eff6ff; }
.case2-stage-row.suspect { border-left: 0.35rem solid #7c3aed; background: #faf5ff; color: #4c1d95; }
.case2-verdict {
  display: flex;
  flex-direction: column;
  justify-content: center;
  border: 1px solid;
  border-radius: 0.9rem;
  padding: 1.2rem;
  text-align: center;
}
.case2-verdict.violet { border-color: #c4b5fd; background: #f5f3ff; color: #5b21b6; }
.case2-verdict.rose { border-color: #fda4af; background: #fff1f2; color: #be123c; }
.case2-verdict > span,
.case2-clue > span,
.case2-hypothesis span,
.case2-compare > span {
  font-size: 0.65rem;
  font-weight: 900;
  letter-spacing: 0.11em;
}
.case2-verdict > b { margin-top: 0.6rem; font-size: 2rem; }
.case2-verdict small { font-size: 0.75rem; }
.case2-verdict p { margin: 1rem 0 0; color: #475569; font-size: 0.82rem; line-height: 1.3; }
.case2-task-head,
.case2-task-row {
  display: grid;
  grid-template-columns: 1.2fr repeat(3, 1fr);
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem;
  color: #334155;
  font-size: 0.75rem;
  text-align: right;
}
.case2-task-head { background: #f1f5f9; color: #64748b; font-size: 0.6rem; font-weight: 900; text-transform: uppercase; }
.case2-task-head span:first-child,
.case2-task-row b:first-child { text-align: left; }
.case2-task-row { border-top: 1px solid #f1f5f9; }
.case2-task-row.healthy { background: #f0fdf4; color: #166534; }
.case2-clue { border: 1px solid #cbd5e1; border-radius: 0.8rem; background: #f8fafc; padding: 0.9rem; }
.case2-clue > span { color: #64748b; }
.case2-clue b { display: block; margin-top: 0.35rem; color: #0f172a; font-size: 1rem; }
.case2-clue small { display: block; margin-top: 0.3rem; color: #64748b; font-size: 0.72rem; }
.case2-hypothesis { display: grid; grid-template-columns: 1fr auto 1fr auto 1fr; align-items: stretch; gap: 0.7rem; }
.case2-hypothesis > div { display: flex; min-height: 12rem; flex-direction: column; justify-content: center; border: 2px solid #cbd5e1; border-radius: 1rem; padding: 1rem; text-align: center; }
.case2-hypothesis > i { align-self: center; color: #94a3b8; font-size: 2rem; font-style: normal; }
.case2-hypothesis .evidence { background: #f8fafc; }
.case2-hypothesis .hypothesis { border-color: #f59e0b; background: #fffbeb; }
.case2-hypothesis .test { border-color: #22c55e; background: #f0fdf4; }
.case2-hypothesis b { margin-top: 0.6rem; font-size: 1.1rem; }
.case2-hypothesis small { margin-top: 0.5rem; color: #64748b; font-size: 0.75rem; }
.case2-compare { display: grid; grid-template-columns: 1.2fr repeat(4, 1fr); gap: 0.5rem; align-items: center; border-radius: 0.75rem; background: #0f172a; padding: 0.8rem 1rem; color: white; text-align: center; }
.case2-compare > span { color: #94a3b8; text-align: left; }
.case2-compare b { font-size: 0.75rem; }
</style>

<!--
3 · LOCALIZE — BAD APPLICATION ATTEMPT 2
In Spark History Server → Jobs → job 5, open the DAG. Then Stages → Stage 10: 53 successful tasks, 187.407 seconds, 259,287,888 input records, and 14,751,508,097 shuffle bytes written (13.74 GiB). The scan succeeds with zero recorded spill. Stage 11 is the unfinished Python profiling stage with eight partitions. Stage 12 has not been submitted in this capture. Do not search only Completed Stages: the problematic stage is still active/incomplete in the supplied log.

Open Stage 11 even though its call site is save at NativeMethodAccessorImpl.java:0. Its DAG/RDD details contain ShuffledRowRDD → PythonRDD → applySchemaToPythonRDD → partial aggregation. This is where the arbitrary Python code runs, not just the final Delta write.

Source anchors: case2_mem_bad_attempt2:553 (Stage 10 completed), :554 (Stage 11 submitted), :564–573 and :586–593 (task failures). No successful Stage 11 task or final application outcome is present in either bad capture.

[click]
4 · INSPECT — TASK ATTEMPTS, NOT ONE SKEWED STRAGGLER
Stage 11 → Tasks: show failed tasks, then compare Index/partition, Attempt, Executor ID, Launch Time, Duration, and Errors. Expand ExecutorLostFailure. The same indices 0–7 recur with task attempt 0 on executor 1 and attempt 1 on executor 2. The stage itself remains stage attempt 0; these are task retries, distinct from the application's two attempts.

Expand the Event Timeline. In application attempt 2, the first eight tasks run from 08:06:28.694 to 08:09:38.521 UTC (189.827s). The next eight run from 08:09:49.653 to 08:15:40.409 (350.756s). Times may display in the browser's local timezone. All eight bars end together because a single executor dies, not because eight independent Python exceptions were observed. Two distinct executor losses produce 16 task failures.

The bad event log ends after executor 3 registers. The third batch of task starts at 08:15:51 is additional DRIVER-LOG evidence, case2_stderr:6038–6045; do not promise that it is visible in the supplied event-log timeline. If demonstrating from these snapshots, stop the UI walkthrough after the second loss and show that driver-log excerpt separately.

Optional: switch to application attempt 1. Stage 10 takes 114.466s; Stage 11 loses all eight tasks after 194.130s, then again after 276.466s. Return to attempt 2 afterward. Do not add the duplicate ExecutorRemoved events as extra dead executors. Across the two captures there are four distinct executor containers killed and 32 failed task attempts.

[click]
5 · CORRELATE — EXECUTORS, ENVIRONMENT, LOGS
Open Executors and include dead/removed executors. Inspect executors 1 and 2 and their removal reasons: exit 137, Container killed on request, Killed by external signal. In Environment → Spark Properties, find spark.executor.memory=56g, spark.executor.memoryOverhead=384m, spark.executor.cores=8, and spark.dynamicAllocation.maxExecutors=1. These are allocation settings, NOT measured peak usage. All eight profiling tasks share that one executor container.

Return to Fabric application details → Logs → Driver → stderr. Search for Lost executor, ExecutorLostFailure, 137, or Spark_System_Executor_ExitCode137BadNode. Use case2_stderr:5154–5201 for the first loss, :5956–6003 for the second, and :5216 for Fabric's memory-related advice. If the dead executor's stderr link says log listing unavailable, use the driver-log download; do not let a broken link derail the walkthrough. The Fabric advice may also appear in the application's diagnostics; the driver excerpt is the reliable fallback, not Diagnosis > Data Skew.

Interpret carefully: exit 137 is SIGKILL, not by itself proof of OOM. Fabric's advice calls it memory-related, but the raw messages also say bad node and all bad-run losses occur on the same host. There is no measured Python RSS or explicit used-X/exceeded-Y memory diagnostic. The JVM OnOutOfMemoryError launch option in stderr is not an actual OOM exception.

Failed Stage 11 tasks have no Task Metrics records: blank/zero-looking UI cells do not prove zero spill or low GC. Python objects are outside JVM heap accounting; Executors Storage Memory is cached Spark blocks, not total container memory. Do not sum per-task peak metrics and call that the executor's physical memory. Case 0 spilled managed state; this suspect is an ordinary Python list that cannot spill.

[click]
6 · TEST — CHANGE THE RETENTION, THEN CHECK THE EXPERIMENT
Show the two comprehension lines. Square brackets materialize every row; parentheses make a generator. The counters and report schema stay the same. The profiler's retained state changes from proportional to partition size to proportional to the number of columns. More partitions or more memory can postpone the bad allocation; streaming removes the need to retain those records.

Switch to the fixed run on the next slide. It completes, but inspect Environment and task placement before saying only one thing changed: this recorded fixed run used TWO concurrent executors, with four profiling tasks each, versus one executor with eight tasks in the bad run. That lowers memory competition too. Treat completion as supporting evidence, not an isolated proof of the code fix. A controlled follow-up would rerun fixed with the bad run's one-executor allocation, keeping the same input and eight partitions; configure resources before session launch.


FIXED:
case2_mem_fixed records application_1790065465428_0001, attempt 1. SparkListenerApplicationStart at line 6 and ApplicationEnd at line 738 give 631.761 seconds = 10m31.761s (the reported approximately 11 minutes). This excludes any Fabric queue/pool startup before Spark's application-start event. All 283 TaskEnd events are Success, all eight jobs succeed, and all 14 submitted stages complete.

LIVE WALKTHROUGH — FIXED RUN
1. Fabric Recent runs → fixed application details → History Server. Confirm the FIXED job description, application ID, and attempt 1. Jobs shows all jobs completed; do not compare this duration to an invented one-hour completed bad run.
2. Stages → Stage 10: 53 tasks, 99.170s, 259,287,888 input records, 14,751,508,097 shuffle bytes. Compare with bad Stage 10 to establish that the historical workload did not disappear. Source: case2_mem_fixed:561.
3. Stages → Stage 11: 461.505s, eight successful tasks and no retries. Open Tasks and sort Shuffle Read Records: minimum 32,410,983, maximum 32,410,989. Each partition carries essentially the same row count: this is not a hot-key distribution. Task durations span 380.123–461.493s, with median 420.658s. The timeline shows eight tasks completing, not batches repeatedly being killed. Source: :563–580 task events, :581 stage completion.
4. In Stage 11's Summary Metrics / task columns, show zero memory spill and zero disk spill for the completed fixed tasks. This is measured only for the fixed tasks, not the failed bad tasks, and does not measure Python RSS. Shuffle read still totals 13.74 GiB: the fix does not remove the shuffle. Its partial aggregate emits 168 records (8 partitions × 21 columns), writing only 7,320 bytes to the final shuffle.
5. Stage 12 → task Output Records: the total is 21; two of its eight tasks have no rows. Stage wall time is 25.475s, including scheduling/resource handover, not 25 seconds of Python profiling. Source: :603. SQL → execution 8 shows Scan ExistingRDD → partial HashAggregate → Exchange hashpartitioning(column_name, 8) → final HashAggregate; inspect the final aggregate's number of output rows = 21. The ExistingRDD starts AFTER the Python boundary, so the list/generator itself is not visible in this SQL plan. If challenged on result correctness, 21 rows proves report shape, not each null count; use the separate native-count verification in CASES.md.

IMPORTANT CONTROL CHECK — SHOW THIS, DO NOT HIDE IT
Open Environment → Spark Properties in BOTH applications. Bad spark.dynamicAllocation.maxExecutors=1; fixed=2. Both have spark.executor.cores=8, spark.executor.memory=56g, spark.executor.memoryOverhead=384m. In fixed Stage 11 → Tasks, show Executor ID: partitions 0,2,4,6 run on executor 1; partitions 1,3,5,7 run on executor 2. All eight start together, four per executor. Thus the fixed capture doubles the available executor memory and halves concurrent profiling tasks per executor. A successful run supports the diagnosis but cannot attribute the entire improvement to the generator alone. The next controlled test is fixed with the bad run's one-executor allocation.

Open Executors → removed executors / event timeline. Fixed executor 2 is removed with 'Executor decommission: spark scale down'; executor 1 with 'Executor decommission: Asked to decommission 1'. Executor 3 is subsequently added. These are decommission events, NOT the bad run's exit-137 failures; no fixed task fails. Merely seeing removed executors is not evidence of OOM. Sources: case2_mem_fixed:576, :583, :585.

TAKEAWAY
The useful contrast is stalled/retried work versus a completed report, not a fabricated speedup ratio. Distinguish observed container kills, Fabric's automated memory diagnosis, the code-level hypothesis, and the resource difference in the test. In production, native Spark SQL null-count aggregates would avoid this Python row-by-row path altogether; streaming here isolates the retention pattern in the code
-->

---

# Case 3: export one gzip CSV

<div class="grid grid-cols-2 gap-6 mt-6">
  <div class="rounded-2xl border border-blue-200 bg-blue-50 p-6">
    <div class="text-sm font-bold tracking-widest text-blue-700">WHAT THE SCRIPT DOES</div>
    <ol class="mt-4 space-y-3 text-lg text-slate-700">
      <li><b>1.</b> Read 2023–2024 trips.</li>
      <li><b>2.</b> Format timestamps and select ten columns.</li>
      <li><b>3.</b> Combine the rows with <code>coalesce(1)</code>.</li>
      <li><b>4.</b> Write a headered, gzip-compressed CSV.</li>
    </ol>
  </div>
  <div class="rounded-2xl border-2 border-amber-300 bg-amber-50 p-6">
    <div class="text-sm font-bold tracking-widest text-amber-700">WHY IT MIGHT FAIL</div>
    <div class="mt-3 text-2xl font-bold text-slate-900">The output contract can erase Spark's parallelism.</div>
    <p class="mt-4 text-lg text-slate-700"><code>coalesce(1)</code> funnels every row into one task. That task must format, serialize, compress, and write the entire gzip stream while the other executor slots wait.</p>
  </div>
</div>

---
clicks: 3
zoom: 0.85
---

# Case 3: the single-file bottleneck

<DetectiveFieldGuide :active="$clicks + 3" compact />

<div v-if="$clicks === 0" class="mt-3">
  <div class="text-sm font-bold tracking-widest text-violet-700">3 · LOCALIZE THE COST</div>
  <div class="grid grid-cols-[1.7fr_0.8fr] gap-6 mt-2">
    <div class="case2-stage-list">
      <div class="case2-stage-row header"><span>Evidence</span><span>Wall time</span><span>Tasks</span><span>Shuffle</span></div>
      <div class="case2-stage-row"><span>Application</span><span><b>572.605s</b></span><span>53 total</span><span>—</span></div>
      <div class="case2-stage-row scan"><span>Delta metadata stages</span><span>up to 5.402s</span><span>1–50</span><span>small</span></div>
      <div class="case2-stage-row suspect"><span><b>Stage 4</b> · CSV write</span><span><b>538.062s</b></span><span><b>1</b></span><span><b>0 B</b></span></div>
    </div>
    <div class="case2-verdict violet">
      <span>THE MAIN SQL EXECUTION</span>
      <b>99.8%</b>
      <small>spent in Stage 4</small>
      <p>The final CSV stage contains one task and accounts for 538.062 of 539.045 seconds.</p>
    </div>
  </div>
</div>

<div v-else-if="$clicks === 1" class="mt-3">
  <div class="text-sm font-bold tracking-widest text-rose-700">4 · INSPECT THE TASK SHAPE</div>
  <div class="grid grid-cols-[1.6fr_0.75fr] gap-6 mt-2">
    <div class="case2-task-chart">
      <div class="case2-task-head"><span>Stage 4 evidence</span><span>Count</span><span>Time</span><span>Data</span></div>
      <div class="case2-task-row"><b>Task 52 · partition 0</b><span><b>1 task</b></span><span><b>537.949s</b></span><span><b>79.48M rows</b></span></div>
      <div class="case2-task-row"><b>Input</b><span>29 files</span><span>—</span><span>1.45 GiB read</span></div>
      <div class="case2-task-row"><b>Output</b><span>1 gzip file</span><span>—</span><span>1.18 GiB written</span></div>
      <div class="case2-task-row healthy"><b>Pressure checks</b><span>0 B spill</span><span>0.944s GC</span><span>0 B shuffle</span></div>
    </div>
    <div class="case2-verdict rose">
      <span>AVAILABLE TASK SLOTS</span>
      <b>1 of 8</b>
      <small>occupied during the write</small>
      <p>The only task uses 508.366 seconds of CPU. Seven executor slots have no task to run.</p>
    </div>
  </div>
</div>

<div v-else-if="$clicks === 2" class="mt-3">
  <div class="text-sm font-bold tracking-widest text-amber-700">5 · CORRELATE THE CLUES</div>
  <div class="case0-plan mt-3">
    <div><b>Scan parquet</b><small>24 partitions · 29 files</small></div><i>→</i>
    <div><b>Project</b><small>format timestamps and select 10 columns</small></div><i>→</i>
    <div class="exchange"><b>Coalesce 1</b><small>one output partition</small></div><i>→</i>
    <div><b>WriteFiles</b><small>CSV · gzip</small></div>
  </div>
  <div class="grid grid-cols-3 gap-4 mt-5">
    <div class="case2-clue"><span>SQL PLAN</span><b><code>Coalesce 1</code>, no Exchange</b><small>The funnel sits directly before <code>WriteFiles</code>.</small></div>
    <div class="case2-clue"><span>EXECUTOR EVENT</span><b>1 executor · 8 cores</b><small>Stage 4 schedules one task, requesting one CPU, on executor 1.</small></div>
    <div class="case2-clue"><span>WRITE METRICS</span><b>1 file · 79,479,946 rows</b><small>The task writes 1,271,759,612 compressed bytes.</small></div>
  </div>
  <div class="mt-5 text-center text-xl font-semibold">The source exposes 24 partitions; <code>coalesce(1)</code> funnels every row into one writer task.</div>
</div>

<div v-else class="mt-3">
  <div class="text-sm font-bold tracking-widest text-emerald-700">6 · TEST ONE HYPOTHESIS</div>
  <div class="case2-hypothesis mt-3">
    <div class="evidence"><span>EVIDENCE</span><b>79.48M rows through 1 task</b><small>537.949 seconds while seven task slots remain unused</small></div>
    <i>→</i>
    <div class="hypothesis"><span>HYPOTHESIS</span><b>The one-file contract serializes the write</b><small>One task formats every row and produces one gzip stream.</small></div>
    <i>→</i>
    <div class="test"><span>ONE CHANGE</span><b><code>coalesce(1)</code> → at least 64 partitions</b><small>Keep the rows and gzip CSV format; write a folder of part files.</small></div>
  </div>
</div>

<style>
.case2-stage-list,
.case2-task-chart {
  overflow: hidden;
  border: 1px solid #cbd5e1;
  border-radius: 0.9rem;
  background: white;
}
.case2-stage-row {
  display: grid;
  grid-template-columns: 1.8fr 0.65fr 0.5fr 0.9fr;
  align-items: center;
  border-top: 1px solid #e2e8f0;
  padding: 0.72rem 0.85rem;
  color: #334155;
  font-size: 0.75rem;
}
.case2-stage-row.header {
  border: 0;
  background: #f1f5f9;
  color: #64748b;
  font-size: 0.63rem;
  font-weight: 900;
  text-transform: uppercase;
}
.case2-stage-row.scan { background: #eff6ff; }
.case2-stage-row.suspect { border-left: 0.35rem solid #7c3aed; background: #faf5ff; color: #4c1d95; }
.case2-verdict {
  display: flex;
  flex-direction: column;
  justify-content: center;
  border: 1px solid;
  border-radius: 0.9rem;
  padding: 1.2rem;
  text-align: center;
}
.case2-verdict.violet { border-color: #c4b5fd; background: #f5f3ff; color: #5b21b6; }
.case2-verdict.rose { border-color: #fda4af; background: #fff1f2; color: #be123c; }
.case2-verdict > span,
.case2-clue > span,
.case2-hypothesis span,
.case2-compare > span {
  font-size: 0.65rem;
  font-weight: 900;
  letter-spacing: 0.11em;
}
.case2-verdict > b { margin-top: 0.6rem; font-size: 2rem; }
.case2-verdict small { font-size: 0.75rem; }
.case2-verdict p { margin: 1rem 0 0; color: #475569; font-size: 0.82rem; line-height: 1.3; }
.case2-task-head,
.case2-task-row {
  display: grid;
  grid-template-columns: 1.2fr repeat(3, 1fr);
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem;
  color: #334155;
  font-size: 0.75rem;
  text-align: right;
}
.case2-task-head { background: #f1f5f9; color: #64748b; font-size: 0.6rem; font-weight: 900; text-transform: uppercase; }
.case2-task-head span:first-child,
.case2-task-row b:first-child { text-align: left; }
.case2-task-row { border-top: 1px solid #f1f5f9; }
.case2-task-row.healthy { background: #f0fdf4; color: #166534; }
.case0-plan {
  display: grid;
  grid-template-columns: 1fr auto 1.2fr auto 1.3fr auto 1.2fr;
  align-items: center;
  gap: 0.7rem;
}
.case0-plan > div {
  border: 1px solid #cbd5e1;
  border-radius: 0.75rem;
  background: white;
  padding: 0.75rem;
  text-align: center;
}
.case0-plan > div.exchange { border: 2px solid #f59e0b; background: #fffbeb; color: #92400e; }
.case0-plan small { display: block; margin-top: 0.25rem; color: #64748b; font-size: 0.67rem; }
.case0-plan > i { color: #94a3b8; font-size: 1.6rem; font-style: normal; font-weight: 900; }
.case2-clue { border: 1px solid #cbd5e1; border-radius: 0.8rem; background: #f8fafc; padding: 0.9rem; }
.case2-clue > span { color: #64748b; }
.case2-clue b { display: block; margin-top: 0.35rem; color: #0f172a; font-size: 1rem; }
.case2-clue small { display: block; margin-top: 0.3rem; color: #64748b; font-size: 0.72rem; }
.case2-hypothesis { display: grid; grid-template-columns: 1fr auto 1fr auto 1fr; align-items: stretch; gap: 0.7rem; }
.case2-hypothesis > div { display: flex; min-height: 12rem; flex-direction: column; justify-content: center; border: 2px solid #cbd5e1; border-radius: 1rem; padding: 1rem; text-align: center; }
.case2-hypothesis > i { align-self: center; color: #94a3b8; font-size: 2rem; font-style: normal; }
.case2-hypothesis .evidence { background: #f8fafc; }
.case2-hypothesis .hypothesis { border-color: #f59e0b; background: #fffbeb; }
.case2-hypothesis .test { border-color: #22c55e; background: #f0fdf4; }
.case2-hypothesis b { margin-top: 0.6rem; font-size: 1.1rem; }
.case2-hypothesis small { margin-top: 0.5rem; color: #64748b; font-size: 0.75rem; }
.case2-compare { display: grid; grid-template-columns: 1.2fr repeat(4, 1fr); gap: 0.5rem; align-items: center; border-radius: 0.75rem; background: #0f172a; padding: 0.8rem 1rem; color: white; text-align: center; }
.case2-compare > span { color: #94a3b8; text-align: left; }
.case2-compare b { font-size: 0.75rem; }
</style>

<!--
3 · LOCALIZE
It lasts 539.045 seconds. The complete application lasts 572.605 seconds; the remaining time includes startup and short Delta metadata work.

Open Stages and sort by Duration. Stage 4, named for the CSV call site, lasts 538.062 seconds and contains one task. It accounts for 99.8% of the main SQL execution. The longest metadata stage lasts 5.402 seconds. Open Stage 4 because the single output stage explains the runtime without adding durations from stages that ran for metadata.

[click]
4 · INSPECT
The executor-added event records one executor with eight cores, and the resource profile assigns one CPU to each task. Stage 4 can therefore occupy only one of eight task slots. The event log proves poor Spark task parallelism; it does not contain a persisted Fabric Executor Usage advice event, so do not quote a Diagnosis percentage for this run.

Open Stage 4. Its event timeline contains one bar: Task 52 for partition 0 runs for 537.949 seconds. The task reads 79,479,946 records and 1,556,145,733 bytes, then writes the same 79,479,946 records and 1,271,759,612 gzip-compressed bytes. The SQL output metrics confirm one written file.
The task spends 537.760 seconds in executor run time and 508.366 seconds on executor CPU. JVM garbage collection takes 0.944 seconds. Memory spill, disk spill, shuffle read, and shuffle write are all zero. This is not a skewed distribution because there is no distribution: one task owns the whole write.


[click]
5 · CORRELATE
Open the physical plan for SQL execution 1. Read it from Scan parquet through ColumnarToRow, Filter, Project, Coalesce, WriteFiles, and Execute InsertIntoHadoopFsRelationCommand. The Project formats both timestamp columns and selects the ten CSV columns. Coalesce has the argument 1 and sits immediately before WriteFiles.
There is no Exchange in this plan. The scan metrics report 24 source partitions and 29 files, but coalesce(1) combines that input into one output partition. Stage 4 consequently launches one task, and that task performs the scan, timestamp formatting, CSV serialization, gzip compression, and output write.
Correlate the plan with the executor and output events. Executor 1 has eight cores, but the stage offers one task. Write metrics report one file, 79,479,946 rows, and 1,271,759,612 bytes. Job commit takes only 328 milliseconds, so commit overhead does not explain the nine-minute stage. The serial data path does.

[click]
6 · TEST
State one hypothesis: coalesce(1) enforces a one-partition, one-file contract, so Spark cannot spread CSV formatting and gzip compression across the eight available task slots.
It replaces coalesce(1) with repartition(OUTPUT_PARTITIONS), where OUTPUT_PARTITIONS is at least 64. The rows, columns, CSV format, and gzip compression stay the same. The contract changes from one file to a folder of gzip part files. 
Repartitioning may add an Exchange and shuffle; that is the cost of creating parallel output partitions.
-->
---

# Case 3: recorded walkthrough

<video controls class="case-video" src="./videos/case3_recording.mp4"></video>

<style>
.case-video {
  display: block;
  width: 100%;
  max-height: 27rem;
  object-fit: contain;
}
</style>

<!--
You will see that there is one stage which still takes some time. If you open that, you will see that stage actually has no quirky metrics, nothing out of the ordinary

This might actually be a bad example because the full execution of the fixed case seems to be taking longer. But the actual execution is taking a lot less time:
Yes—for the full application comparison, mostly.

┌─────────────────────────────┬────────┬───────┐
│ Interval                    │ Bad    │ Fixed │
├─────────────────────────────┼────────┼───────┤
│ App start → main SQL starts │ 36.2s  │ 73.1s │
├─────────────────────────────┼────────┼───────┤
│ Main SQL execution          │ 102.0s │ 57.1s │
├─────────────────────────────┼────────┼───────┤
│ SQL end → app end           │ 1.9s   │ 3.9s  │
└─────────────────────────────┴────────┴───────┘


The join was actually removed here, so the stage is not present
-->

---
class: emfcc-end
---

<div class="emfcc-visually-hidden">Please rate this session in the conference app.</div>

<!--
Leave this official conference rating slide on screen for questions.
-->
