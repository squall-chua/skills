---
name: integration-test
description: >
  Write tests that run against the real database, broker, and other collaborators,
  prove each one red before green and the suite hermetic, and report which seams are
  covered and which are still unproven.
disable-model-invocation: true
---

A **seam** is where your code hands work to something it does not own — a database, a broker, a
cache, another team's API. Unit tests stop at the seam and mock what is on the far side, so
everything they prove is a statement about your own mock. This skill writes the tests that
cross it and run against the **real** thing.

Real infrastructure makes tests slow and flaky unless they are **hermetic**: each test brings
its own data, leaves nothing behind, and passes alone, shuffled, and twice in a row. A suite
without that property gets marked `skip` within a month. Both halves are the job — cross the
seam, and stay hermetic while doing it.

## What this skill writes

New test files, the harness that starts the real dependencies, and one report. The production
code stays as it is: a test that can only pass after the source changes has found a bug, and
that goes in the report as a finding for its owner.

## 1. Inventory the seams

Read the wiring, not the whole codebase: where clients are constructed, what the config and
environment variables name, what the container or compose files declare, what the manifest
lists as a driver or SDK.

| Seam | Looks like |
| --- | --- |
| Database | a connection string, an ORM, a migration folder, raw SQL |
| Cache | Redis, Memcached, a client with a TTL |
| Broker or stream | Kafka, RabbitMQ, SQS, NATS, an outbox table |
| Object store | S3, GCS, Azure Blob, a signed-URL helper |
| Third-party API | an SDK, a base URL in config, a webhook receiver |
| Another service you own | an internal base URL, a generated client |
| Filesystem | a path from config, a temp directory, an upload folder |

Rank them the same way risk is ranked anywhere: what the seam decides — money, permissions,
data writes — and how often the code around it changes:

```sh
git log --since='6 months ago' --name-only --format= -- <path> | grep . | sort | uniq -c | sort -rn
```

The `grep .` matters: `--name-only` prints a blank line between commits, and without it the
blank sorts to the top as your busiest file.

**Done when:** every seam is listed with its technology, the file that constructs it, the code
that uses it, and its rank; and the ranking rule is written down.

## 2. Decide real or faked, seam by seam

One rule decides it: **run the collaborators you own, fake the ones you do not.**

| Seam | Run it |
| --- | --- |
| Database, cache, broker, object store | **real**, in a container the suite starts |
| Another service in this repo | **real**, started alongside |
| Third-party API | a **fake** pinned to a recorded real response |
| Payments, email, SMS | the vendor's sandbox where one exists, the fake otherwise |
| A service another team owns and deploys | a fake, plus their published contract if they have one |

A test that calls a third party for real is a bill, a rate limit, and a build that fails for
somebody else's deploy. A fake is only as true as the recording behind it, so record it from a
real call, note the date in the file, and re-record when their API changes.

A seam mocked in-process stays a unit test and the seam stays **unproven**. A mock counted as
integration coverage is the one number in this report that can lie outright.

**Done when:** every seam from step 1 carries a decision, its reason, and — for a fake — the
date and source of the recording behind it.

## 3. Start the real thing from the suite itself

The bar: a clone of the repo on a machine with nothing installed but a container runtime runs
the suite and it passes. A dependency the developer has to install and seed by hand is a
dependency that will be missing in CI.

Prefer the harness the project already has. Otherwise:

| Language | Tool |
| --- | --- |
| JavaScript / TypeScript | Testcontainers for Node, `docker compose` through the runner's global setup |
| Python | `testcontainers-python`, `pytest-docker` |
| Go | `testcontainers-go`, `dockertest` |
| Java / Kotlin | Testcontainers, `@ServiceConnection` in Spring Boot |
| C# / .NET | `Testcontainers` |
| Rust | `testcontainers-rs` |
| PHP | Testcontainers for PHP, `docker compose` |
| Ruby | `testcontainers-ruby`, `docker compose` |

### Nothing installed?

Two prerequisites, and they fail differently.

**A container runtime** — check `docker info` or the Podman equivalent answers. Where it is
absent or not running, that is a machine prerequisite you cannot install on the user's behalf:
say which runtime the harness needs, point at its install page, and stop until they have it.

**The harness library** — check the manifest and lockfile first. Where none is there, put the
setup to the user in one message: the library, the exact install command, what it adds to the
manifest, and the first-run cost, which for containers is an image pull worth naming in
megabytes. Wait for the go-ahead, then install exactly that and commit nothing.

Two settings decide whether the run means anything:

- **Pin the image to the version production runs.** A suite green on Postgres 16 says little
  about a production on 13. Where they differ, put both in the report.
- **Build the schema with the project's own migrations.** A hand-written test schema drifts from
  the real one silently, and then the suite proves the code works against a database nobody runs.

Wait on readiness rather than a sleep — the tool's own wait strategy, a health check, or a poll
with a timeout. A sleep is the commonest source of a suite that passes on a laptop and fails in
CI.

**Done when:** the container runtime answers, the harness was already present or the user
approved its setup, one throwaway test connects to the real dependency started by the suite, the
image version and the production version are both written down, and the schema came from the
project's migrations.

## 4. Write the tests, one seam at a time

Work the step 1 ranking from the top. Each test gets written, then **proven red**: point it at
the wrong table, the wrong queue, or a closed port, and watch it fail. A test that stays green
with the seam broken is testing your assertion against itself.

Then cover what only a real collaborator can answer. Per seam, a round trip and at least one
failure:

| Kind | What it proves |
| --- | --- |
| **Round trip** | the write lands and reads back as what was written |
| **Real query** | the SQL, the mapping, the index, the JSON column, the decimal and the timezone survive the real engine |
| **Constraint** | the unique, foreign key, or not-null violation fires and the code handles it |
| **Transaction** | a failure mid-way rolls back, and no half-written row survives |
| **Migration** | the migration applies to a database already holding old rows, not only to an empty one |
| **Delivery** | the message is published, consumed, and handled once — including when it arrives twice |
| **Outage** | the collaborator down, slow past the timeout, or answering garbage, and the code's own behaviour under it |

Drive the system through its own doors — the repository, the client, the handler the application
itself calls. A test that issues its own SQL beside the code proves the database works, which
nobody doubted.

Keep production code untouched. Where a test can only pass after the source changes, it found a
bug: write it up as a finding and mark the test skipped, naming the finding in the skip reason.

**Done when:** every seam marked real in step 2 has a round trip and at least one failure case,
every new test was proven red before it went green, and every test that cannot pass names its
finding.

## 5. Prove the suite hermetic

Hermetic is a property you demonstrate, not one you intend. Run all four:

| Check | Run | Passes when |
| --- | --- | --- |
| **Alone** | each new test on its own | it passes without its neighbours |
| **Shuffled** | the suite in random order, the runner's own flag | order changes nothing |
| **Twice** | the suite twice against the same container, no wipe between | the second run is as green as the first |
| **Parallel** | the suite at the project's real worker count | no test fails on another's data |

Where one fails, the fix is in the test, and three cover nearly every case: give each test its
own data under a unique key rather than a shared fixture, clean up by rolling back the
transaction or truncating what the test made, and wait on a condition instead of sleeping.

The **twice** run is the one people skip and the one that catches most of it: a test that only
passes against a fresh database fails the moment the suite runs twice in a day.

**Done when:** all four checks have been run and pass, and each command and its result is
recorded for the report.

## 6. Keep it fast enough that people run it

An integration suite dies of its runtime. Record the total, then take whichever of these the
project needs:

- One container for the whole suite, not one per test. Reuse it between runs where the tool
  supports it.
- Parallel workers, which the step 5 data isolation has already made safe.
- A separate command from the unit suite, so the fast loop stays fast.

**Done when:** the suite runtime is recorded, and either it is one a person will wait for or the
report says plainly which of the above is left to do.

## 7. Work out the gate

Two recommendations, neither applied here:

**Run the integration suite in CI on pull requests**, where the runner can start containers. Too
slow for every push? Nightly and on merges to the default branch instead, and say which you chose.

**Judge new work on new seams.** A pull request that adds a seam with no integration test is the
gap this skill exists to close, and far cheaper to catch there than in the next audit.

**Done when:** both are written down with the workflow file each would live in, and no CI file
has been edited.

## 8. Write the report

Header: the timestamp from `date '+%Y-%m-%d-%H%M%S'`, the commit from `git rev-parse --short
HEAD`, and a note if the working tree is dirty.

Write to `<module>/.reports/integration-report-<timestamp>.md`. `<module>` is the nearest
directory at or above the scope holding the project's manifest (`package.json`, `go.mod`,
`pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`, `*.csproj`); a run
spanning several writes to the repository root. Create the folder if missing, add `.reports/` to
the root `.gitignore` if nothing there covers it, one file per run, never overwrite an older one.

Report one number and one verdict:

> **seam coverage = seams with a real integration test ÷ seams that apply**

and the hermetic verdict from step 5, a pass only when all four checks passed. High seam
coverage with a failed shuffle is a suite about to start lying.

Use the shape below and put the data in tables. The prose left over is the reason a seam is
unproven and the description of each finding.

Then tell the user the file path, the seam coverage, the hermetic verdict, the suite runtime, and
any finding the tests turned up in the production code.

**Done when:** the report sits in the module's `.reports` folder, `.reports/` is git-ignored, no
older report was overwritten, and every seam from step 1 appears with its decision, its tests,
and its state.

---

# Report shape

A TypeScript report. The tables, kinds, and checks are what transfers — swap in your own tools
and paths. Every table here is shown with one or two data rows; a real report lists them all.

````markdown
# Integration Test Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Commit** | `<short sha>` (dirty working tree) |
| **Scope** | `src/**` — 6 seams |
| **Harness** | Testcontainers for Node 10.13.2, started by `vitest` global setup |
| **Command** | `<the command you ran>` |
| **Suite** | 34 integration tests, 33 passed, 1 skipped · 1m 48s |
| **Previous** | [`integration-report-2026-07-30-091412.md`](./integration-report-2026-07-30-091412.md) |

## Seam coverage

| | Value | Previous | Change |
| --- | --- | --- | --- |
| **Seam coverage** | **66.7%** — 4 of 6 seams | 33.3% | +33.4 |
| **Hermetic** | 🟢 pass — all four checks | 🔴 shuffle failed | — |

Two seams are unproven, and neither is mocked into a false green.

## The seams

| Seam | Technology | Test version | Production version | Decision | Tests | State |
| --- | --- | --- | --- | --- | --- | --- |
| Orders database | PostgreSQL | `postgres:16.2` | **13.14** | real, container | 18 | 🟠 covered, version drift |
| Document store | S3 | — | — | mocked in-process | 0 | 🔴 unproven |

The orders database runs 16 in tests and 13 in production: every query here is proved against an
engine three majors ahead of the one serving customers.

## Tests written

| File | Seam | Kind | What it proves | Proven red against |
| --- | --- | --- | --- | --- |
| `src/orders/orderRepo.integration.test.ts` | database | round trip | an order written through the repository reads back with its line items and totals intact | the table renamed to `orders_x` |
| `src/payments/stripeClient.integration.test.ts` | payments | outage | a gateway timeout leaves the order unpaid rather than half-paid | the timeout raised past the test's wait |

## Hermetic proof

| Check | Command | Result |
| --- | --- | --- |
| Alone | `vitest run <each new file>` | 🟢 all pass |
| Shuffled | `vitest run --sequence.shuffle` — 3 runs | 🟢 pass |
| Twice | the suite twice against one container, no wipe | 🟢 pass |
| Parallel | `vitest run --pool=threads` at 4 workers | 🟢 pass |

The shuffle failed first time: two tests shared a fixed customer id. Each now generates its own.

---

## 🔴 Unproven seams

### 1. Document store — S3

| | |
| --- | --- |
| **Today** | the S3 client is mocked in-process in every test that touches it |
| **What that proves** | that the mock returns what the mock was told to return |
| **What it would take** | LocalStack or MinIO in a container, then a round trip and a failure case on the upload path |
| **Rank** | 2 of 6 — it stores customer invoices, and `documents/` changed 8 times in 6 months |

---

## Findings for the code

Turned up while writing the tests. The production code was left as it is.

| File · line | Finding | Evidence | Suggested action |
| --- | --- | --- | --- |
| `src/orders/orderRepo.ts:112` | the retry runs outside the transaction, so a retried insert writes the order twice against a real database — the in-memory fake used until now allowed it | `orderRepo.integration.test.ts › retries an insert once` — skipped, names this finding | move the retry inside the transaction, or make the insert idempotent on the key |

---

## The gates

| Gate | Judged on | Where | State |
| --- | --- | --- | --- |
| Integration suite on pull requests | green, and no new seam without a test | `.github/workflows/ci.yml` | not applied |
| Nightly full run | green | `.github/workflows/nightly.yml` | not applied |

The suite runs in 1m 48s, so pull requests can carry it.
````

Drop any empty section, and lead the body with the seams. Where no older report sits beside this
one, drop the "Previous" row and the "Previous" and "Change" columns.
