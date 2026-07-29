---
name: mutation-test
description: >
  Run mutation testing end to end, kill the surviving mutants, and write a rich
  Markdown report.
disable-model-invocation: true
---

Coverage says a line ran. Mutation testing says a line is **checked**. Break the
code on purpose, one small edit at a time, and a suite worth having goes red.
Each edit is a **mutant**. A mutant the suite fails to notice is a **survivor**,
and every survivor marks a behaviour nobody is testing. This skill ends with
those survivors killed and each kill proven by a re-run.

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
in at step 8, once you know what the real score is.

Commit the configuration file to the repository, so the next run and the CI run
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

**Done when:** every mutant sits in a bucket, the score is computed, and every
survivor and no-coverage mutant carries its one-sentence behaviour statement and
a label. Equivalents carry their written argument.

## 6. Kill the survivors

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

## 7. Re-run and prove

Run the same command from step 3 again over the same scope.

**Done when:** every mutant you set out to kill in step 6 comes back Killed,
every one still alive is a mutant you deferred there with its reason, the before
and after scores are both recorded, and no mutant that was killed in step 4 has
turned into a survivor.

## 8. Lock it in

Set the score threshold in the config to the score you just achieved, so the
full-scope number can only go up. That threshold belongs to the full-scope run —
give it a scheduled or nightly job.

A full-repo mutation run on every pull request is too slow to survive contact
with a team, so run the diff there instead: mutate the changed files and report
the survivors the change introduced. Judge that run on new survivors, not on its
score. A changed-files run mutates a different population of code every time, so
its percentage is not comparable between runs and makes a dishonest gate — one
pull request fails on a module it never touched, the next passes for touching a
well-tested file.

**Done when:** the full-scope threshold is in the committed config, and either
the two CI jobs are added or the user has said they do not want them.

## 9. Write the report

Run `date '+%Y-%m-%d-%H%M%S'` for the timestamp and `git rev-parse --short HEAD`
for the commit. Both go in the header. Note a dirty working tree there too,
since the run then covers code that commit does not hold.

Write the report to `mutation-report-<timestamp>.md`, in the project's reports or
docs directory. One file per run, so two runs can be compared.

When an earlier report sits beside the new one, say what moved: the score, and
which files gained or lost coverage of behaviour.

Use the shape below. Then tell the user the file path, the before and after
scores, and the most important hole you found.

**Done when:** the report file exists, every survivor and no-coverage mutant from
step 5 appears in it with its outcome, and the killed-this-run entries each show
the test that killed them.

---

# Report shape

````markdown
# Mutation Test Report

**Run:** <YYYY-MM-DD HH:MM:SS> · **Tool:** `stryker 8.2.0` ·
**Command:** `<the command you ran>` · **Commit:** `<short sha>` (dirty working tree)
**Scope:** `src/domain/**` (12 files) · **Duration:** 14m 22s

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

## By file — after

Killed includes timeouts. Excluded is build errors plus equivalents, and comes
off the denominator.

| File | Mutants | Killed | Survived | No coverage | Excluded | Score |
| --- | --- | --- | --- | --- | --- | --- |
| `src/domain/pricing.ts` | 48 | 46 | 2 | 0 | 0 | 95.8% |
| `src/domain/refunds.ts` | 31 | 21 | 6 | 3 | 1 | 70.0% |

---

## 🔴 Still alive

Survivors left after the re-run. Each carries a plan.

### `src/domain/tax.ts:22` — arithmetic operator

```diff
- const tax = subtotal * rate
+ const tax = subtotal / rate
```

**Unchecked behaviour:** every tax test uses a rate of exactly 1.0, so
multiplying and dividing give the same answer and no test can tell them apart.

**Label:** missing case · **Plan:** deferred — killing it needs the multi-rate
fixture set, which lands with the VAT work.

---

## ⚫ No coverage

| File · line | Mutation | Unchecked behaviour |
| --- | --- | --- |
| `src/domain/refunds.ts:112` | `return true` → `return false` | no test reaches the partial-refund eligibility path at all |

---

## 🟢 Killed this run

| File · line | Mutation | Test that kills it |
| --- | --- | --- |
| `src/domain/pricing.ts:84` | `>` → `>=` | `pricing.test.ts › charges shipping at exactly the threshold` |

Each was proven: the new test fails against the hand-applied mutant and passes
against the original.

---

## ⚪ Equivalent mutants

### `src/domain/refunds.ts:40` — `<` → `!=`

```diff
- for (let i = 0; i < items.length; i++) {
+ for (let i = 0; i != items.length; i++) {
```

**Argument:** `i` starts at 0 and increments by 1, so it can only ever reach
`items.length` from below. The two conditions are identical for every reachable
state, and no test can distinguish them. Excluded in `stryker.config.json`.

---

## Findings for the code

- `src/domain/refunds.ts:150` — the `legacyRefund` branch is unreachable: every
  caller sets `mode` to `standard` or `partial`. No test can kill its mutants
  because no input reaches it. Delete the branch, or tell us what should reach it.
````

Every mutant appears in exactly one section. Drop any section with no entries.
Keep the score tables, and lead the body with what is still alive.
