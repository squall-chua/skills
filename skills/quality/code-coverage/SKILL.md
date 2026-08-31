---
name: code-coverage
description: >
  Run the test suite with coverage on, rank the uncovered gaps by risk, and
  report per module and per file with a suggested test for each gap.
disable-model-invocation: true
---

Coverage is a floor, not a proof. It says a line **ran**, never that it is **checked** —
a test with no assertion covers as much as a good one. The percentage alone is close to
worthless; the ranked list of **gaps** underneath it is what is worth having. This skill
ends with that list written down, each gap carrying the behaviour nobody tests and a
concrete test to add.

## This skill reports

Steps 1 to 7 measure, rank, and write up. The tests stay exactly as they are and the step
5 suggestions are left on the page for a person to accept or reject. That report is the
whole deliverable.

Steps 8 and 9 run only on a **fix signal**: "fix the coverage", "close the gaps", "write
those tests", "go ahead". The step 7 report is the *before*, so it is written on a fix run
too, and written before any test is touched.

## 1. Take the baseline

Run the project's existing suite with coverage still off. It must be green: a failing suite
can stop early and leave whole files unexecuted, which makes every number below a guess.
Skipped tests do the same quietly — a test that does not run covers nothing.

**Done when:** the suite is green on a clean tree, and you have written down its command,
its pass / fail / skip counts, and its runtime.

## 2. Turn coverage on and fix the denominator

Prefer the tool the project already has. Otherwise:

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

### Nothing installed?

Look before you install: the manifest and its lockfile, the CI workflows, the project's own
config files, and the binary on `PATH`. A tool declared in the manifest but missing from the
environment needs the project's own install command, not a new dependency.

Where the project genuinely has none, put the setup to the user in one message — the tool and
why it fits this project, the exact install command, the config file with its contents, the
command this skill will then run, and what it costs in download size and first-run time — and
wait for the go-ahead. A new dependency changes the manifest and the lockfile, which is the
user's call. Then install exactly that, leave the config in the repo, and commit nothing.

Coverage arrives two ways: some runners need only a flag, others need a provider package as
well. Check which before proposing anything.

Read the tool's own docs for current flags — names drift between versions, and a config
written from memory fails in ways that look like broken code.

Set four things:

- **Branch coverage on.** Several tools report lines only, and line coverage flatters: a
  one-line `if` whose else-branch never runs still counts as covered.
- **A machine-readable report** — lcov, Cobertura XML, JSON, or Go's coverprofile — beside
  any HTML. You read the machine-readable one.
- **The include list**: code that holds decisions — business rules, calculations, guards,
  state changes.
- **The exclude list**: test files, generated code, vendored dependencies, migrations,
  plain configuration.

Every exclusion moves the denominator, so write down each one and its reason. An exclusion
nobody can justify is a number that lies.

One trap: `go test -cover ./...` measures each package only against its own tests. Where
tests in one package exercise another, add `-coverpkg=./...` or the exercised packages read
as untested.

Leave the config file in the repo, so the next run and CI use the same settings.

**Done when:** the tool was already present or the user approved its setup, a coverage run
completes over the whole scope, branch data is in the output, the machine-readable file
exists on disk, and every exclusion is written down with a reason.

## 3. Read the numbers

Roll the machine-readable report up twice: first by the project's own unit of grouping — Go
package, Java or Python package, .NET namespace, or the top source directories for JS and
TS — then per file. At each level record lines, branches, and functions, covered and total,
with the percentage for each.

Record the test count beside them. Take it from the runner's own per-file results (nearly
every runner emits these in JSON or JUnit XML) and pair each test file to the source file it
is named for — `pricing.ts` with `pricing.test.ts`, `pricing.py` with `test_pricing.py`,
`pricing.go` with `pricing_test.go`. A source file with no test file named for it counts
zero. Say once in the report that this is a name pairing, not a measurement: a test named
for one file may exercise several, and coverage can arrive from an integration test that
pairs with nothing.

The count is worth having because coverage alone cannot tell these apart. A file at 88%
behind 40 tests is well examined. The same 88% behind 2 tests means two broad tests walk
most of the code and assert almost nothing about it — a stronger signal than the percentage.

Look at the shape, not the average. A repo at 80% with one payment module at 0% is in worse
shape than a repo flat at 70%, and the average hides that. A wide gap between line and
branch coverage is the other tell: the tests walk the code but only down one path.

Pull out four lists:

- Files at 0%, and whether a test file is named for them at all.
- Files below the project's median file coverage.
- Files with high coverage and a low test count — coverage is arriving from elsewhere and
  little is asserted here.
- Lines covered but holding an uncovered branch. The cheap wins.

**Done when:** you have the totals, a per-module and a per-file table each carrying test
counts, and the four lists above.

## 4. Rank the gaps by risk

An untested log formatter costs nothing; an untested discount rule costs money. Rank with
two facts you can measure and one you must read for.

**Churn** — how often the file changes:

```sh
git log --since='6 months ago' --name-only --format= -- <path> | grep . | sort | uniq -c | sort -rn
```

The `grep .` matters: `--name-only` prints a blank line between commits, and without it the
blank sorts to the top as your busiest file. A file that changes often and is not covered
breaks often and quietly.

**Churn you can see right now beats churn from six months ago.** A file changed on this branch
is being edited today, so an uncovered gap in it is the gap most likely to ship:

```sh
base=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)
if [ -z "$base" ]; then
  for c in origin/main origin/master origin/develop main master; do
    git rev-parse --verify --quiet "$c" >/dev/null && base=$c && break
  done
fi
[ -n "$base" ] && git diff --name-only "$base"...HEAD
```

Files on that list sort first inside whichever bucket they land in. They do not get their own
bucket and they do not skip the risk test below — an untested log formatter you touched this
morning is still P3.
Both empties need saying out loud. **An empty `$base`** means no branch to compare against —
no `origin`, or a remote named something else — and a silent empty list reads as "nothing is
being edited", which is the opposite of what it means. **An empty diff against a good base**
usually means the work is still in the working tree, so add `git diff --name-only HEAD` and
`git status --porcelain` to catch this morning's edits. The three-dot diff only sees committed
work, and on `main` it sees nothing at all.

**Size of the gap** — uncovered lines and branches in that file.

**What the code decides** — read it. Money, permissions, data writes, and calls to other
systems carry more risk than formatting and glue.

Then bucket every file with a gap:

- **P1** — decides money, permissions, or data writes, and is at 0% or has uncovered
  branches.
- **P2** — changed 5+ times in 6 months and sits below the project's median coverage.
- **P3** — everything else with a gap.

**Done when:** every file with a gap sits in exactly one bucket, and P1 and P2 are each
ordered worst first.

## 5. Name the gap and suggest the test

Work through P1 then P2, file by file. Read the uncovered code and write one sentence naming
the behaviour nobody tests — the behaviour, not the line numbers. "Nothing runs the refund
path for an order that was already refunded" is useful; "Lines 40 to 52 are uncovered"
restates the report.

Label each gap:

- **Untested file** — no test file exists for it. One new file moves it a long way.
- **Untested branch** — the line runs, but only one side of the `if`, the ternary, or the
  `||` ever does.
- **Untested error path** — the happy path runs; the failure, catch, or timeout never does.
- **Untested edge** — boundaries, empty collections, nulls, zero, the maximum.
- **Unreachable** — nothing in the product can reach it. A finding about the code, not the
  tests. Raise it with the user; do not write a test to reach dead code.
- **Not worth covering** — generated code, trivial getters, program wiring. Suggest
  excluding it, and say what the percentage becomes without it.

Then make the suggestion concrete: which test file, what the case is called, and the input
that reaches the gap. "Add more tests for refunds" is the problem restated.

**Done when:** every P1 and P2 gap carries a behaviour sentence, exactly one label, and a
concrete suggested test; P3 is summarised by module with counts; and any gap left off the
report has its count stated.

## 6. Work out the ratchet

Recommend a threshold set to the number you just measured, rounded down to the whole point,
so it can only go up. A ratchet holds; a 90% target on a 60% repo fails every build until
somebody deletes it, and then there is no gate at all.

Recommend gating pull requests on the coverage of the **changed lines**, not the whole-repo
percentage. The whole-repo number moves when a well-covered file is deleted, which makes a
dishonest gate: one pull request fails for code it never touched, the next passes for
deleting something.

Say plainly in the report that the number goes up by covering behaviour. A number raised by
widening the exclude list, or by tests that execute code without asserting on it, is a lie
to the next reader — and `mutation-test` finds those tests.

Nothing is edited here on any run; step 8 applies, after the step 7 before-report has
recorded the state the repo was in. So every gate row in the step 7 report reads "not
applied", because at that moment none of them are.

**Done when:** you have the threshold number and the changed-lines gate written down for the
report, and the config and CI files are untouched.

## 7. Write the report

Header: the timestamp from `date '+%Y-%m-%d-%H%M%S'`, the commit from `git rev-parse --short
HEAD`, and a note if the working tree is dirty — the run then covers code that commit does
not hold.

Write to `<module>/.reports/coverage-report-<timestamp>.md`. `<module>` is the nearest
directory at or above the scope holding the project's manifest (`package.json`, `go.mod`,
`pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`, `*.csproj`); a run
spanning several writes to the repository root. Create the folder if missing, add
`.reports/` to the root `.gitignore` if nothing there covers it, one file per run, never
overwrite an older one.

**Keep the machine-readable coverage file beside it**, under the report's own timestamp —
`coverage-<timestamp>.lcov`, `.info`, `.out`, `.xml`, `.json`, whatever the tool wrote. It
costs nothing to keep and it is the exact input `/crap-test` needs. Without it that skill runs
the whole suite with coverage on a second time to rebuild a file that existed ten minutes ago,
which on a large suite is the expensive half of both runs done twice. Name it in the report
header beside the tool and the command that produced it.

Write this report on a fix run too, and *before* you touch a test. This is the before;
without it there is nothing to compare against, and a number you remember is not a number
you can show.

Use the shape below and put the data in tables — every number, path, label, and suggested
case belongs in a cell where it can be scanned. The prose left over is the one-sentence
untested behaviour and a short note under a table saying what the numbers mean. Leave
"Previous" and "Change" empty unless an earlier report sits beside this one.

Then tell the user the file path, the line and branch percentages, and the one P1 gap to
close first. On a report-only run, say the report is all this run changed, so they can ask
for the gaps to be closed next.

**Done when:** the report sits in the module's `.reports` folder, the machine-readable
coverage file sits beside it under the same timestamp and is named in the header, `.reports/`
is git-ignored, no older report was overwritten, and it holds every section of the shape below
— including every P1 and P2 gap with its behaviour sentence, label and suggested test, and the
exclusion list with reasons.

## 8. Close the gaps — on a fix signal

Without the signal the work finished at step 7. Work P1 from the top, then P2, one gap at a
time:

1. Write the test for the behaviour you named in step 5.
2. Run it and watch it pass for the right reason — confirm the line and branch now register
   as covered.
3. Run the full suite and confirm it is green.

Then apply the ratchet, set from the numbers you have *now*, not step 6's. Step 9 re-runs
coverage; take the threshold from that result, rounded down, and put it in the config with
the changed-lines gate in CI. A gate left at the before figure lets every point you just
gained slide back without failing a build.

Where a gap can only be covered by changing the source, the gap found dead code or a bug.
Write it up as a finding and move on.

**Done when:** every P1 and P2 gap from step 5 is one of three things — covered by a new test
that passes with the suite green, raised as a finding about the code, or deferred with a
stated reason. None are simply unmentioned. The ratchet is applied at the step 9 re-run's
number, not step 6's recommendation.

## 9. Write the after report — on a fix signal

Re-run the step 2 coverage command over the same scope. That result is where the ratchet
threshold comes from, so do this before the step 8 config edit settles, and record the final
threshold here.

Fresh timestamp, second file in the same `.reports` folder; the step 7 report stays
untouched, so anyone can read the before for themselves.

Fill "Previous" and "Change" from the step 7 report, and lead the body with a "What moved"
section naming that file. Give each of these its own table:

- lines, branches, and functions before and after, with the point difference;
- which modules gained and which did not move;
- how many gaps were closed, are still open, and were deferred;
- any file whose coverage dropped. That is a regression, and the first thing the reader
  needs.

Then tell the user both file paths, the two sets of percentages, and what is still open.

**Done when:** both reports sit side by side, the after report names the before file and
states the point differences, and every P1 and P2 gap from step 7 appears with its outcome.

---

# Report shape

A TypeScript after-report. The tables, columns, and buckets are what transfers — swap in
your own tool, paths, and metric names. Every table here is shown with one or two data rows;
a real report lists them all.

````markdown
# Code Coverage Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Tool** | `vitest 3.0.5 (v8)` |
| **Command** | `<the command you ran>` |
| **Data** | [`coverage-2026-07-30-142205.json`](./coverage-2026-07-30-142205.json) — the machine-readable file, kept for `/crap-test` |
| **Commit** | `<short sha>` (dirty working tree) |
| **Scope** | `src/**` — 84 files, 6 excluded |
| **Suite** | 412 passed, 0 failed, 3 skipped |
| **Before** | [`coverage-report-2026-07-30-091412.md`](./coverage-report-2026-07-30-091412.md) |

## What moved

Against the before report, taken before any test was written.

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

Modules gained: `src/domain/refunds` 41.7% → 96.1%. Did not move: `src/http`, 72.9%.
**Lost coverage:** none.

## Totals

| Metric | Covered | Total | % | Previous | Change |
| --- | --- | --- | --- | --- | --- |
| **Lines** | 4,812 | 6,140 | **78.4%** | 74.1% | +4.3 |
| **Branches** | 1,204 | 1,980 | **60.8%** | 59.9% | +0.9 |
| **Functions** | 611 | 702 | **87.0%** | 86.4% | +0.6 |

Branches sit 18 points below lines. The tests walk the code but take one path through it,
and that spread is where the untested decisions live.

## By module

| Module | Files | Tests | Lines % | Branches % | Functions % | Worst file |
| --- | --- | --- | --- | --- | --- | --- |
| `src/domain/refunds` | 4 | 9 | 41.7% | 22.0% | 50.0% | `eligibility.ts` (0.0%) |

## By file — worst first

Tests counts the tests in the file named for this one. A name pairing, not a measurement.

| File | Lines | Uncovered | Tests | Lines % | Branches % | Churn 6mo | Bucket |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `src/domain/refunds/eligibility.ts` | 148 | 148 | 0 | 0.0% | 0.0% | 11 | P1 |
| `src/domain/pricing/rounding.ts` | 40 | 8 | 2 | 81.0% | 50.0% | 2 | P3 |

Showing the 20 worst of 61 files with a gap. Full data in `coverage/lcov.info`.

`rounding.ts` is the shape worth noticing: 81% behind 2 tests. The coverage arrives from the
pricing tests next door, and almost nothing here is asserted directly.

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
| `allows a partial refund below the amount paid` | paid 100, requested 40 | allowed |

### 2. `src/domain/pricing/discount.ts:88` — uncovered branch

Same table, plus the uncovered code quoted so the untaken side is visible, and a case table
that pins the boundary from both directions:

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
| `src/http/errorMapper.ts:40-96` | 30.4% | 3 | untested error path | every mapping from a domain error to an HTTP status is untested except the 200 path | `errorMapper.test.ts` — one case per error type asserting status and body | 🔴 open |

---

## ⚪ P3 — the rest

| Module | Files with a gap | Uncovered lines |
| --- | --- | --- |
| `src/cli` | 9 | 341 |

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

Thresholds are set to the number measured, so they can only go up.
````

Every file with a gap appears in exactly one bucket. Drop any empty section, and lead the
body with P1.

The before report is the same shape, shorter: no "Before" row, no "What moved", no "Outcome"
rows or columns, "Previous" and "Change" only if an older report sits beside it, and every
ratchet row reading "not applied". On a fix run every closed gap also gains a **Covered by**
row naming the test that now covers it.
