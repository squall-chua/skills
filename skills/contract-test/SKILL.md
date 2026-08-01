---
name: contract-test
description: >
  Test a running API against its own contract — OpenAPI, GraphQL, protobuf, or
  AsyncAPI — from the outside, and report every drift between what the contract
  promises and what the API does.
disable-model-invocation: true
---

A contract is the promise an API makes to callers who cannot see inside it. This skill checks
that promise the only way a caller can: send a request, read the response. The API stays a
**black box** — every finding comes from a request and the reply it got back, so the report says
what a real consumer hits. A gap between the promise and the behaviour is a **drift**, and this
skill ends with every drift written down.

## What this skill writes

The report, the probe suite from step 7, and — on the derived rung — the contract itself. The
source stays closed once the operations are known: an explanation drawn from the code describes
the implementation, where the value here is a verdict a consumer could have reached alone.

Each drift has two possible fixes, the API or the contract. The report names both, says which
the evidence favours, and leaves the edit to whoever owns that side.

## 1. Find the contract

Work down this ladder and stop at the first rung that yields one.

**1. Published** — the contract file the team keeps in the repo:

| Surface | Contract |
| --- | --- |
| HTTP / REST | OpenAPI or Swagger, `openapi.yaml`, `swagger.json` |
| GraphQL | an SDL file checked into the repo |
| gRPC | the `.proto` files |
| Events / messaging | AsyncAPI, or the JSON Schema each message is published against |
| Consumer-driven | Pact files already published to a broker by consumer teams |

**2. Served** — what the running service hands out: a `/openapi.json`, `/swagger.json`, or
`/v3/api-docs` route, a GraphQL introspection query, gRPC server reflection. The box stays
closed, because a caller could have fetched the same thing. Ask for the base URL here; step 2
settles the credentials.

**3. Derived** — read the code for its route table alone, and write the contract out as a file.
Ask the framework first: FastAPI, NestJS, springdoc, gin-swagger and most others generate a spec
from the routes already declared, and that beats reading handlers by hand. Where nothing
generates, walk the route registrations, the path decorators or annotations, the method, the
request and response types, and the status codes the handlers return.

This is the one time the source is opened, and it is opened for the **inventory** — which
operations exist — never for an explanation of behaviour.

A derived contract is a weaker instrument, and the report says so on every run that uses one:

- It **cannot** prove shape conformance: written from the implementation, the two agree by
  construction.
- It **can** prove the promises kept somewhere other than where they are declared — a guard the
  route declares and the runtime skips, a required field the types declare and the handler
  ignores, a documented status that never arrives, an error body no handler produces, an
  operation that answers `500`.
- Save it beside the code as a first draft the team can review and publish, marked unreviewed.

**4. Ask** — only when all three fail. Tell the user which rungs you tried.

Record the rung, path, format, version, and operation count. Where a published contract is
itself generated at build time, say so — it drifts only where generation is stale or the file
was hand-edited since.

**Done when:** the contract is a file you can point the runner at, its rung is recorded, and a
derived one is saved and marked unreviewed — or the user has been asked, with the rungs named.

## 2. Pin the target and agree what may be sent

Get the base URL, the environment name, and working credentials, and prove them with one
known-good request first. A run against a wrong URL or a dead service returns total drift, and
reads as a catastrophe rather than a typo.

Conformance runs send generated data through `POST`, `PUT`, `PATCH`, and `DELETE`. Agree the
method set with the user. Against production, or any environment holding real user data, run the
read-only methods and get an explicit go-ahead before adding the rest. Record which methods ran,
so a clean report on `GET` alone is never read as a clean report on everything.

Keep credentials out of the report: name the auth scheme and the variable the token came from.

**Done when:** the base URL, environment, auth scheme, and agreed method set are recorded, and
one trial request has returned the status the contract promises for it.

## 3. Pick and configure the runner

Prefer the tool the project already has. Otherwise:

| Contract | Tool |
| --- | --- |
| OpenAPI / Swagger | Schemathesis, Dredd, Prism in proxy-validation mode, Portman with Newman |
| GraphQL | `graphql-inspector diff` between the SDL and a live introspection, Schemathesis for GraphQL |
| gRPC | `grpcurl` against server reflection, compared with the `.proto`; `buf` for the schema diff |
| AsyncAPI / events | Microcks, or an AsyncAPI validator over captured messages |
| Pact | the Pact provider verifier, run against the pacts in the broker |

### Nothing installed?

Look before you install: the manifest and its lockfile, the CI workflows, the project's own
config files, and the binary on `PATH`. A tool declared in the manifest but missing from the
environment needs the project's own install command, not a new dependency.

Where the project genuinely has none, put the setup to the user in one message — the tool and
why it fits this project, the exact install command, the config file with its contents, the
command this skill will then run, and what it costs in download size and first-run time — and
wait for the go-ahead. A new dependency changes the manifest and the lockfile, which is the
user's call. Then install exactly that, leave the config in the repo, and commit nothing.

A conformance run is one-shot, so a runner that works through `npx`, `uvx`, `pipx run`, or a
container image needs no dependency at all. Prefer that where it exists and say so, since it
leaves the manifest untouched.

Read the tool's own docs for its current flags — names drift between versions, and a config
written from memory fails in ways that look like a broken API.

Set five things: the contract file, the base URL, the auth header or hook, the agreed method set
from step 2, and a machine-readable report file — JUnit XML or JSON — beside whatever the tool
prints. You read the machine-readable one.

Turn on every check the tool offers: status code, content type, response body against the
schema, response headers, and the negative cases — a malformed body, a missing required field, a
call with no credentials. A run that only replays the happy path proves the least interesting
half of the contract.

Leave the config file in the repo, so the next run and CI use the same settings.

**Done when:** the runner was already present or the user approved its setup, the config is in
the repo, a single-operation trial run completes against the live API, and it writes the
machine-readable report you asked for.

## 4. Run and capture

Run the full command and capture stdout, stderr, the exit code, and the report file. Long runs
belong in the background so you can keep working.

Then list the operations the run touched and the ones it never called. Tools skip operations
quietly — a missing path parameter, a required setup call, an endpoint behind a feature flag —
and a skipped operation is unproven, not passing.

**Done when:** every operation is marked exercised or not, and every exercised one carries its
request, response status, and result.

## 5. Take the two numbers

> **contract coverage = operations exercised ÷ operations in the contract**
>
> **conformance = operations with no drift ÷ operations exercised**

Report both side by side. An API at 100% conformance over 3 of 40 operations has proved almost
nothing, and a single blended percentage is how that gets hidden.

Under a derived contract, conformance covers only the drift such a contract can find — the step
6 probes. Say that beneath the number, so a high score reads as the narrow result it is.

**Done when:** both numbers are computed, every unexercised operation carries its reason, and a
derived run states what its conformance number leaves out.

## 6. Probe what the runner cannot see

A conformance tool checks the shapes it was given. These are promises it will not test on its
own, so send them by hand:

| Probe | Send | The contract promises |
| --- | --- | --- |
| Guard enforced | a protected operation with no credentials | 401, and no data in the body |
| Scope enforced | the same call with a token lacking the scope | 403 |
| Error shape | any failing call | a body matching the documented error schema |
| Required fields | a body with a required field removed | 400, documented shape |
| Unknown fields | a body with a field the schema never declares | whatever the contract states — accepted or rejected |
| Wrong media type | a valid body sent as `text/plain` | 415 |
| Unknown identifier | a `GET` on an id that does not exist | 404, not 200 with an empty body, not 500 |
| Pagination | a page size and cursor from the contract | the documented page size, and a usable next cursor |
| Documented headers | any successful call | every header the contract declares, rate-limit headers included |

**Done when:** every probe has been sent and carries its request, response, and verdict, or is
marked not applicable with a reason.

## 7. Keep the probes

The runner regenerates its own cases from the contract every time. The probes are different: you
sent them by hand, and unless they are kept they evaporate with this run and CI never sends them
at all.

Use the project's own test runner and HTTP client. Take the base URL and token from the
environment, so no credential lands in the file. Keep it out of the unit suite — it needs a live
target, so it belongs behind its own command, beside the runner config.

Each probe becomes one case asserting what the **contract** promises rather than what the API
did. A probe that passed is checked in green. A probe that found drift is written the same way
and marked skipped, its skip reason naming the drift and the report, so it goes green the day
the owner fixes it.

Then prove each green case red: invert the expectation once — the status the API does not
return, the route you know is open — and watch it fail. A guard test that passes against an
unguarded route reports safety that was never checked.

**Done when:** the file sits beside the runner config, every step 6 probe is a case in it, every
green case was proven red by an inverted expectation, every skipped case names its drift, and no
credential is written into the file.

## 8. Triage every drift

Label each one:

- **Missing** — the contract promises it, the API does not deliver it. A 404 on a declared path,
  an absent field, a header that never arrives.
- **Undocumented** — the API delivers it, the contract never mentions it. An extra endpoint, an
  extra field, a status code nobody declared.
- **Shape** — present on both sides, but a different type, format, enum, or nullability.
- **Status** — the same condition answered with a different status code.
- **Guard** — the authentication or authorization the contract describes is not enforced, or is
  enforced where the contract says the operation is open.

Then bucket it:

- **P1 breaking** — a consumer that follows the contract gets a wrong answer or an error. Missing
  fields, changed types, changed statuses, a vanished operation, a guard that lets an
  unauthenticated call through, data in a body that promised none.
- **P2 divergent** — the API behaves and the contract misdescribes it, so consumers written from
  the contract break later. Undocumented fields and statuses, a wrong required list.
- **P3 cosmetic** — descriptions, examples, ordering. No behaviour rides on it. A stale example
  belongs here even where it misstates a default, because nothing reads it at runtime.

For every P1 and P2 write one sentence about the **consumer**, not the diff. "A client that reads
`order.total` as a number receives a string and fails on the first calculation" is useful; "type
mismatch at `#/properties/total`" restates the tool output.

Then name the side to fix, with the evidence for it. A field the API has returned since its first
release, absent from a contract updated last week, points at the contract. Where the evidence
does not settle it, say so and leave the choice to the owner.

Keep the request and the response beside every drift; that pair is what lets the owner reproduce
the finding without this skill.

**Done when:** every drift carries one label, one bucket, its request and response, and — for P1
and P2 — a consumer sentence and a named side to fix.

## 9. Work out the gate

Recommend three, apply none.

**A conformance run in CI** against a deployed environment, judged on **new drift** rather than
the total. The population changes whenever the contract changes, so a total-count gate fails one
pull request for drift it never caused and passes the next for deleting an operation.

**A contract diff on pull requests that change the contract**, flagging removed operations and
fields, a widened required list, a narrowed enum. Each breaks a consumer that was correct
yesterday, and the diff catches it while it is still cheap.

**The step 7 probe suite on every pull request**, judged on its green cases staying green. It is
the cheap half of the other two — seconds rather than minutes — so it can sit on every pull
request even where the full sweep cannot.

**Done when:** all three are written down with the file each would live in, and no workflow file
has been edited.

## 10. Write the report

Header: the timestamp from `date '+%Y-%m-%d-%H%M%S'`, the commit from `git rev-parse --short
HEAD`, and a note if the working tree is dirty. Record the contract's version and its rung beside
them — which rung it came from decides how much the numbers are worth.

Write to `<module>/.reports/contract-report-<timestamp>.md`. `<module>` is the nearest directory
at or above the contract holding the project's manifest (`package.json`, `go.mod`,
`pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`, `*.csproj`); a run
spanning several writes to the repository root. Create the folder if missing, add `.reports/` to
the root `.gitignore` if nothing there covers it, one file per run, never overwrite an older one.

Where an older report sits beside this one, fill "Previous" and "Change" from it and lead the
body with what moved — new drift first, then drift that has gone.

Use the shape below and put the data in tables. The prose left over is the consumer sentence.

Then tell the user the report path, the probe file path, both numbers, and the one P1 drift to
take first.

**Done when:** the report sits in the module's `.reports` folder, `.reports/` is git-ignored, no
older report was overwritten, the probe file is named with each case's state, and every drift
from steps 6 and 8 appears in exactly one bucket with its evidence.

---

# Report shape

An OpenAPI report. The tables, columns, and buckets are what transfers — swap in your own
contract format, tool, and paths. Tables are shown with one or two data rows; a real report lists
them all.

````markdown
# API Contract Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Contract** | `api/openapi.yaml` — OpenAPI 3.1, version `2.4.0`, 40 operations |
| **Rung** | published — the file the team keeps in the repo |
| **Target** | `https://staging.example.com/api` — staging |
| **Auth** | bearer token from `$STAGING_TOKEN` |
| **Methods sent** | `GET`, `POST`, `PUT`, `PATCH` — `DELETE` withheld by the user |
| **Tool** | `schemathesis 3.36.0` |
| **Probes** | `test/contract/probes.test.ts` — 9 cases, 7 green, 2 skipped |
| **Command** | `<the command you ran>` |
| **Commit** | `<short sha>` (dirty working tree) |
| **Duration** | 6m 04s |
| **Previous** | [`contract-report-2026-07-30-091412.md`](./contract-report-2026-07-30-091412.md) |

## The two numbers

| | Value | Previous | Change |
| --- | --- | --- | --- |
| **Contract coverage** | **80.0%** — 32 of 40 operations exercised | 77.5% | +2.5 |
| **Conformance** | **78.1%** — 25 of 32 exercised operations with no drift | 84.4% | −6.3 |

Conformance is measured over the 32 that ran, never over all 40.

## What moved

| Drift | New this run | Gone | Still open | Total |
| --- | --- | --- | --- | --- |
| 🔴 P1 breaking | 2 | 1 | 1 | 3 |
| 🟠 P2 divergent | 1 | 0 | 5 | 6 |
| ⚪ P3 cosmetic | 0 | 0 | 4 | 4 |

**New since the last run:** `GET /orders/{id}` now returns `total` as a string.

## By operation

| Operation | Exercised | Requests | Drift | Worst bucket |
| --- | --- | --- | --- | --- |
| `GET /orders/{id}` | yes | 24 | 2 | 🔴 P1 |

Showing 12 of 40 operations. Full data in `.reports/contract-run.json`.

## Not exercised

| Operation | Why |
| --- | --- |
| `DELETE /orders/{id}` | the user withheld `DELETE` against staging |
| `POST /payments/refund` | needs a settled payment; no fixture in staging reaches that state |

Unproven, not passing. Eight operations, a fifth of the contract.

---

## 🔴 P1 — breaking

### 1. `GET /orders/{id}` — `total` is a string

| | |
| --- | --- |
| **Label** | shape |
| **Contract says** | `total: { type: number }`, required |
| **API does** | `"total": "129.99"` |
| **Consumer impact** | a client that reads `order.total` as a number receives a string and fails on the first calculation, silently in JavaScript and with a crash in a typed client |
| **Evidence** | `GET /api/orders/8842` → `200` · `{ "id": "8842", "total": "129.99" }` |
| **Fix side** | the **API**. The contract has declared `number` since `1.0.0`, and the field was a number in the report of 2026-07-30. |

---

## 🟠 P2 — divergent

| Operation | Label | Contract says | API does | Consumer impact | Fix side |
| --- | --- | --- | --- | --- | --- |
| `POST /orders` | undocumented | `201` and `400` only | also answers `409` when the idempotency key repeats | a consumer treats `409` as an unknown failure and retries a call that already succeeded | the **contract** — the behaviour is deliberate and in the changelog |

---

## ⚪ P3 — cosmetic

| Operation | Label | Drift |
| --- | --- | --- |
| `GET /orders` | undocumented | the `limit` example says `20`; the default the API applies is `25` |

---

## Probes

Kept in `test/contract/probes.test.ts`, run with `npm run test:contract`.

| Probe | Request | Response | Verdict | In the file |
| --- | --- | --- | --- | --- |
| Guard enforced | `GET /admin/reports`, no header | `200` + body | 🔴 P1 drift | skipped — names the P1 drift |
| Wrong media type | `POST /orders` as `text/plain` | `415` | 🟢 pass | green, proven red against an expected `200` |

---

## The gates

| Gate | Judged on | Where | State |
| --- | --- | --- | --- |
| Conformance run against staging | new drift | `.github/workflows/contract.yml` | not applied |
| Contract diff on contract changes | removed operations and fields, tightened requirements | `.github/workflows/ci.yml` | not applied |
| Probe suite on every pull request | the 7 green cases staying green | `.github/workflows/ci.yml` | not applied |
````

Every drift appears in exactly one bucket. Drop any empty section, keep both numbers and the
"Not exercised" table even when they are perfect, and lead the body with P1. Where no older
report sits beside this one, drop the "Previous" row, the "What moved" section, and the
"Previous" and "Change" columns.

A **derived** run keeps the same shape, with the header's **Rung** row reading like this and a
note added under the two numbers:

````markdown
| **Rung** | derived — generated from the FastAPI routes, saved to `api/openapi.derived.yaml`, unreviewed |

> This contract was written from the implementation, so the two agree by construction. Shape
> conformance is not tested here and the conformance number covers the probes alone. Review the
> derived file and publish it, and the next run measures the whole contract.
````
