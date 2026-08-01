---
name: stress-test
description: >
  Raise the load on a running system until it stops keeping up, find the knee, name what
  gave first, and report how much headroom sits between that point and the real peak.
disable-model-invocation: true
---

Every system has a **knee**: the load at which throughput stops rising and latency starts
climbing. Below it, adding load adds work done. Above it, adding load adds only waiting. The
knee is one number, it moves whenever the code or the data changes, and almost nobody knows
where theirs is.

Finding it is the job. Then two things follow. **What gave first** — the connection pool, one
pinned core, the garbage collector, a query without an index — because a knee with no cause
named is a number nobody can act on. And **headroom**: the knee divided by the peak the system
actually has to serve. Headroom is the figure someone outside the team can use, and the only
one that answers "are we going to be fine".

The run has to be honest to be worth anything, and the standard way it stops being honest is
quiet. A load generator that waits for each response before sending the next stops sending when
the system stalls — so the slowest requests are never made, never recorded, and the report comes
back with a p99 that a real peak walks straight through. Step 2 exists for that alone.

## This skill reports

Steps 1 to 8 run the load and write up what happened. The production code stays exactly as it
is. That report is the whole deliverable.

Steps 9 and 10 run only on a **fix signal**: "fix it", "raise the knee", "make it faster", "go
ahead". The step 8 report is the *before*, so it is written on a fix run too, and written before
anything is changed.

## 1. Build the load model

A load test is only ever a guess about users, and an unexamined guess produces a confident
number about traffic nobody sends. Write the guess down.

| Ask | Where the answer lives |
| --- | --- |
| Which journeys carry the traffic | access logs, analytics, the APM's top routes by count |
| The share each takes | the same, as a percentage — not an even split across endpoints |
| The rate at peak | requests per second at the busiest minute of the busiest day, not the daily average |
| Think time | the gap between a real person's actions, which is what stops a script from behaving like a benchmark |
| The mix of reads and writes | writes cost more and lock more; a read-only script finds a knee that does not exist |
| Data variety | distinct users, distinct ids, distinct search terms. One id repeated is a cache test |

Then the number everything is measured against: **the expected peak.** Today's busiest minute,
and where the business expects it to be in a year. Headroom is meaningless without it, and a
peak nobody wrote down becomes whatever number makes the report look best.

Where the traffic data does not exist, say so and state the model as an assumption in the
report. An assumption on the page can be argued with; one in your head cannot.

**Done when:** every journey carries its share, its rate at peak, and its think time; the data
each needs is named; the expected peak is written down with its source; and every figure with no
evidence behind it is marked as an assumption.

## 2. Make the measurement honest

Two settings decide whether any number below means anything.

**Use an open model.** A **closed** model runs a fixed number of virtual users, each waiting for
its response before sending again. An **open** model sends at a fixed arrival rate, whether or
not the last one came back. Real users are open: a person clicking a link does not wait for your
other users' requests to finish.

The difference is not academic. Little's Law says concurrency equals throughput times latency,
so 50 virtual users at 200ms cannot exceed 250 requests per second however fast the system gets
— the generator caps the system before the system does, and you measure your own script.

Worse, a closed model **stops sending when the system stalls**. The requests that would have
been the slowest are never made, so they are never recorded, and the percentiles come back
describing a system that was asked to do less exactly when it was struggling. That is
**coordinated omission**, and it is the single commonest reason a load test passes and the real
peak does not. Record each request's latency from the time it was **due** to be sent, not the
time it actually went.

Then three things about the environment, because a knee is a fact about a system *and* the box
it runs on:

- **Size it like production**, or record the ratio. A knee found on a laptop transfers to
  production only as an order of magnitude.
- **Fill the database.** A query that is instant over 500 rows and hopeless over 5 million is
  the most common knee there is, and an empty test database hides it completely.
- **Warm up, and discard the warm-up.** Caches fill, connection pools open, JIT compiles. Those
  first seconds are a different system and they drag every percentile.

Last, make sure you will be able to read the answer. Latency percentiles and error rate from the
generator; CPU, memory, and garbage collection from the host or runtime; pool usage, queue depth,
and slow queries from the application and the database. A run that finds the knee and cannot say
what gave has to be run again.

**Done when:** the generator is set to a constant arrival rate with latency recorded against
intended send time, the environment's size and data volume are recorded against production's, a
warm-up is applied and excluded, and every signal step 6 needs can be read for the whole run.

## 3. Set the scope, the abort condition, and the authorization

A stress test is an outage you scheduled. Decide the limits before the first run, because the
moment to stop is not a judgement you can make well while a graph is climbing.

- **The target.** A dedicated environment needs only your own decision. **Shared staging or
  production needs recorded authorization** — who approved it, when, the hosts and services in
  scope, and the window. No authorization, no run.
- **Third parties are out of scope by default.** A load test that sends real traffic to a
  payment sandbox, an email provider, or another team's service is a bill, a rate limit, and
  somebody else's incident. Stub them, and note in the report that their latency is simulated.
- **The abort condition, as a number.** Error rate above a figure, latency past a ceiling, or
  any sign the environment itself is in trouble. Write it down and honour it.
- **The stop command, tested.** Run it once before you start, while nothing is wrong.

**Done when:** the environment, the in-scope targets, the stubbed third parties, the
authorization where the environment is shared, the abort condition as a number, and a stop
command already proved to work are all written down.

## 4. Pick the generator

Prefer the tool the project already has. Otherwise:

| Language or protocol | Tool |
| --- | --- |
| HTTP, scripted in JavaScript | k6, Artillery |
| HTTP, scripted in Python | Locust |
| HTTP, scripted in Scala or Java | Gatling |
| HTTP, no script — one endpoint at a rate | Vegeta, wrk2, hey, oha, bombardier |
| HTTP, JVM shop with existing plans | Apache JMeter |
| gRPC | ghz, k6 with its gRPC module |
| WebSocket or streaming | k6, Artillery |
| Database on its own | the engine's own bench tool — `pgbench`, `sysbench` |

The one thing to check in whichever you pick: **can it hold a constant arrival rate?** k6 has a
constant-arrival-rate executor, Gatling injects a constant rate of users, Artillery is built
around an arrival rate, and Vegeta and wrk2 send at a fixed rate by design — wrk2 exists
because of the problem in step 2. Where a tool only offers a fixed pool of virtual users, you
are running a closed model and step 2 says what that costs.

### Nothing installed?

Most of these are a single binary and need no place in the manifest, which makes this cheaper
than it looks. Check first: the manifest and lockfile, the CI workflows, a `k6/` or `load/`
folder, and the binary on `PATH`.

Where the project genuinely has none, put the setup to the user in one message — the tool and
why it fits this project, the exact install command, whether it lands in the manifest or only on
the machine, and the download size — and wait for the go-ahead. Then install exactly that and
commit nothing beyond the script itself, which belongs in the repo so the next run is the same
run.

Read the tool's own docs for its current options. Flag names drift between versions, and an
arrival-rate setting written from memory silently falls back to a closed model, which is the one
mistake this skill is built to prevent.

**Done when:** the tool was already present or the user approved its setup, its
constant-arrival-rate mode is confirmed from its own documentation, the script lives in the
repo, and a one-minute trial run produces latency percentiles and an error rate.

## 5. Run the shapes, and find the knee

Five shapes, five different questions. Run them in this order — each one is cheap insurance
against wasting the next.

| Shape | Load | Runs for | Answers |
| --- | --- | --- | --- |
| **Smoke** | one or two users | a minute | does the script work at all, before an hour is spent on it |
| **Load** | the expected peak from step 1 | 10 to 30 minutes | does it hold at the number the business expects |
| **Stress** | raised in steps past the peak | until the knee | where the knee is, and what gives |
| **Soak** | the expected peak, steady | hours | does anything drift that a short run cannot see |
| **Spike** | peak to several times peak in seconds | minutes | does a sudden arrival survive, and does it recover after |

**The stress run is the one that finds the knee.** Raise the arrival rate in steps, hold each
step long enough to settle — a few minutes, not seconds — and record throughput, latency
percentiles, and error rate at each. The knee is the step where **throughput stops rising while
latency keeps climbing**. Past it you are adding queue, not work.

Record the shape of the curve past the knee, because two very different things happen there.
Throughput that **plateaus** is a system holding its limit. Throughput that **falls** is
congestion collapse — retries and queues actively making it worse — and it is much the more
serious of the two, because it means overload does not stabilise on its own.

The soak run needs no larger load, only time. Watch memory, connection counts, file handles,
disk, and consumer lag against a straight line. Anything that only ever climbs is a leak, and it
will end the process eventually whatever the knee says.

The spike run has two halves and the second is the one people forget: it arrives, and then it
has to come back. Record how long after the spike the system returns to its normal latency.

**Done when:** all five shapes have run or are recorded as skipped with a reason; the stress run
has a table of arrival rate against throughput, latency percentiles, and error rate at every
step; the knee is named with the step either side of it; the curve past the knee is described as
a plateau or a collapse; the soak run's drift figures are recorded against a straight line; and
the spike run has both its survival and its recovery time.

## 6. Name what gave first

A knee with no cause is a number. Read the resource signals from step 2 across the stress run
and find the one that saturated as throughput went flat.

| What the run did | Usually |
| --- | --- |
| throughput flat, latency climbing, CPU well under full | a pool or a queue — requests are waiting for a resource, not for work |
| throughput flat, one core pinned | single-threaded work: a lock, a serialization step, a blocked event loop |
| throughput flat, every core pinned | genuinely CPU bound. The code itself is the limit |
| latency in steps rather than a curve | garbage collection, or a batch or flush interval |
| throughput falling past the knee | congestion collapse — retries piling onto an overloaded system |
| latency steady, errors climbing | a limit rejecting cleanly: a rate limiter, a fail-fast pool, a connection cap |
| database busy, application idle | the query, the index, or the row count |
| fine until well into the run | a leak — memory, connections, file handles, or disk |

Prove it rather than matching a row: the signal that saturated should flatten at the same step
the throughput does, and relieving it should move the knee. Where two saturate together, say so
— naming one bottleneck out of two is how a fix delivers nothing.

Then compute the number the report leads with:

> **headroom = the knee ÷ the expected peak**

Headroom under 1 means the system cannot serve today's peak. Between 1 and 2 means one busy day
or one bad deploy away from trouble. What counts as enough is the project's call, and traffic
that can double without warning needs more than traffic that grows a few percent a month.

**Done when:** one bottleneck is named with the signal that saturated and the step it saturated
at, or two are named where two saturated together; headroom is computed against the step 1
expected peak; and every finding from the soak and spike runs carries its own cause.

## 7. Work out the gates

Three recommendations, none applied here:

**Run the smoke shape on every pull request.** A minute, and it keeps the script working. A load
script that has quietly rotted is discovered on the day somebody needs it most.

**Run the load shape on a schedule** against a stable environment, and judge it on a **latency
budget** rather than on a raw number. Machines differ and cloud neighbours differ, so a gate
pinned to an absolute millisecond figure fails for reasons nobody can act on.

**Judge new work on regression, not on absolutes.** A change that moves p95 at the expected peak
by more than an agreed percentage is worth a conversation before it merges. Comparing a run to
the last run on the same environment is the only comparison that holds.

The stress, soak, and spike shapes do not belong on a pull request. They take too long and they
need an environment nobody minds you breaking.

**Done when:** all three are written down with the workflow file each would live in, the shapes
that are deliberately not gated are named, and no CI file has been edited.

## 8. Write the report

Header: the timestamp from `date '+%Y-%m-%d-%H%M%S'`, the commit from `git rev-parse --short
HEAD`, and a note if the working tree is dirty. Record the environment and its size beside them,
because a knee only holds for the box it was measured on.

Write to `<module>/.reports/stress-report-<timestamp>.md`. `<module>` is the nearest directory at
or above the scope holding the project's manifest (`package.json`, `go.mod`, `pyproject.toml`,
`pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`, `*.csproj`); a run spanning several writes
to the repository root. Create the folder if missing, add `.reports/` to the root `.gitignore` if
nothing there covers it, one file per run, never overwrite an older one.

Report one number and one verdict:

> **headroom = the knee ÷ the expected peak**

and the **soak verdict**, a pass only when nothing drifted over the long run. A system with
three times the headroom it needs and a memory leak is a system that falls over on a quiet
Tuesday, so the shape below leads with the soak.

State the arrival model in the header, in plain words. A reader who cannot tell whether the
percentiles are subject to coordinated omission cannot use them, and every number in the file
depends on that one line.

Keep host names, credentials, and anything captured from real user data out of it. Where the
load model was a guess, the report says which figures were assumptions.

Use the shape below and put the data in tables. The prose left over is the bottleneck argument
and the paragraph on what the headroom means for this project.

Then tell the user the file path, the knee, the headroom, what gave first, and the soak verdict.

**Done when:** the report sits in the module's `.reports` folder, `.reports/` is git-ignored, no
older report was overwritten, the arrival model is stated in the header, and every shape from
step 5 appears with its result — including the ones skipped, with the reason.

## 9. Raise the knee — on a fix signal

Without the signal the work finished at step 8. **One change at a time**, and re-run the stress
shape after each. Two changes and one re-run cannot say which of them worked, or that one of
them made things worse.

Work the bottleneck step 6 named, not the list of everything that could be faster. Fixing what
was not the limit moves nothing and costs a day, and this is the commonest way performance work
produces no result.

| What gave | The usual first move |
| --- | --- |
| a pool or a queue | raise the size to what the downstream can actually serve — past that it queues in a different place |
| one pinned core | find the serialized section: a lock, a synchronous call on an async path, a blocking read |
| every core pinned | profile before changing anything. CPU-bound work needs the hot path, not a guess |
| garbage collection | allocation in the hot path first, generation sizing second |
| congestion collapse | a concurrency limit that sheds load, plus backoff on the retries feeding it |
| the database | the query plan and the index before the instance size |
| a leak | the thing that is not being released — the fix is a bug fix, not a tuning change |

Two ways to fake it. **Moving the expected peak** turns thin headroom into comfortable headroom
with no change to the system. **Softening the run** — a shorter hold at each step, a friendlier
data mix, the warm-up left in — does the same to the knee. The step 1 peak and the step 5 shapes
are fixed; a fix run that edits them has rewritten the exam.

Watch what each change costs elsewhere. A larger pool moves the load onto the database. A cache
raises the knee and adds a staleness question. A concurrency limit that sheds load raises the
error rate on purpose. Every one of those belongs in the report beside the improvement.

Where the fix needs a decision only the owner can make — more instances, a schema change, a
queue between two things that are currently synchronous — write it up as a decision waiting and
move on.

**Done when:** every change was made one at a time with its own stress re-run; the bottleneck
from step 6 is either relieved, left standing with a stated reason, raised as a decision waiting
on the owner, or deferred with its reason; the expected peak and the five shapes are unchanged
from the before run; and each change's cost elsewhere is recorded.

## 10. Write the after report — on a fix signal

Fresh timestamp, second file in the same `.reports` folder; the step 8 report stays untouched, so
anyone can read the before for themselves.

Lead the body with a "What moved" section naming the step 8 file, and give each of these its own
table:

- the knee, the headroom, and the soak verdict, before and after;
- each change made, the bottleneck it addressed, and the knee immediately after it — so a change
  that moved nothing is visible as one;
- latency at the expected peak, before and after, because a knee raised while normal traffic got
  slower is a trade rather than a win;
- what gave first now. There is always a new bottleneck, and naming it is where the next run
  starts.

Then tell the user both file paths, both knees, the headroom now, and what is still waiting on a
decision.

**Done when:** both reports sit side by side, the after report names the before file and states
both knees, every change from step 9 appears with the knee it produced, latency at the expected
peak is shown before and after, and the new bottleneck is named.

---

# Report shape

A Node service on four instances. The tables, shapes, and the two numbers are what transfers —
swap in your own journeys, tools, and paths. Every table is shown with one or two data rows; a
real report lists them all.

````markdown
# Stress Test Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Commit** | `<short sha>` (dirty working tree) |
| **Environment** | staging — 4 × 2 vCPU app instances, `db.r6g.large`, 1.2M orders in the database (production holds 4.1M) |
| **Generator** | `k6 0.52.0`, constant arrival rate, latency recorded against intended send time |
| **Arrival model** | **open** — not subject to coordinated omission |
| **Expected peak** | 180 req/s — busiest minute of Black Friday 2025, from the access logs |
| **Stubbed** | the payments provider, at a fixed 120ms. Its real latency is not in these numbers |
| **Warm-up** | 2 minutes, excluded from every figure |
| **Previous** | [`stress-report-2026-07-30-091412.md`](./stress-report-2026-07-30-091412.md) |

## The verdict

# Soak failed — connections leak, and the knee is 1.6× the peak

The knee is at **290 req/s** against an expected peak of 180, so there is 1.6× headroom: enough
for today, not enough for a marketing push. The connection pool is what gives.

The soak run is the more urgent finding. Over six hours at the expected peak, open database
connections climbed from 40 to 194 on a straight line and never fell. At that rate the pool
ceiling of 200 arrives about fifteen minutes after the run ended, and nothing in the run
suggests it stops there. This
is a leak, and it is unrelated to load.

| | Value | Previous | Change |
| --- | --- | --- | --- |
| **Knee** | **290 req/s** | 240 req/s | +50 |
| **Headroom** | **1.6×** — 290 ÷ 180 | 1.3× | +0.3 |
| **Soak** | 🔴 fail — connections leak | 🔴 fail — connections leak | — |
| **What gave first** | the database connection pool, saturated at 288 req/s | the same | — |

## The load model

| Journey | Share | At peak | Think time | Data |
| --- | --- | --- | --- | --- |
| Browse catalogue | 62% | 112 req/s | 3–8s | 400 search terms from the logs |
| Checkout | 14% | 25 req/s | 5–15s | 5,000 distinct users, one order each |

Assumption: the 3–8s think time on browse has no evidence behind it. Analytics does not record
it, so it was estimated from session length ÷ page views.

## The stress run

| Arrival rate | Throughput | p50 | p95 | p99 | Errors | Pool in use |
| --- | --- | --- | --- | --- | --- | --- |
| 180 req/s | 180 | 84ms | 210ms | 340ms | 0.00% | 71 of 200 |
| 280 req/s | 279 | 128ms | 402ms | 710ms | 0.01% | 178 of 200 |
| 300 req/s | **291** | 402ms | 2,940ms | 6,100ms | 0.4% | **200 of 200** |
| 340 req/s | **274** | 890ms | 7,200ms | 14,800ms | 4.1% | 200 of 200 |

**The knee is at 290 req/s** — between the 280 and 300 steps. Throughput stops rising there and
latency goes up sevenfold.

Past the knee throughput **falls**, from 291 to 274 — congestion collapse rather than a plateau.
The client retries on timeout with no backoff, so the system receives most traffic exactly when
it can serve least.

## The other shapes

| Shape | Result | Detail |
| --- | --- | --- |
| Smoke | 🟢 pass | script correct, all three journeys reach their assertions |
| Load | 🟢 pass | 30 min at 180 req/s, p95 210ms, no errors |
| Soak | 🔴 fail | 6 h at 180 req/s. Connections 40 → 194, never falling. Memory flat, disk flat, no lag |
| Spike | 🟠 survived, slow to recover | 180 → 720 req/s in 5s: 31% errors for 40s, then stable at a shed rate. Back to normal latency 4m 20s after the spike ended |

---

## 🔴 What gave first — the database connection pool

| | |
| --- | --- |
| **Evidence** | pool usage hits 200 of 200 at the same step throughput goes flat. App CPU is 46%, database CPU 38% — neither is the limit |
| **Why it is the pool** | requests are waiting for a connection, not for work. The pool flattens one step before throughput does |
| **Second in line** | at 340 req/s the database reaches 71% CPU, so relieving the pool alone moves the knee to roughly 380 req/s and no further |
| **What it would take** | raise the pool toward what the database can actually serve, and shorten the checkout transaction, which holds a connection for 340ms while it calls the payments stub |

## 🔴 The leak

| | |
| --- | --- |
| **What** | open database connections climb from 40 to 194 over 6 hours at a steady 180 req/s, on a straight line |
| **Why it matters** | this has nothing to do with load. At this rate the 200 ceiling arrives about 15 minutes after the run ended, and the process needs a restart to clear it |
| **Where to look** | the connection released on the happy path only — the error branch in `src/orders/repo.ts` returns without releasing |

## Decisions waiting on the owner

| Finding | The decision | Why it is not ours |
| --- | --- | --- |
| Headroom is 1.6× | whether 1.6× is enough, or the fleet grows | depends on the traffic the business expects, not on the code |

## The gates

| Gate | Judged on | Where | State |
| --- | --- | --- | --- |
| Smoke on pull requests | the script runs and asserts | `.github/workflows/ci.yml` | not applied |
| Load, nightly | p95 within budget at 180 req/s | `.github/workflows/load-nightly.yml` | not applied |
| Regression on pull requests | p95 at peak, against the last run on this environment | `.github/workflows/ci.yml` | not applied |

Stress, soak, and spike are deliberately not gated, for the reason in step 7.
````

Drop any empty section. Where no older report sits beside this one, drop the "Previous" row and
the "Previous" and "Change" columns.

The after report from step 10 is this shape with a "Before" row in the header, the four tables
that step names leading the body, and the new bottleneck named at the end. The before report is
never edited to match it.
