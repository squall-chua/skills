# Report shape

A TypeScript service example. The tables, grades, and dimensions are what transfers — swap in
your own tools and paths. Tables are shown with one or two rows; a real report lists them all.

````markdown
# Release Quality Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Commit** | `a1b2c3d` (clean) |
| **Scope** | the `orders` service, deployed |
| **Environment** | staging — 2× `t3.large`, Postgres 15.4, 40 GB of data. Production is 4× `t3.large`, Postgres 15.4, 900 GB |
| **Phase** | release — the running system. Not a code verdict |
| **Starting position** | thin — 4 of 5 applicable dimensions measured, 3 of them Fragile |
| **Bands** | project SLO where set, defaults otherwise |
| **Previous** | [`release-quality-report-2026-07-23-140218.md`](./release-quality-report-2026-07-23-140218.md) |

## Verdict

# 🔴 Fragile — 1 of 5 applicable dimensions unproven

## Not ready to release

A signing key is committed in `src/http/session.ts:18` and has not been rotated. That alone
holds the release, and it outranks everything else on this list. Behind it, the order consumer
never recovered from a broker restart: checkout keeps returning 200, so orders are accepted and
silently never processed.

Last week's verdict was 🟡 Thin, on the same environment. Headroom set the floor then and
exposure sets it now, on a live secret that did not exist in the previous run.

**Not covered here.** These five describe the running system. Nothing above says how much of the
code runs under test, whether the tests assert anything, or what the code reads like — run
`/code-quality` for those seven. Access and signature need a rendered interface — run
`/visual-quality`.

## Dimensions

| Dimension | Relevance | Grade | The numbers | Environment | Evidence | Behind HEAD |
| --- | --- | --- | --- | --- | --- | --- |
| Promised behaviour | applies | 🔴 Fragile | conformance 78.1%, contract coverage 80.0%, 3 P1 drift | same | [contract](./contract-report-2026-07-30-144510.md) | 0 commits |
| Proven seams | applies | 🟡 Thin | seam coverage 66.7%, hermetic passed, 2 seams unproven | same | [integration](./integration-report-2026-07-30-151133.md) | 1 commit |
| Resilience | applies | 🔴 Fragile | pass rate 81.8%, 1 experiment never recovered | same | [fault injection](./fault-report-2026-08-01-093044.md) | 0 commits |
| Headroom | applies | ⚫ Unproven | knee 290 req/s on 40 GB of data | **changed** — run against a 40 GB database; production holds 900 GB | [stress](./stress-report-2026-08-01-104530.md) | 0 commits |
| Exposure | applies | 🔴 Fragile | 4 P1 — 1 unrotated secret, 1 reachable CVE, 2 access control | same | [security](./security-report-2026-07-31-140203.md) | 0 commits |

Exposure, promised behaviour, and resilience are jointly at the floor, so the verdict is
🔴 Fragile. Headroom is Unproven rather than 🟡 Thin: the run measured a database a twentieth
the size of production, so its knee describes a system nobody operates.

## What is not graded here

| Dimension | Relevance | Why |
| --- | --- | --- |
| — | — | all five apply to this service |

Had the ask been `src/domain/` rather than the service, promised behaviour, resilience,
headroom, and the live half of exposure would sit here, marked **out of scope**.

## What the signals say together

| The pair | The numbers | What it means |
| --- | --- | --- |
| A P1 exposure finding on an endpoint that also drifts | `POST /orders` — missing authorization check, and `total` now returns as a string | the endpoint is both reachable and wrong. Fixing one leaves the other live on the same URL |
| Thin headroom, an experiment that never recovered | 1.6× on the previous run, order consumer stalled on a broker restart | overload and failure arrive together in practice, and this system handles neither |
| Green suite, breaking contract drift *(crosses into `/code-quality`)* | 412 tests green, `GET /orders/{id}` returns `total` as a string | the suite checks the code against itself. The promise to callers broke and nothing in CI noticed |

## Dimensions to cover next

| Dimension | Relevance | Run | Costs | Needs first | What it would tell you |
| --- | --- | --- | --- | --- | --- |
| Headroom | applies | `/stress-test` | an afternoon or more | a staging database sized like production, and a peak figure somebody will defend | what traffic it takes before it stops keeping up, on the data volume it actually runs on |

## The next moves

**Start here:** rotate the signing key and take it out of the source. Minutes of work, and
nothing else on this list matters while a live key sits in git history.

The rest of the list keeps. Run `/release-quality` again when that one is done and it will name
the move after it.

| # | Do this | Why it is here | Costs | Needs first | Command |
| --- | --- | --- | --- | --- | --- |
| 1 | Rotate the signing key, then remove it from the source | a committed secret is live until the key changes, and git history keeps it | minutes | — | — |
| 2 | Make the order consumer recover on its own, and alert on lag | any broker blip stalls it for good. Checkout keeps returning 200, so orders are accepted and never processed and nothing reports it | a day | — | `/fault-injection-test` |
| 3 | Re-run the load test against a production-sized database | the 290 req/s knee was measured on a fortieth of the data. It says nothing about the system being released | an afternoon | a staging database restored from a production snapshot | `/stress-test` |

## Next phase

| Phase | Dimensions | Command |
| --- | --- | --- |
| Development | verified behaviour, test strength, change risk, specified behaviour, construction, single source, readability | `/code-quality` |
| Visual | access, signature | `/visual-quality` |
````

Drop any empty section, and lead the body with the verdict and the release line. The dimension
that set the floor is named in the verdict and appears first among the moves that are not
outright defects.

An **unproven** system's report is the same shape with two differences: the release line is
"Unknown", and the moves table holds the step 7 ladder in that order, with each move naming the
environment or permission it waits on. It closes on the two things step 7 says an unproven plan
must state: that the verdict stays ⚫ Unproven until move 4 lands, and which moves are blocked on
a platform conversation rather than on effort.
