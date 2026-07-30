---
name: mutation-test
description: >
  Break the source on purpose, find the mutants the tests fail to catch, and
  report each survivor with the behaviour nobody is checking.
disable-model-invocation: true
---

Coverage says a line ran. Mutation testing says a line is **checked**. Break the
code on purpose, one small edit at a time, and a suite worth having goes red.
Each edit is a **mutant**. A mutant the suite fails to notice is a **survivor**,
and every survivor marks a behaviour nobody is testing. This skill ends with
every survivor named and the missing behaviour written down.

## This skill reports

It runs the mutants and writes up what survived. The tests stay exactly as they
are. A report the user did not ask to act on is the whole deliverable — run
steps 1 to 6 and hand it over.

Kill the survivors only when the user gives a **fix signal**: "kill them", "fix
it", "write the tests", "go ahead". Steps 7 to 10 then follow, and they end in a
second report that sits beside the first. The step 6 report is the before, so it
gets written on a fix run too, and it gets written before any test is touched.

## 1. Take the baseline

Find and run the project's existing test suite on an unmodified tree. It must be
green. A red or flaky test poisons every verdict that follows: the tool cannot
tell a mutant it caught from a test that was already broken.

Record the exact command and the wall-clock runtime. The mutation run costs
roughly that runtime × the mutant count ÷ the parallelism, so this number sets
your expectations for step 2.

**Done when:** the suite is green on a clean tree, and you have written down its
command, its pass count, and its runtime.

## 2. Scope the run

Decide which source files get mutated. Mutate the code that holds decisions —
business rules, calculations, guards, state changes. Leave out test files,
generated code, vendored dependencies, migrations, and plain configuration.

Reckon on tens of mutants per source file, and put that mutant count into the
step 1 estimate. If it points at a run nobody will sit through, narrow the
scope: the files changed against the main branch, or one module. A finished run
on a small scope beats an abandoned run on the whole repo.

**Done when:** you have an explicit include and exclude list, and a rough
estimate of how long the run will take.

## 3. Pick and configure the runner

Prefer the tool the project already has. Otherwise pick by language:

| Language | Tool |
| --- | --- |
| JavaScript / TypeScript | Stryker (`@stryker-mutator/core`) |
| C# / .NET | Stryker.NET (`dotnet-stryker`) |
| Java / Kotlin | PIT (`pitest`) |
| Python | `mutmut`, `cosmic-ray` |
| Go | `gremlins`, `go-mutesting` |
| Rust | `cargo-mutants` |
| PHP | `infection` |
| Ruby | `mutant` |
| Swift | `muter` |
| Elixir | `muzak` |

Read the tool's own documentation for its current configuration schema. Flag
names and file formats drift between versions, and a config written from memory
fails in ways that look like broken code.

Set five things: the include and exclude lists from step 2, the test command
from step 1, a per-mutant timeout (baseline runtime plus a margin), parallelism
(leave a core free), and a machine-readable report file — JSON or XML — next to
whatever HTML the tool produces. You will read the machine-readable one.

Leave the mutation-score threshold switched off for this run. You want the
survivor list, and a threshold that aborts the run hides it. The threshold goes
in at step 9, once you know what the real score is.

Leave the configuration file in the repository, so the next run and the CI run
use the same settings.

**Done when:** the config file exists in the repo, a single-file trial run
completes, and it writes the machine-readable report you asked for.

## 4. Run and capture

Run the full command from step 3. Capture stdout, stderr, the exit code, and the
report file. Long runs belong in the background so you can keep working.

**Done when:** every mutant in scope carries a status, a file, a line, and the
mutation that was applied.

## 5. Triage every mutant

Sort each one:

- **Killed** — a test failed. The behaviour is checked. Nothing owed.
- **Timeout** — the mutant sent the code into a loop. The suite did detect the
  change, so it counts as killed.
- **Survived** — the tests ran over the mutated line and stayed green. A hole.
- **No coverage** — no test reaches the line at all. A bigger hole, and usually
  a faster fix, because one new test kills a whole cluster of these.
- **Build error** — the mutant did not compile, so no test ever ran against it.
  The tool generated invalid code; that is a fact about the tool, not about your
  suite. It leaves the score entirely. Stryker calls this `CompileError`, PIT
  calls it `NON_VIABLE`, and both drop it the same way.
- **Equivalent** — the mutated code behaves the same as the original, so no test
  can ever kill it. Real but rare. It needs a written argument, not a hunch, and
  it leaves the score too.

Compute the mutation score once, and use this formula everywhere — the totals,
the per-file table, and the CI threshold:

> **score = (killed + timeout) ÷ (total − build error − equivalent)**

For every survivor and every no-coverage mutant, read the mutated line and write
one sentence naming the behaviour that goes unchecked — not the mutation, the
behaviour. "Nothing asserts that an order over the limit is rejected" is useful.
"The `>` became `>=`" is a restatement of the diff.

Then label each one:

- **Missing assertion** — the test runs the code but never checks this result.
- **Missing case** — no test supplies the input that reaches this branch.
- **Dead code** — nothing in the product can reach the line. This is a finding
  about the code, not the tests. Raise it with the user; do not write a test to
  reach unreachable code.

Then write the test that would kill it, in words: which test file it goes in,
what the case is called, and the input that reaches the mutated line. On a
report-only run this is what the reader acts on, so keep it concrete. "Add a
test for refunds" is the problem restated, not a suggestion.

**Done when:** every mutant sits in a bucket, the score is computed, and every
survivor and no-coverage mutant carries its one-sentence behaviour statement, a
label, and a suggested test. Equivalents carry their written argument.

## 6. Write the report

Run `date '+%Y-%m-%d-%H%M%S'` for the timestamp and `git rev-parse --short HEAD`
for the commit. Both go in the header. Note a dirty working tree there too,
since the run then covers code that commit does not hold.

Write the report to `<module>/.reports/mutation-report-<timestamp>.md`, where
`<module>` is the root of the module the run covered — the nearest directory at
or above the scope that holds the project's manifest (`package.json`, `go.mod`,
`pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`, a
`*.csproj`). A run spanning several modules writes to the repository root.

Create the folder if it is missing, and keep it out of version control: add
`.reports/` to the repository's root `.gitignore` when nothing there covers it
already. One file per run, and no run ever overwrites an older file.

Use the shape below, and put the data in tables. Every number, path, mutation,
label, and suggested case belongs in a table cell where it can be scanned and
compared. The prose left over is the one-sentence unchecked behaviour, the
equivalence argument, and the short note under a table that says what the
numbers mean. Drop the "After" column and the "Killed this run" section —
nothing has been fixed yet.

Write this report even on a fix run, and write it *before* you touch a test.
This is the before. Without it there is nothing to compare the after against,
and a score you remember is not a score you can show.

Then tell the user the file path, the score, and the most important hole you
found. On a report-only run, say that the report is all this run changed, so
they can ask for the survivors to be killed if they want that next.

**Done when:** the report file sits in the module's `.reports` folder, `.reports/`
is ignored by git, no older report was overwritten, and every survivor and
no-coverage mutant from step 5 appears in it with its behaviour sentence, label,
and suggested test.

## 7. Kill the survivors — on a fix signal

Without the signal, the work is finished at step 6. Hand over the report.

Work one survivor at a time, test first:

1. Write or extend a test that asserts the behaviour you named in step 5.
2. Prove the kill. Edit the source by hand into the mutated form, run the new
   test, and watch it fail. Revert the source.
3. Run the full suite and confirm it is green again.

A test that passes against the hand-applied mutant does not kill it. Step 2 is
the whole point — without that red, you have written a test that agrees with the
bug.

The tests change here; the production code stays as it is. When the only way to
kill a mutant is to change the source, that mutant found a bug or dead code —
write it up as a finding and move on to the next survivor.

Raise the score by killing mutants. A score raised by widening the exclude list,
loosening the operators, or marking an awkward mutant equivalent is a number
that lies to the next reader.

**Done when:** every survivor from step 5 is one of three things — killed by a
new test that was proven red against the hand-applied mutant and green after,
ruled equivalent with its written argument, or deferred with a stated reason.
None are simply unmentioned.

## 8. Re-run and prove — on a fix signal

Run the same command from step 3 again over the same scope.

**Done when:** every mutant you set out to kill in step 7 comes back Killed,
every one still alive is a mutant you deferred there with its reason, the before
and after scores are both recorded, and no mutant that was killed in step 4 has
turned into a survivor.

## 9. Lock it in — on a fix signal

Set the score threshold in the config to the score from the step 8 re-run,
rounded down — the score you just *achieved*, never the one step 6 reported. A
gate left at the before score lets every point of the work slide back without
failing a build, which is the one thing this step exists to stop. That threshold
belongs to the full-scope run, so give it a scheduled or nightly job.

A full-repo mutation run on every pull request is too slow to survive contact
with a team, so run the diff there instead: mutate the changed files and report
the survivors the change introduced. Judge that run on new survivors, not on its
score. A changed-files run mutates a different population of code every time, so
its percentage is not comparable between runs and makes a dishonest gate — one
pull request fails on a module it never touched, the next passes for touching a
well-tested file.

**Done when:** the threshold is in the config file at the score from step 8, and
either the two CI jobs are added or the user has said they do not want them.

## 10. Write the after report — on a fix signal

Take a fresh timestamp and write a second file into the same `.reports` folder.
The step 6 report stays where it is, untouched. Two files, so the move is on
the record and anyone can read the before for themselves.

This one uses the full shape: the "Before" column filled from the step 6 report,
the "After" column from the step 8 re-run, and the "Killed this run" section.

Lead it with a "What moved" section that names the step 6 file, and give each of
these its own table:

- the score before and after, and the point difference;
- which files gained, and which did not move;
- how many survivors were killed, how many are still alive, and how many were
  deferred;
- any mutant that was killed before and is a survivor now. That is a
  regression, and it is the first thing the reader needs.

Then tell the user both file paths, the two scores, and what is still alive.

**Done when:** both report files exist side by side, the after report names the
before file and states the score difference, every survivor from step 6 appears
in it with its outcome, and each killed-this-run entry shows the test that
killed it.

---

# Report shape

The example below is a TypeScript project. The tables, the columns, and the
buckets are what transfers — swap in the tool, the paths, and the status names
your runner actually uses.

````markdown
# Mutation Test Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Tool** | `stryker 8.2.0` |
| **Command** | `<the command you ran>` |
| **Commit** | `<short sha>` (dirty working tree) |
| **Scope** | `src/domain/**` — 12 files |
| **Suite** | 412 passed, 0 failed, 3 skipped · 42s |
| **Duration** | 14m 22s |
| **Before** | [`mutation-report-2026-07-30-091412.md`](./mutation-report-2026-07-30-091412.md) |

## What moved

Against `mutation-report-2026-07-30-091412.md`, taken before any test was
written.

| | Before | After | Change |
| --- | --- | --- | --- |
| **Mutation score** | 69.1% | **92.2%** | **+23.1** |

| Survivor outcome | Survived | No coverage | Total |
| --- | --- | --- | --- |
| 🟢 Killed this run | 29 | 16 | 45 |
| ⏸️ Deferred | 2 | 0 | 2 |
| ⚪ Ruled equivalent | 2 | 0 | 2 |
| 🔧 Raised as a finding | 1 | 0 | 1 |
| 🔴 Still alive | 10 | 3 | 13 |
| **Total before** | **41** | **19** | **60** |

| File | Before | After | Change |
| --- | --- | --- | --- |
| `src/domain/refunds.ts` | 41.9% | 70.0% | +28.1 |
| `src/domain/pricing.ts` | 91.7% | 95.8% | +4.1 |
| `src/domain/tax.ts` | 60.0% | 60.0% | 0.0 |

**Killed before, surviving now:** none.

## Score

`score = (killed + timeout) ÷ (total − build error − equivalent)`

| | Before | After |
| --- | --- | --- |
| **Mutation score** | **69.1%** (134 ÷ 194) | **92.2%** (177 ÷ 192) |

| Status | Before | After | In the score |
| --- | --- | --- | --- |
| 🟢 Killed | 130 | 173 | numerator |
| ⏱️ Timeout | 4 | 4 | numerator |
| 🔴 Survived | 41 | 12 | denominator only |
| ⚫ No coverage | 19 | 3 | denominator only |
| 🔧 Build error | 2 | 2 | excluded |
| ⚪ Equivalent | 0 | 2 | excluded |
| **Total** | **196** | **196** | |

## By file

After the re-run on a fix run; the only numbers there are on a report-only run.
Killed includes timeouts. Excluded is build errors plus equivalents, and comes
off the denominator.

| File | Mutants | Killed | Survived | No coverage | Excluded | Score |
| --- | --- | --- | --- | --- | --- | --- |
| `src/domain/pricing.ts` | 48 | 46 | 2 | 0 | 0 | 95.8% |
| `src/domain/refunds.ts` | 31 | 21 | 6 | 3 | 1 | 70.0% |

---

## 🔴 Still alive

Every survivor on a report-only run; the ones left after the re-run on a fix
run. Each carries a suggested test.

### 1. `src/domain/tax.ts:22` — arithmetic operator

| | |
| --- | --- |
| **Mutation** | `subtotal * rate` → `subtotal / rate` |
| **Label** | missing case |
| **Unchecked behaviour** | every tax test uses a rate of exactly 1.0, so multiplying and dividing give the same answer and no test can tell them apart |
| **Suggested test** | add to `src/domain/tax.test.ts` — any rate other than 1.0 kills this mutant |
| **Outcome** | ⏸️ deferred — needs the multi-rate fixtures landing with the VAT work |

```diff
- const tax = subtotal * rate
+ const tax = subtotal / rate
```

| Case | Input | Expected |
| --- | --- | --- |
| `applies a 20% rate to the subtotal` | `subtotal: 200, rate: 0.2` | `40` |

---

## ⚫ No coverage

| File · line | Mutation | Unchecked behaviour | Suggested test |
| --- | --- | --- | --- |
| `src/domain/refunds.ts:112` | `return true` → `return false` | no test reaches the partial-refund eligibility path at all | `refunds.test.ts` › `allows a partial refund below the amount paid` (paid 100, requested 40) |

---

## 🟢 Killed this run

| File · line | Mutation | Test that kills it |
| --- | --- | --- |
| `src/domain/pricing.ts:84` | `>` → `>=` | `pricing.test.ts › charges shipping at exactly the threshold` |

Each was proven: the new test fails against the hand-applied mutant and passes
against the original.

---

## ⚪ Equivalent mutants

### 1. `src/domain/refunds.ts:40` — `<` → `!=`

| | |
| --- | --- |
| **Mutation** | `i < items.length` → `i != items.length` |
| **Argument** | `i` starts at 0 and increments by 1, so it can only ever reach `items.length` from below. The two conditions are identical for every reachable state, and no test can distinguish them. |
| **Excluded in** | `stryker.config.json` |

```diff
- for (let i = 0; i < items.length; i++) {
+ for (let i = 0; i != items.length; i++) {
```

---

## Findings for the code

| File · line | Finding | Suggested action |
| --- | --- | --- |
| `src/domain/refunds.ts:150` | the `legacyRefund` branch is unreachable — every caller sets `mode` to `standard` or `partial`, so no input reaches it and no test can kill its mutants | delete the branch, or say what should reach it |

---

## The gates

| Gate | Value | Where | State |
| --- | --- | --- | --- |
| `thresholds.break` | 92 | `stryker.config.json` | applied |
| Full-scope run | nightly | `.github/workflows/mutation-nightly.yml` | not applied |
| Pull-request run | changed files only, judged on new survivors | `.github/workflows/ci.yml` | not applied |

The threshold is 92, the score this run *achieved* — 92.2% rounded down — not the
69% it started from. A gate left at the before score lets all 23 points slide back
without failing a build, which is the one thing the ratchet exists to stop. The
pull-request run is judged on new survivors, never on its score.
````

Every mutant appears in exactly one section. Drop any section with no entries.
Keep the score tables, and lead the body with what is still alive.

The before report is the same shape, shorter: no "Before" row, no "What moved",
no "After" column, no "Outcome" rows, and no "Killed this run". Every gate row
reads "not applied".
