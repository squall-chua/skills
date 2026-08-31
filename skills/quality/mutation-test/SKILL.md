---
name: mutation-test
description: >
  Break the source on purpose, find the mutants the tests fail to catch, and
  report each survivor with the behaviour nobody is checking.
disable-model-invocation: true
---

Coverage says a line ran. Mutation testing says a line is **checked**. Break the code on
purpose, one small edit at a time, and a suite worth having goes red. Each edit is a
**mutant**; a mutant the suite fails to notice is a **survivor**, and every survivor marks
a behaviour nobody is testing. This skill ends with every survivor named and the missing
behaviour written down.

## This skill reports

Steps 1 to 6 run the mutants and write up what survived. The tests stay exactly as they
are. That report is the whole deliverable.

Steps 7 to 10 run only on a **fix signal**: "kill them", "fix it", "write the tests", "go
ahead". The step 6 report is the *before*, so it is written on a fix run too, and written
before any test is touched.

## 1. Take the baseline

Run the project's suite on an unmodified tree. It must be green: a red or flaky test
poisons every verdict that follows, because the tool cannot tell a mutant it caught from a
test that was already broken.

Record the wall-clock runtime. The mutation run costs roughly that runtime × the mutant
count ÷ the parallelism, so this number sets your expectations for step 2.

**Done when:** the suite is green on a clean tree, and you have written down its command,
its pass count, and its runtime.

## 2. Scope the run

Mutate the code that holds decisions — business rules, calculations, guards, state changes.
Leave out test files, generated code, vendored dependencies, migrations, and plain
configuration.

Reckon on tens of mutants per source file, and put that count into the step 1 estimate.

**Where the user named no paths, mutate the files changed against the default branch.** This
is the one dimension whose cost scales with the scope you hand it — tens of mutants per file,
each one a full suite run — so a whole-repo default is what turns this skill into an afternoon
nobody spends. Discover the branch, because a repo may use `master` or `develop` and
`origin/HEAD` is often absent:

```sh
base=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)
if [ -z "$base" ]; then
  for c in origin/main origin/master origin/develop main master; do
    git rev-parse --verify --quiet "$c" >/dev/null && base=$c && break
  done
fi
[ -n "$base" ] && git diff --name-only "$base"...HEAD
```

The three-dot form already diffs from the merge base, so a separate `git merge-base` call is
dead work. Two empties mean different things and neither is "nothing changed":

- **An empty `$base`** is no branch to compare against — no `origin`, or a remote named
  something else. Say so and ask for the scope, because a silent empty list reads as "nothing
  to mutate".
- **An empty diff against a good base** is almost never a branch with no work. It is somebody
  typing this skill's name on `main` after an afternoon's editing, so look in the working tree
  before you conclude anything: `git diff --name-only HEAD` for tracked edits and
  `git status --porcelain` for untracked files. Still empty after both, ask for a module.

**Then intersect the list with the include and exclude rules above**, and drop deleted paths
with `--diff-filter=d`. A branch that renames a file puts a path the runner cannot open into
the scope, and a branch that is mostly new tests hands the mutator its own test files.

Say in the report that the scope was your choice and what it left out. A score on the diff is
a statement about this branch's code, never about the suite as a whole, and step 6 has to read
that way.

**Most runners take a scope natively, and they do not all take the same thing:**

| Runner | Flag | Takes |
| --- | --- | --- |
| `mutmut` | `--paths-to-mutate` | source paths — pass the list |
| Stryker | `--mutate` | source globs — pass the list |
| `pitest` | `--targetClasses` | fully-qualified class globs, so changed `.java` paths need mapping to class names first |
| `cargo-mutants` | `--in-diff <file>` | a diff **file**, and it restricts to changed *lines* — write one first with `git diff "$base"...HEAD > changed.diff` |

The last two are the ones that fail if you hand them a path list.

A finished run on a small scope beats an abandoned run on the whole repo. Where the user did
name paths, those are the scope exactly as given, however long it takes.

**Done when:** you have an explicit include and exclude list, a rough estimate of how long the
run will take, and — where the scope came from the diff rather than the user — that fact
written down with what it left out.

## 3. Pick and configure the runner

Prefer the tool the project already has. Otherwise:

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

### Nothing installed?

Look before you install: the manifest and its lockfile, the CI workflows, the project's own
config files, and the binary on `PATH`. A tool declared in the manifest but missing from the
environment needs the project's own install command, not a new dependency.

Where the project genuinely has none, put the setup to the user in one message — the tool and
why it fits this project, the exact install command, the config file with its contents, the
command this skill will then run, and what it costs in download size and first-run time — and
wait for the go-ahead. A new dependency changes the manifest and the lockfile, which is the
user's call. Then install exactly that, leave the config in the repo, and commit nothing.

Read the tool's own docs for its current config schema — flag names and file formats drift
between versions, and a config written from memory fails in ways that look like broken code.

Set five things: the include and exclude lists from step 2, the test command from step 1, a
per-mutant timeout (baseline runtime plus a margin), parallelism (leave a core free), and a
machine-readable report file — JSON or XML — next to whatever HTML the tool produces. You
read the machine-readable one.

Leave the mutation-score threshold **off** for this run. You want the survivor list, and a
threshold that aborts the run hides it. The threshold goes in at step 9, once you know the
real score.

Leave the config file in the repo, so the next run and CI use the same settings.

**Done when:** the tool was already present or the user approved its setup, the config file
exists in the repo, a single-file trial run completes, and it writes the machine-readable
report you asked for.

## 4. Run and capture

Run the full command from step 3. Capture stdout, stderr, the exit code, and the report
file. Long runs belong in the background so you can keep working.

**Done when:** every mutant in scope carries a status, a file, a line, and the mutation that
was applied.

## 5. Triage every mutant

- **Killed** — a test failed. The behaviour is checked. Nothing owed.
- **Timeout** — the mutant sent the code into a loop. The suite did detect the change, so it
  counts as killed.
- **Survived** — the tests ran over the mutated line and stayed green. A hole.
- **No coverage** — no test reaches the line at all. A bigger hole, and usually a faster
  fix, because one new test kills a whole cluster of these.
- **Build error** — the mutant did not compile, so no test ever ran against it. A fact about
  the tool, not your suite, and it leaves the score entirely. Stryker calls this
  `CompileError`, PIT calls it `NON_VIABLE`; both drop it the same way.
- **Equivalent** — the mutated code behaves the same as the original, so no test can ever
  kill it. Real but rare. Needs a written argument, not a hunch, and it leaves the score too.

Compute the score once, and use this formula everywhere — totals, per-file table, CI
threshold:

> **score = (killed + timeout) ÷ (total − build error − equivalent)**

For every survivor and no-coverage mutant, read the mutated line and write one sentence
naming the behaviour that goes unchecked — not the mutation, the behaviour. "Nothing asserts
that an order over the limit is rejected" is useful; "the `>` became `>=`" restates the diff.

Then label each one:

- **Missing assertion** — the test runs the code but never checks this result.
- **Missing case** — no test supplies the input that reaches this branch.
- **Dead code** — nothing in the product can reach the line. A finding about the code, not
  the tests. Raise it with the user; do not write a test to reach unreachable code.

Then write the test that would kill it, in words: which test file, what the case is called,
and the input that reaches the mutated line. On a report-only run this is what the reader
acts on, so keep it concrete. "Add a test for refunds" is the problem restated.

**Done when:** every mutant sits in a bucket, the score is computed, every survivor and
no-coverage mutant carries its one-sentence behaviour statement, a label, and a suggested
test, and every equivalent carries its written argument.

## 6. Write the report

Header: the timestamp from `date '+%Y-%m-%d-%H%M%S'`, the commit from `git rev-parse --short
HEAD`, and a note if the working tree is dirty — the run then covers code that commit does
not hold.

Write to `<module>/.reports/mutation-report-<timestamp>.md`. `<module>` is the nearest
directory at or above the scope holding the project's manifest (`package.json`, `go.mod`,
`pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`, `*.csproj`); a run
spanning several writes to the repository root. Create the folder if missing, add
`.reports/` to the root `.gitignore` if nothing there covers it, one file per run, never
overwrite an older one.

Write this report on a fix run too, and *before* you touch a test. This is the before;
without it there is nothing to compare against, and a score you remember is not a score you
can show.

Use the shape below and put the data in tables — every number, path, mutation, label, and
suggested case belongs in a cell. The prose left over is the one-sentence unchecked
behaviour, the equivalence argument, and a short note under a table saying what the numbers
mean. Drop the "After" column and the "Killed this run" section; nothing has been fixed yet.

Then tell the user the file path, the score, and the most important hole you found. On a
report-only run, say the report is all this run changed, so they can ask for the survivors to
be killed next.

**Done when:** the report sits in the module's `.reports` folder, `.reports/` is git-ignored,
no older report was overwritten, and every survivor and no-coverage mutant from step 5
appears with its behaviour sentence, label, and suggested test.

## 7. Kill the survivors — on a fix signal

Without the signal the work finished at step 6. Work one survivor at a time, test first:

1. Write or extend a test that asserts the behaviour you named in step 5.
2. **Prove the kill.** Edit the source by hand into the mutated form, run the new test, and
   watch it fail. Revert the source.
3. Run the full suite and confirm it is green again.

Step 2 is the whole point. A test that passes against the hand-applied mutant does not kill
it — without that red, you have written a test that agrees with the bug.

The tests change here; the production code stays as it is. Where the only way to kill a
mutant is to change the source, that mutant found a bug or dead code — write it up as a
finding and move on.

Raise the score by killing mutants. A score raised by widening the exclude list, loosening
the operators, or marking an awkward mutant equivalent is a number that lies to the next
reader.

**Done when:** every survivor from step 5 is one of three things — killed by a new test
proven red against the hand-applied mutant and green after, ruled equivalent with its written
argument, or deferred with a stated reason. None are simply unmentioned.

## 8. Re-run and prove — on a fix signal

Run the same command from step 3 again over the same scope.

**Done when:** every mutant you set out to kill comes back Killed, every one still alive is
one you deferred with its reason, both scores are recorded, and no mutant killed in step 4
has turned into a survivor.

## 9. Lock it in — on a fix signal

Set the threshold in the config to the score from the step 8 re-run, rounded down — the score
you just *achieved*, never the one step 6 reported. A gate left at the before score lets
every point of the work slide back without failing a build, which is the one thing this step
exists to stop. That threshold belongs to the full-scope run, so give it a scheduled or
nightly job.

A full-repo mutation run on every pull request is too slow to survive contact with a team, so
run the diff there: mutate the changed files and report the survivors the change introduced.
Judge that run on **new survivors**, not on its score — a changed-files run mutates a
different population every time, so its percentage is not comparable between runs and makes a
dishonest gate, where one pull request fails on a module it never touched and the next passes
for touching a well-tested file.

**Done when:** the threshold is in the config at the step 8 score, and either the two CI jobs
are added or the user has said they do not want them.

## 10. Write the after report — on a fix signal

Fresh timestamp, second file in the same `.reports` folder; the step 6 report stays untouched,
so anyone can read the before for themselves.

This one uses the full shape: the "Before" column filled from the step 6 report, the "After"
column from the step 8 re-run, and the "Killed this run" section.

Lead with a "What moved" section naming the step 6 file, and give each of these its own table:

- the score before and after, and the point difference;
- which files gained and which did not move;
- how many survivors were killed, are still alive, and were deferred;
- any mutant killed before and surviving now. That is a regression, and the first thing the
  reader needs.

Then tell the user both file paths, the two scores, and what is still alive.

**Done when:** both reports sit side by side, the after report names the before file and states
the score difference, every survivor from step 6 appears with its outcome, and each
killed-this-run entry shows the test that killed it.

---

# Report shape

A TypeScript after-report. The tables, columns, and buckets are what transfers — swap in
your own tool, paths, and status names. Every table here is shown with one data row; a real
report lists them all.

````markdown
# Mutation Test Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Tool** | `stryker 8.2.0` |
| **Command** | `<the command you ran>` |
| **Commit** | `<short sha>` (dirty working tree) |
| **Scope** | `src/domain/**` — 12 files, changed against `origin/main` |
| **Suite** | 412 passed, 0 failed, 3 skipped · 42s |
| **Duration** | 14m 22s |
| **Before** | [`mutation-report-2026-07-30-091412.md`](./mutation-report-2026-07-30-091412.md) |

## What moved

Against the before report, taken before any test was written.

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

Files gained: `src/domain/refunds.ts` 41.9% → 70.0%. Did not move: `src/domain/tax.ts`,
60.0%. **Killed before, surviving now:** none.

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

After the re-run on a fix run; the only numbers there are on a report-only run. Killed
includes timeouts. Excluded is build errors plus equivalents, and comes off the denominator.

| File | Mutants | Killed | Survived | No coverage | Excluded | Score |
| --- | --- | --- | --- | --- | --- | --- |
| `src/domain/refunds.ts` | 31 | 21 | 6 | 3 | 1 | 70.0% |

---

## 🔴 Still alive

Every survivor on a report-only run; the ones left after the re-run on a fix run.

### 1. `src/domain/tax.ts:22` — arithmetic operator

| | |
| --- | --- |
| **Mutation** | `subtotal * rate` → `subtotal / rate` |
| **Label** | missing case |
| **Unchecked behaviour** | every tax test uses a rate of exactly 1.0, so multiplying and dividing give the same answer and no test can tell them apart |
| **Suggested test** | add to `src/domain/tax.test.ts` — any rate other than 1.0 kills this mutant |
| **Outcome** | ⏸️ deferred — needs the multi-rate fixtures landing with the VAT work |

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

Each was proven: the new test fails against the hand-applied mutant and passes against the
original.

---

## ⚪ Equivalent mutants

### 1. `src/domain/refunds.ts:40` — `<` → `!=`

| | |
| --- | --- |
| **Mutation** | `i < items.length` → `i != items.length` |
| **Argument** | `i` starts at 0 and increments by 1, so it can only reach `items.length` from below. The two conditions are identical for every reachable state, and no test can distinguish them. |
| **Excluded in** | `stryker.config.json` |

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

The threshold is 92, the score this run *achieved* — 92.2% rounded down — not the 69% it
started from.
````

Every mutant appears in exactly one section. Drop any empty section, keep the score tables,
and lead the body with what is still alive.

The before report is the same shape, shorter: no "Before" row, no "What moved", no "After"
column, no "Outcome" rows, no "Killed this run", and every gate row reading "not applied".
