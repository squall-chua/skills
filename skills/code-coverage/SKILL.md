---
name: code-coverage
description: >
  Run the test suite with coverage on, rank the uncovered gaps by risk, and
  report per module and per file with a suggested test for each gap.
disable-model-invocation: true
---

Coverage is a floor, not a proof. It tells you a line **ran**. It never tells you
the line is **checked** — a test with no assertion covers just as much as a good
one. So the percentage on its own is close to worthless. What is worth having is
the ranked list of **gaps** underneath it, in the order a person should close
them. This skill ends with that list written down, each gap carrying the
behaviour nobody tests and a concrete test to add.

To find out whether the *covered* lines are actually checked, use
[`mutation-test`](../mutation-test/SKILL.md) instead. The two answer different
questions, and this one answers the easier half.

## This skill reports

It measures, ranks, and writes up. The tests stay exactly as they are, and the
suggestions in step 5 are left on the page for a person to accept or reject. A
report the user did not ask to act on is the whole deliverable — finish at step
7 and hand it over.

Write the tests only when the user gives a **fix signal**: "fix the coverage",
"close the gaps", "write those tests", "go ahead". Steps 8 and 9 then follow,
and they end in a second report that sits beside the first. The step 7 report is
the before, so it gets written on a fix run too, and it gets written before any
test is touched.

## 1. Take the baseline

Find and run the project's existing test suite, with coverage still off. It must
be green. A failing suite can stop early and leave whole files unexecuted, so
every number below it becomes a guess. Skipped tests do the same thing quietly:
a test that does not run covers nothing.

Record the exact command, the pass, fail, and skip counts, and the runtime.

**Done when:** the suite is green on a clean tree, and you have written down its
command, all three counts, and its runtime.

## 2. Turn coverage on and fix the denominator

Prefer the tool the project already has. Otherwise pick by language:

| Language | Tool |
| --- | --- |
| JavaScript / TypeScript | `vitest --coverage`, `jest --coverage`, `c8`, `nyc` |
| Go | `go test -coverprofile=coverage.out ./...` |
| Python | `coverage.py`, `pytest --cov` |
| Java / Kotlin | JaCoCo |
| C# / .NET | Coverlet |
| Rust | `cargo-llvm-cov`, `cargo-tarpaulin` |
| PHP | PHPUnit with Xdebug or PCOV |
| Ruby | SimpleCov |
| Swift | `swift test --enable-code-coverage` with `llvm-cov` |
| Elixir | ExCoveralls |

Read the tool's own documentation for its current flags. Names drift between
versions, and a config written from memory fails in ways that look like broken
code.

Set four things:

- **Branch coverage on.** Several tools report lines only by default, and line
  coverage flatters: a one-line `if` whose else-branch is never taken still
  counts as a covered line.
- **A machine-readable report** — lcov, Cobertura XML, JSON, or Go's
  coverprofile — written beside any HTML. You will read the machine-readable one.
- **The include list**: the code that holds decisions. Business rules,
  calculations, guards, state changes.
- **The exclude list**: test files, generated code, vendored dependencies,
  migrations, and plain configuration.

Every exclusion moves the denominator, so write down each one and its reason. An
exclusion nobody can justify is a number that lies.

One trap worth knowing: `go test -cover ./...` measures each package only
against its own tests. When tests in one package exercise another, add
`-coverpkg=./...` or the exercised packages read as untested.

Leave the configuration file in the repo, so the next run and the CI run use the
same settings.

**Done when:** a coverage run completes over the whole scope, branch data is
present in the output, the machine-readable file exists on disk, and every
exclusion is written down with a reason.

## 3. Read the numbers

Roll the machine-readable report up twice.

First by the project's own unit of grouping — Go package, Java or Python
package, .NET namespace, or the top source directories for JavaScript and
TypeScript. Then again per file.

At each level record lines covered and total, branches covered and total,
functions covered and total, and the percentage for each.

Record the test count beside them. Take it from the runner's own per-file
results, which nearly every runner emits in its JSON or JUnit XML report, and
pair each test file to the source file it is named for — `pricing.ts` with
`pricing.test.ts`, `pricing.py` with `test_pricing.py`, `pricing.go` with
`pricing_test.go`. A source file with no test file named for it counts zero. Say
once in the report that the count is a name pairing, not a measurement: a test
named for one file may exercise several, and coverage can arrive from an
integration test that pairs with nothing.

The count is worth having because coverage alone cannot tell these apart. A file
at 88% behind 40 tests is well examined. The same 88% behind 2 tests means two
broad tests walk most of the code and assert almost nothing about it — and that
is a stronger signal to act on than the percentage.

Look at the shape, not just the average. A repo at 80% with one payment module
at 0% is in worse shape than a repo flat at 70%, and the average hides that. A
wide gap between line coverage and branch coverage is the other tell: it means
the tests walk through the code but only ever down one path.

Pull out four lists:

- Files at 0%, and whether a test file is named for them at all.
- Files below the project's median file coverage.
- Files with a high coverage percentage and a low test count. Coverage is
  arriving from somewhere else, and little is being asserted here.
- Lines that are covered but hold an uncovered branch. These are the cheap wins.

**Done when:** you have the totals, a per-module table and a per-file table each
carrying test counts, and the four lists above.

## 4. Rank the gaps by risk

Uncovered lines are not equal. An untested log formatter costs nothing. An
untested discount rule costs money. Rank with two facts you can measure and one
you have to read for.

**Churn** — how often the file changes:

```sh
git log --since='6 months ago' --name-only --format= -- <path> | grep . | sort | uniq -c | sort -rn
```

The `grep .` matters: `--name-only` prints a blank line between commits, and
without it the blank is counted and sorts to the top as your busiest file.

A file that changes often and is not covered breaks often and quietly.

**Size of the gap** — uncovered lines and uncovered branches in that file.

**What the code decides** — read it. Money, permissions, data writes, and calls
to other systems carry more risk than formatting and glue.

Then put every file with a gap in one bucket:

- **P1** — decides money, permissions, or data writes, and is at 0% or has
  uncovered branches.
- **P2** — changed 5 or more times in the last 6 months and sits below the
  project's median coverage.
- **P3** — everything else with a gap.

**Done when:** every file with a gap sits in exactly one bucket, and P1 and P2
are each ordered worst first.

## 5. Name the gap and suggest the test

Work through P1 and P2, file by file. Read the uncovered code and write one
sentence naming the behaviour that nobody tests — the behaviour, not the line
numbers. "Nothing runs the refund path for an order that was already refunded"
is useful. "Lines 40 to 52 are uncovered" is a restatement of the report.

Then label each gap:

- **Untested file** — no test file exists for it. One new file moves it a long
  way.
- **Untested branch** — the line runs, but only one side of the `if`, the
  ternary, or the `||` ever does.
- **Untested error path** — the happy path runs; the failure, the catch, the
  timeout never do.
- **Untested edge** — boundaries, empty collections, nulls, zero, the maximum.
- **Unreachable** — nothing in the product can reach it. That is a finding about
  the code, not about the tests. Raise it with the user; do not write a test to
  reach dead code.
- **Not worth covering** — generated code, trivial getters, program wiring.
  Suggest excluding it, and say what the percentage becomes without it.

Then write the suggestion, and make it concrete: which test file it goes in,
what the case is called, and the input that reaches the gap. "Add more tests for
refunds" is not a suggestion — it is the problem restated.

**Done when:** every P1 and P2 gap carries a behaviour sentence, exactly one
label, and a concrete suggested test. P3 is summarised by module with counts. If
any gap was left off the report, its count is stated.

## 6. Work out the ratchet

Recommend a threshold set to the number you just measured, rounded down to the
nearest whole point, so it can only go up. A ratchet holds. A target of 90% set
on a 60% repo fails every build until somebody deletes it, and then there is no
gate at all.

Recommend gating pull requests on the coverage of the changed lines, not on the
whole-repo percentage. The whole-repo number moves when a well-covered file is
deleted, so it makes a dishonest gate: one pull request fails for code it never
touched, the next passes for deleting something.

Say plainly in the report that the number goes up by covering behaviour. A
number raised by widening the exclude list, or by tests that execute code
without asserting on it, is a lie to the next reader.

This step only works the numbers out. Nothing is edited here on any run — step 8
does the applying, after the before report at step 7 has recorded the state the
repo was in. A threshold written into the config now would make that report
describe a repo that no longer exists.

Two consequences worth holding on to. The threshold recommended here comes from
the *before* numbers, and on a fix run step 9 raises it again to the number
actually achieved — a gate left at the before figure lets every point of the work
slide straight back. And every gate row in the step 7 report reads "not applied",
because at that moment none of them are.

**Done when:** you have the threshold number and the changed-lines gate written
down for the report, and the config and CI files are untouched.

## 7. Write the report

Run `date '+%Y-%m-%d-%H%M%S'` for the timestamp and `git rev-parse --short HEAD`
for the commit. Both go in the header. Note a dirty working tree there too,
since the run then covers code that commit does not hold.

Write the report to `<module>/.reports/coverage-report-<timestamp>.md`, where
`<module>` is the root of the module the run covered — the nearest directory at
or above the scope that holds the project's manifest (`package.json`, `go.mod`,
`pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`, a
`*.csproj`). A run spanning several modules writes to the repository root.

Create the folder if it is missing, and keep it out of version control: add
`.reports/` to the repository's root `.gitignore` when nothing there covers it
already. One file per run, and no run ever overwrites an older file.

Write this report even on a fix run, and write it *before* you touch a test.
This is the before. Without it there is nothing to compare the after against,
and a number you remember is not a number you can show.

Use the shape below, and put the data in tables. Every number, path, label, and
suggested case belongs in a table cell where it can be scanned and compared. The
prose left over is the one-sentence untested behaviour, and the short note under
a table that says what the numbers mean. Leave the "Previous" and "Change"
columns empty unless an earlier report sits beside this one.

Then tell the user the file path, the line and branch percentages, and the
single P1 gap they should close first. On a report-only run, say that the report
is all this run changed, so they can ask for the gaps to be closed if they want
that next.

**Done when:** the report file sits in the module's `.reports` folder, `.reports/`
is ignored by git, no older report was overwritten, and the report holds the
totals, the test counts per module and per file, the per-module table, the per-file table, every P1 and P2 gap
with its behaviour sentence, label, and suggested test, and the exclusion list
with reasons.

## 8. Close the gaps — on a fix signal

Without the signal, the work is finished at step 7. Hand over the report.

Work the P1 list from the top, then P2, one gap at a time:

1. Write the test for the behaviour you named in step 5.
2. Run it and watch it pass for the right reason — it must exercise the gap.
   Confirm that by checking the line and branch now register as covered.
3. Run the full suite and confirm it is green.

Then apply the ratchet, and set it from the numbers you have *now*, not the ones
step 6 worked out. Step 9 re-runs coverage; take the threshold from that result,
rounded down, and put it in the config with the changed-lines gate in CI. A gate
left at the before figure lets every point you just gained slide back without
failing a build.

Raise the number by covering behaviour. A number raised by widening the exclude
list, or by a test that runs the code without asserting on the result, is a lie
to the next reader — and `mutation-test` finds those tests.

When a gap can only be covered by changing the source, the gap found dead code
or a bug. Write it up as a finding and move to the next one.

**Done when:** every P1 and P2 gap from step 5 is one of three things — covered
by a new test that passes with the suite green, raised as a finding about the
code, or deferred with a stated reason. None are simply unmentioned. The ratchet
is applied, and its threshold matches the re-run in step 9 rather than step 6's
recommendation.

## 9. Write the after report — on a fix signal

Re-run the same coverage command from step 2 over the same scope. That result is
what the ratchet threshold comes from, so do this before the config edit in step
8 settles, and record the final threshold here.

Take a fresh timestamp and write a second file into the same `.reports` folder.
The step 7 report stays where it is, untouched. Two files, so the move is on the
record and anyone can read the before for themselves.

Fill the "Previous" and "Change" columns from the step 7 report, and lead the
body with a "What moved" section that names that file. Give each of these its
own table:

- lines, branches, and functions before and after, with the point difference;
- which modules gained, and which did not move;
- how many gaps were closed, how many are still open, and how many were
  deferred;
- any file whose coverage dropped. That is a regression, and it is the first
  thing the reader needs.

Then tell the user both file paths, the two sets of percentages, and what is
still open.

**Done when:** both report files exist side by side, the after report names the
before file and states the point differences, and every P1 and P2 gap from the
step 7 report appears in it with its outcome.

---

# Report shape

The example below is a TypeScript project. The tables, the columns, and the
buckets are what transfers — swap in the tool, the paths, and the metric names
your language actually uses.

````markdown
# Code Coverage Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Tool** | `vitest 3.0.5 (v8)` |
| **Command** | `<the command you ran>` |
| **Commit** | `<short sha>` (dirty working tree) |
| **Scope** | `src/**` — 84 files, 6 excluded |
| **Suite** | 412 passed, 0 failed, 3 skipped |
| **Duration** | 1m 04s |
| **Before** | [`coverage-report-2026-07-30-091412.md`](./coverage-report-2026-07-30-091412.md) |

## What moved

Against `coverage-report-2026-07-30-091412.md`, taken before any test was
written.

| Metric | Before | After | Change |
| --- | --- | --- | --- |
| **Lines** | 74.1% | **78.4%** | **+4.3** |
| **Branches** | 59.9% | **60.8%** | **+0.9** |
| **Functions** | 86.4% | **87.0%** | **+0.6** |

| Gap outcome | P1 | P2 | P3 |
| --- | --- | --- | --- |
| 🟢 Closed | 6 | 3 | 0 |
| ⏸️ Deferred | 1 | 0 | 0 |
| 🔧 Raised as a finding | 1 | 0 | 0 |
| 🔴 Still open | 0 | 9 | 41 |
| **Total** | **8** | **12** | **41** |

| Module | Before | After | Change |
| --- | --- | --- | --- |
| `src/domain/refunds` | 41.7% | 96.1% | +54.4 |
| `src/domain/pricing` | 91.0% | 94.2% | +3.2 |
| `src/http` | 72.9% | 72.9% | 0.0 |

**Lost coverage:** none.

## Totals

| Metric | Covered | Total | % | Previous | Change |
| --- | --- | --- | --- | --- | --- |
| **Lines** | 4,812 | 6,140 | **78.4%** | 74.1% | +4.3 |
| **Branches** | 1,204 | 1,980 | **60.8%** | 59.9% | +0.9 |
| **Functions** | 611 | 702 | **87.0%** | 86.4% | +0.6 |

Branches sit 18 points below lines. The tests walk the code but take one path
through it, and that spread is where the untested decisions live.

## By module

| Module | Files | Tests | Lines % | Branches % | Functions % | Worst file |
| --- | --- | --- | --- | --- | --- | --- |
| `src/domain/pricing` | 6 | 148 | 94.2% | 88.1% | 96.0% | `rounding.ts` (81.0%) |
| `src/domain/refunds` | 4 | 9 | 41.7% | 22.0% | 50.0% | `eligibility.ts` (0.0%) |
| `src/http` | 11 | 71 | 72.9% | 55.3% | 80.1% | `errorMapper.ts` (30.4%) |

## By file — worst first

Tests counts the tests in the file named for this one. It is a name pairing, not
a measurement: a test named for one file may exercise several, and coverage can
arrive from an integration test that pairs with nothing.

| File | Lines | Uncovered | Tests | Lines % | Branches % | Churn 6mo | Bucket |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `src/domain/refunds/eligibility.ts` | 148 | 148 | 0 | 0.0% | 0.0% | 11 | P1 |
| `src/http/errorMapper.ts` | 92 | 64 | 4 | 30.4% | 18.2% | 3 | P2 |
| `src/domain/pricing/discount.ts` | 76 | 9 | 21 | 88.2% | 61.5% | 7 | P1 |
| `src/domain/pricing/rounding.ts` | 40 | 8 | 2 | 81.0% | 50.0% | 2 | P3 |

Showing the 20 worst of 61 files with a gap. The full data is in
`coverage/lcov.info`.

`rounding.ts` is the shape worth noticing: 81% behind 2 tests. The coverage is
arriving from the pricing tests next door, and almost nothing here is asserted
directly.

---

## 🔴 P1 — close these first

### 1. `src/domain/refunds/eligibility.ts` — whole file at 0%

| | |
| --- | --- |
| **Uncovered** | 148 of 148 lines · 22 of 22 branches |
| **Tests** | 0 — no file is named for it |
| **Churn** | 11 commits in 6 months |
| **Decides** | whether refund money goes out |
| **Label** | untested file |
| **Untested behaviour** | nothing exercises refund eligibility at all — the 30-day window check, the already-refunded guard, and the partial-refund rule run only in production |
| **Suggested test** | new file `src/domain/refunds/eligibility.test.ts` |
| **Outcome** | 🟢 closed |

| Case | Input | Expected |
| --- | --- | --- |
| `rejects a refund after the 30-day window` | order dated 31 days back | rejected |
| `rejects an order already refunded` | `status: 'refunded'` | rejected |
| `allows a partial refund below the amount paid` | paid 100, requested 40 | allowed |

### 2. `src/domain/pricing/discount.ts:88` — uncovered branch

| | |
| --- | --- |
| **Uncovered** | 9 of 76 lines · 5 of 13 branches |
| **Tests** | 21 in `discount.test.ts` |
| **Churn** | 7 commits in 6 months |
| **Decides** | the discount applied to an order |
| **Label** | untested branch |
| **Untested behaviour** | no test has a gold customer spending over 500, so the 15% tier discount is never applied in any test run |
| **Suggested test** | add to `src/domain/pricing/discount.test.ts` |
| **Outcome** | ⏸️ deferred — needs the customer-tier fixtures |

```ts
if (customer.tier === 'gold' && order.total > 500) {  // ← true side never runs
  discount = order.total * 0.15
}
```

| Case | Input | Expected |
| --- | --- | --- |
| `applies the 15% gold discount above 500` | `{ tier: 'gold', total: 501 }` | discount `75.15` |
| `does not apply it at exactly 500` | `{ tier: 'gold', total: 500 }` | discount `0` |

---

## 🟠 P2 — changes often, covered least

| File · lines | Lines % | Churn | Label | Untested behaviour | Suggested test | Outcome |
| --- | --- | --- | --- | --- | --- | --- |
| `src/http/errorMapper.ts:40-96` | 30.4% | 3 | untested error path | every mapping from a domain error to an HTTP status is untested except the 200 path | `errorMapper.test.ts` — one case per error type asserting the status and the body | 🔴 open |
| `src/http/retry.ts:22-31` | 48.0% | 6 | untested edge | the retry loop is never entered with `attempts: 0` | `retry.test.ts` — `does not call the handler when attempts is 0` | 🟢 closed |

---

## ⚪ P3 — the rest

| Module | Files with a gap | Uncovered lines |
| --- | --- | --- |
| `src/cli` | 9 | 341 |
| `src/util` | 14 | 210 |

41 files and 980 uncovered lines, not listed one by one.

---

## Findings for the code

| File · line | Finding | Suggested action |
| --- | --- | --- |
| `src/legacy/oldRefund.ts:44-70` | unreachable — every caller sets `mode` to `standard` or `partial`, so no input reaches this branch | delete the branch, or say what should reach it |

---

## Excluded from the denominator

| Path | Reason |
| --- | --- |
| `src/**/*.gen.ts` | generated from the OpenAPI schema |
| `src/main.ts` | program wiring, no decisions |
| **Without these** | line coverage reads **71.2%** instead of 78.4% |

---

## The ratchet

| Setting | Value | File | State |
| --- | --- | --- | --- |
| `coverage.thresholds.lines` | 78 | `vitest.config.ts` | applied |
| `coverage.thresholds.branches` | 60 | `vitest.config.ts` | applied |
| changed-lines gate | required on pull requests | `.github/workflows/ci.yml` | not applied |

Thresholds are set to the number measured, so they can only go up. Pull requests
are gated on the coverage of the changed lines, never on the whole-repo
percentage.
````

Every file with a gap appears in exactly one bucket. Drop any section with no
entries, and lead the body with P1.

The before report is the same shape, shorter: no "Before" row, no "What moved",
no "Outcome" rows or columns, and the "Previous" and "Change" columns only if an
older report sits beside it. Every ratchet row reads "not applied".

On a fix run, the after report adds the **Outcome** row to each P1 entry and the
**Outcome** column to the P2 table, and every closed gap gains a **Covered by**
row or column naming the test that now covers it.
