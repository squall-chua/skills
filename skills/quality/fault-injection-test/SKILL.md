---
name: fault-injection-test
description: >
  Break the environment under a running system on purpose, measure how far the steady
  state moved and whether it came back, and report every weakness with the resilience
  mechanism that was missing.
disable-model-invocation: true
---

A **steady state** is the handful of numbers that say the system is serving people: the success
rate, the latency at the tail, the orders going through per minute. Write them down and measure
them *before* anything breaks. Without that baseline there is nothing to compare a broken run
against, and "it seemed fine" is the whole finding.

Then break the environment underneath it — the database refusing connections, a third party
answering 429, a pod killed mid-request, the disk full — and watch what the steady state does.
The measurement is a comparison, not a score: how far it moved while the fault was live, how far
the damage spread, and whether it came back once the fault was gone.

That last half is the one people forget. A system that survives every fault and then never
recovers is worse than one that dips and returns, because a fault ends and this does not.

## This skill reports

Steps 1 to 8 run the experiments and write up what happened. The production code stays exactly
as it is. That report is the whole deliverable.

Steps 9 and 10 run only on a **fix signal**: "fix it", "close the gaps", "make it survive", "go
ahead". The step 8 report is the *before*, so it is written on a fix run too, and written before
anything is changed.

## 1. Define the steady state

Before naming a single fault. Pick the few signals that say the system is doing its job, and
prefer the ones a customer would feel over the ones a dashboard happens to have.

| Signal | Reads like |
| --- | --- |
| **Success rate** | non-error responses ÷ requests, on the paths that matter |
| **Latency at the tail** | p95 and p99, not the mean — the mean hides the fault you are looking for |
| **Throughput** | requests, jobs, or messages per second |
| **A business number** | orders placed, payments captured, messages delivered per minute |
| **Backlog** | queue depth, consumer lag, connection pool waiters |
| **Recovery** | how long after a fault stops before the above are back in band |

Each needs three things: the command or query that reads it, a value measured now, and a
**tolerance band** — the range that still counts as serving people. A band decided after seeing
the broken run is a band fitted to the result.

Then hold the system under a realistic load and watch the signals for a window long enough to
see them settle. A steady state measured on an idle system is a measurement of an idle system,
and every fault below will look survivable.

Where a signal has no way to be read, that is the first finding: a system nobody can measure
cannot be shown to have survived anything.

**Done when:** every signal carries its read command, its measured value, and its tolerance band;
the load applied is written down; and the system sat inside every band for the whole baseline
window.

## 2. Choose the faults, and state a hypothesis for each

List what the system talks to — the same wiring read as in any dependency audit: where clients
are constructed, what the config and environment name, what the compose file or manifest
declares. Then cross each against the faults that can actually happen to it.

| Fault | What it looks like |
| --- | --- |
| **Down** | connection refused, the process stopped, the container gone |
| **Slow** | latency added past the client's own timeout |
| **Flapping** | up and down on a cycle, so each retry lands on a moving target |
| **Rejecting** | 429s and 500s from a third party, or a connection pool with nothing free |
| **Partitioned** | packets dropped in one direction, so one side still believes it is fine |
| **Killed mid-request** | the pod or container removed with work in flight |
| **Duplicated or reordered** | a message delivered twice, or out of the order it was sent |
| **Starved** | the disk full, memory pressure, the CPU pinned |
| **Skewed** | the clock moved, a token expired, a certificate past its date |

Rank the pairs the way risk is ranked anywhere: what the dependency decides — money,
permissions, data writes — and how much of the system stops when it goes.

Then each experiment gets a **hypothesis**, written before it runs and specific enough to be
wrong:

> With the session cache refusing connections, checkout success stays above 99% and p99 stays
> under 800ms, because the code falls back to the database. It returns to band within 30
> seconds of the cache coming back.

"The system handles it" is not a hypothesis. Name the signal, the direction, the threshold, and
the recovery. A prediction that cannot fail teaches nothing when it passes.

Where the honest prediction is that the system falls over, keep the experiment and say so. A
confirmed weakness is a finding; an untested guess is not.

**Done when:** every dependency is listed with the faults that apply to it and its rank, and
every experiment carries a written hypothesis naming its signal, its threshold, and the recovery
expected.

## 3. Set the blast radius, and the abort condition

The **blast radius** is how far the damage is allowed to spread. Decide it before the first
fault, because the point at which you decide you have seen enough is a decision you cannot make
honestly while a queue is filling.

Four things, all written down:

- **The environment.** A local compose stack or a dedicated test environment needs nothing but
  your own decision. **Shared staging or production needs recorded authorization** — who
  approved it, when, the exact hosts and services in scope, and the window. No authorization, no
  run; say that plainly rather than narrowing the scope until it feels acceptable.
- **The targets.** The specific containers, pods, hosts, or routes the fault may touch, and what
  is explicitly out of scope. One instance, not the replica set; one route, not the gateway.
- **The abort condition.** The signal and the value at which the run stops — a success rate under
  a floor, a queue past a depth, any error a real customer could see. State it as a number.
- **The kill switch, tested.** The command that removes the fault, run once *before* the
  experiment, so you know it works while nothing is wrong. A kill switch first used during an
  incident is not a kill switch.

Every experiment also gets a **hold time** and a hard stop. An experiment left running because
it looked interesting is an outage you caused.

**Done when:** the environment, the target list, the out-of-scope list, the abort condition as a
number, the hold time, and the hard stop are all written down; the kill switch has been run
successfully against an unbroken system; and for any shared or production environment the
approver and the date are recorded.

## 4. Pick the injector

Prefer the tool the project already has. Otherwise:

| Where the system runs | Tool |
| --- | --- |
| Docker Compose, locally or in CI | Toxiproxy for network faults, Pumba for kill and pause, `docker compose stop` for down |
| Kubernetes | Chaos Mesh, LitmusChaos, or `kubectl delete pod` for the simplest case |
| AWS | AWS Fault Injection Service |
| Any of the above, driver-based | Chaos Toolkit, with the driver for your platform |
| In-process, Go | `failpoint`, `gofail` |
| In-process, Java / Spring Boot | Chaos Monkey for Spring Boot |
| Host resources | `stress-ng` for CPU, memory, and disk; `tc netem` for latency, loss, and reordering |
| Message duplication and ordering | the broker's own controls — redelivery, a paused consumer, a replayed offset |

Network faults are the ones worth reaching for first, because most dependency failures are
network failures wearing a different name, and a proxy in front of the dependency reproduces
down, slow, flapping, and partitioned without touching either side.

### Nothing installed?

Two prerequisites, and they fail differently.

**A container runtime** — check `docker info` or the Podman equivalent answers. Where it is
absent or not running, that is a machine prerequisite you cannot install on the user's behalf:
name the runtime the injector needs, point at its install page, and stop until they have it.
`tc netem` has its own version of this — it needs root on the host and it changes the host's
networking, so it is the last resort rather than the first reach.

**The injector itself** — check the manifest, the compose file, the CI workflows, and the binary
on `PATH` first. Where none is there, put the setup to the user in one message: the tool, the
exact install command, whether it lands in the manifest or only in the environment, and the
first-run cost, which for a container image is worth naming in megabytes. Wait for the
go-ahead, then install exactly that and commit nothing.

Read the tool's own docs for its current commands. Flag names drift between versions, and an
injector invoked from memory fails in a way that looks like a system surviving the fault.

**Done when:** the container runtime answers or the injector needs none, the tool was already
present or the user approved its setup, and one throwaway run has proved the injector both
applies a fault and removes it again.

## 5. Run the experiments, one fault at a time

One fault per run. Two at once and the result names neither of them, and this skill's whole
output is a statement about cause.

Each experiment goes the same way:

1. **Confirm the steady state.** Read every step 1 signal and check it is in band. Where it is
   not, stop — the system is already unwell and nothing you break next means anything.
2. **Apply the fault**, and record the exact command.
3. **Hold**, for the step 3 hold time, reading the signals throughout rather than only at the
   end. The shape matters: a success rate that sags and recovers on its own is a different
   system from one that sags and stays down.
4. **Remove the fault**, with the step 3 kill switch.
5. **Watch it come back.** Keep reading until every signal is in band again, or until the hard
   stop. **Record the time it took**, and where it never came back, record that instead.

Abort the moment the step 3 condition trips, and write down that it tripped. An aborted
experiment is a result — usually the most important one on the report.

Look past the signals too, at what only shows up during a fault: what the logs said, what the
user actually saw, whether an alert fired, whether the retries piled up. A system that survives
a fault silently and one that survives it while paging four people at 3am are not the same
system.

**Done when:** every experiment has its command, its readings from before, during, and after,
its hold time, its recovery time or a note that it never recovered, and either a completion or a
recorded abort with the value that tripped it.

## 6. Triage against the hypothesis

Every experiment gets one verdict, against the prediction written in step 2 — not against how it
felt to watch:

- 🟢 **Survived** — every signal stayed in band. The hypothesis held.
- 🟡 **Degraded as designed** — a signal left its band in a way somebody chose and step 2
  predicted: a fallback served stale data, a queue absorbed the writes, a feature turned itself
  off. A pass, and worth naming as one.
- 🟠 **Degraded unplanned** — it stayed up, but in a way nobody chose and nobody predicted.
- 🔴 **Broke** — the steady state is gone.
- ⚫ **Did not recover** — the fault was removed and the system stayed down. This outranks
  everything above it, whatever the numbers during the fault looked like.
- 🟣 **Collateral** — something outside the blast radius moved. The finding is the coupling
  nobody knew about, not the fault that revealed it.

Then give each non-green result its **blast radius** — one request, one user, one tenant, one
feature, or everybody — and name the mechanism that was missing. The symptom usually says which:

| What happened | Usually missing |
| --- | --- |
| the call hung until the whole connection pool was gone | a timeout on the client |
| every caller retried at the same instant and finished it off | backoff with jitter |
| the failing dependency took its callers down with it | a circuit breaker |
| one slow dependency starved every other request | a bulkhead, or a pool per dependency |
| the retry charged the card twice | an idempotency key |
| nothing served at all when the cache went | a fallback, or a stale read |
| the queue never drained after the fault stopped | a dead-letter path, or a drain that outpaces arrivals |
| it never came back on its own | a health check that actually recovers, or a reset |

Where the missing mechanism is a design decision rather than a setting — a fallback that needs
a product answer about what to show, a bulkhead that changes the deployment — say so and leave
it as a decision for the owner.

**Done when:** every experiment from step 5 carries one of the six verdicts, every non-green
result carries its blast radius and the mechanism that was missing, and every mechanism needing
a design decision is marked as one.

## 7. Work out the gates

Three recommendations, none applied here:

**Run the cheap experiments in CI**, against the compose stack the tests already start. Down and
slow on the collaborators the suite owns cost seconds and catch a removed timeout the day it
lands.

**Run the full set on a schedule** against a dedicated environment, not on pull requests — the
long ones need a realistic load and a real recovery window, and neither fits a pull request.

**Judge new work on new dependencies.** A change that adds a call to something outside the
process, with no timeout and no fallback, is the gap this skill exists to close, and it is far
cheaper to catch there than in the next run.

**Done when:** all three are written down with the workflow file each would live in, and no CI
file has been edited.

## 8. Write the report

Header: the timestamp from `date '+%Y-%m-%d-%H%M%S'`, the commit from `git rev-parse --short
HEAD`, and a note if the working tree is dirty. Record the environment and the load beside them,
because a verdict only holds for the environment it was measured in.

Write to `<module>/.reports/fault-report-<timestamp>.md`. `<module>` is the nearest directory at
or above the scope holding the project's manifest (`package.json`, `go.mod`, `pyproject.toml`,
`pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`, `*.csproj`); a run spanning several writes
to the repository root. Create the folder if missing, add `.reports/` to the root `.gitignore` if
nothing there covers it, one file per run, never overwrite an older one.

Report one number and one verdict:

> **hypothesis pass rate = experiments whose steady state held ÷ experiments run**

and the **recovery verdict**, a pass only when every experiment returned to band inside its hard
stop. The shape below leads with the recovery, not the pass rate.

Write it on a fix run too, before anything is changed. Keep host names, tokens, customer records,
and anything else captured from a real environment out of it; a report is read by more people
than the run was.

Use the shape below and put the data in tables. The prose left over is the hypothesis on each
experiment and the paragraph explaining a weakness.

Then tell the user the file path, the pass rate, the recovery verdict, and the worst thing that
happened.

**Done when:** the report sits in the module's `.reports` folder, `.reports/` is git-ignored, no
older report was overwritten, and every experiment from step 2 appears with its hypothesis, its
verdict, its blast radius, and its recovery time — including the ones aborted and the ones never
run, with the reason.

## 9. Close the gaps — on a fix signal

Without the signal the work finished at step 8. Work one weakness at a time, worst verdict first
— ⚫ did not recover, then 🔴 broke, then 🟣 collateral, then 🟠 degraded unplanned.

For each:

1. **Add the one mechanism step 6 named.** One at a time. A timeout, a retry with backoff and
   jitter, a circuit breaker, a bulkhead, an idempotency key, a fallback — not all six at once,
   or the re-run cannot say which of them worked.
2. **Re-run the exact same experiment** — same fault, same command, same hold time, same load.
   Anything else and the comparison is between two different questions.
3. **Check the steady state with the fault gone.** A retry that fixes the broken run and adds
   200ms to every normal request has moved the cost rather than removed it.

Step 2 is the proof this skill can give that no sibling can: the same fault, before and after.

Two ways to fake it, both worth naming. **Widening the tolerance band** turns a red into a green
without changing the system. **Softening the fault** — a shorter hold, a smaller latency, one
instance instead of two — does the same. The bands and the faults are what step 1 and step 2
fixed; a fix run that edits them has rewritten the exam.

Mind what a retry does to a system already under load. Retries added without a budget and a
circuit breaker are the standard way a small dependency failure becomes a full outage, so
whatever you add, re-run the experiment that first showed the callers piling on.

Where the fix needs a decision only the owner can make — what to show when the recommendation
service is down, whether a payment may be held rather than declined — write it up as a decision
waiting and move on.

**Done when:** every ⚫, 🔴, 🟣, or 🟠 experiment from step 6 is one of four things — fixed and proved
by a re-run of the identical experiment, left standing with a stated reason, raised as a
decision waiting on the owner, or deferred with its reason; no tolerance band and no fault
definition was changed; and the steady state with no fault applied is still in its original
band. None are simply unmentioned.

## 10. Write the after report — on a fix signal

Fresh timestamp, second file in the same `.reports` folder; the step 8 report stays untouched, so
anyone can read the before for themselves.

Lead the body with a "What moved" section naming the step 8 file, and give each of these its own
table:

- the pass rate and the recovery verdict, before and after;
- what happened to each non-green experiment — fixed, left standing, waiting on a decision,
  deferred — and the mechanism added;
- the steady state with no fault applied, before and after, so the cost of the fixes is visible;
- any experiment green before and not green now. That is a regression, and the first thing the
  reader needs.

Then tell the user both file paths, both pass rates, the recovery verdict now, and what is still
waiting on a decision.

**Done when:** both reports sit side by side, the after report names the before file and states
both pass rates, every ⚫, 🔴, 🟣, or 🟠 experiment from step 6 appears with its outcome and the
mechanism added, and each fixed one shows the re-run that proved it.

---

# Report shape

A Node service on a compose stack. The tables, verdicts, and the two numbers are what transfers —
swap in your own dependencies, faults, and paths. Every table is shown with one or two data rows;
a real report lists them all.

````markdown
# Fault Injection Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Commit** | `<short sha>` (dirty working tree) |
| **Environment** | `docker compose` stack on the build host — not production |
| **Load** | 40 req/s against `/checkout` and `/catalog` for the whole run, `k6` |
| **Injector** | Toxiproxy 2.9.0 in front of Postgres, Redis, Kafka, and the payments API; Pumba 0.10.1 for container kill |
| **Blast radius** | the four app containers and their four proxies. Out of scope: the host, the CI runner, anything outside the compose network |
| **Abort at** | checkout success below 90%, or queue depth above 5,000 |
| **Experiments** | 11 run, 1 aborted, 1 not run |
| **Previous** | [`fault-report-2026-07-30-091412.md`](./fault-report-2026-07-30-091412.md) |

## The verdict

# Recovery failed — the order consumer does not come back on its own

Nine of eleven experiments held their steady state, which reads well until the tenth: with Kafka
partitioned for 60 seconds, the consumer stopped and stayed stopped after the partition was
removed. Nothing recovers it but a restart, and nothing alerts on it. Orders queued silently for
the remaining 9 minutes of the run.

| | Value | Previous | Change |
| --- | --- | --- | --- |
| **Hypothesis pass rate** | **81.8%** — 9 of 11 | 72.7% | +9.1 |
| **Recovery** | 🔴 fail — 1 of 11 never returned to band | 🔴 fail — 2 | — |

## The steady state

Measured under load before the first fault, and again after the last one.

| Signal | Read with | Band | Baseline | After the run |
| --- | --- | --- | --- | --- |
| Checkout success rate | `sum(rate(http_requests_total{route="/checkout",code!~"5.."}[1m]))` | ≥ 99.0% | 99.8% | 99.7% |
| Consumer lag | `kafka-consumer-groups --describe --group orders` | ≤ 100 | 4 | **11,840** |

The last row is the finding above, seen from the baseline side.

## The experiments

| # | Dependency | Fault | Hold | Verdict | Blast radius | Recovered in |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Postgres | slow — 500ms added | 60s | 🟢 survived | — | n/a |
| 5 | Kafka | partitioned one way | 60s | ⚫ did not recover | every order placed after the fault | **never** |

Experiment 8, the clock skew on the token issuer, was **not run**: the compose stack shares the
host clock, so the fault could not be limited to the blast radius in step 3. It needs a dedicated
environment.

---

## ⚫ Did not recover

### 1. Kafka partitioned — the order consumer stops and stays stopped

| | |
| --- | --- |
| **Hypothesis** | with the broker unreachable for 60s, orders queue and the consumer resumes within 30s of the partition being removed, so no order is lost |
| **Fault** | `toxiproxy-cli toxic add kafka -t timeout -a timeout=0 --upstream` |
| **What happened** | the consumer logged `Disconnected` once, then nothing. The partition was removed at 60s; the consumer never reconnected. Lag climbed from 4 to 11,840 over the following 9 minutes and no order was confirmed |
| **What the user saw** | checkout kept returning 200. The order was accepted and never processed — the worst shape of this failure, because nothing upstream reported a problem |
| **Blast radius** | every order placed after the fault, indefinitely |
| **Alerting** | none fired. There is no alert on consumer lag |
| **Missing** | a health check that fails on a stalled consumer so the orchestrator restarts it, plus a reconnect loop in the client. The lag alert is a separate finding |

---

## 🟡 Degraded as designed

| # | Dependency | What it did instead | Cost | Predicted |
| --- | --- | --- | --- | --- |
| 3 | Redis down | read straight through to Postgres | p99 410ms → 690ms, inside the band | yes, in the step 2 hypothesis |

---

## Decisions waiting on the owner

| Finding | The decision | Why it is not ours |
| --- | --- | --- |
| Catalog service killed — the search page 500s with it | what search should show when the catalog is gone: stale results, an empty state, or an error | a product answer about what a customer sees |

---

## The gates

| Gate | Judged on | Where | State |
| --- | --- | --- | --- |
| Cheap experiments on pull requests | down and slow on Postgres and Redis, against the compose stack | `.github/workflows/ci.yml` | not applied |
| Full set, scheduled | pass rate and recovery, against a dedicated environment | `.github/workflows/fault-nightly.yml` | not applied |
| New dependency without a timeout or fallback | review | `.github/workflows/ci.yml` | not applied |

The first takes about 90 seconds, so pull requests can carry it.
````

Drop any empty section. Where no older report sits beside this one, drop the "Previous" row and
the "Previous" and "Change" columns.

The after report from step 10 is this shape plus a "Before" row in the header, the four tables
that step names, and an **Outcome** row on every experiment. The before report is never edited to
match it.
