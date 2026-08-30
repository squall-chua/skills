---
name: crap-test
description: >
  Score every function with the CRAP metric — cyclomatic complexity crossed with test
  coverage — by generating one script that computes it, proving the script on fixed
  vectors, and reporting each failing function with the exact coverage it needs to pass.
disable-model-invocation: true
---

CRAP — Change Risk Anti-Patterns — asks one question: if I have to change this function, how
likely am I to break it quietly? Complexity is how many ways it can go wrong, coverage is how
many of those a test is watching, and the metric crosses them:

```
CRAP(f) = complexity(f)² × (1 − coverage(f))³ + complexity(f)
```

The cube is the point. Complexity alone is a scold you learn to ignore; coverage alone is a
number you can raise without asserting anything.

**The run is a replay.** Every number comes out of one script this skill writes, run over two
machine-readable files. The script, both inputs, and the CSV go on disk beside the report — a
table nobody can re-run is an opinion with decimal places.

**The rank is the score.** Functions are ordered by CRAP descending and nothing else. No
bumping a payment function up the list; that judgement is `code-coverage`'s job, on purpose.

Steps 1 to 7 measure and write up, and no source or test file is edited. Steps 8 and 9 run
only on a **fix signal** — "fix the CRAP", "bring these down", "go ahead". The step 7 report
is the *before*, so it is written on a fix run too, before anything is touched.

## The thresholds are fixed

| CRAP | Band | Meaning |
| --- | --- | --- |
| ≤ 30 | 🟢 pass | the standard threshold, unchanged |
| > 30, complexity ≤ 30 | 🟠 test it | tests alone can bring it under |
| complexity ≥ 31 | 🔴 split it | fails at **100%** coverage — 31² × 0 + 31 = 31 |

Two facts fall out of the formula and decide every action below:

- **Complexity ≤ 5 always passes** — at zero coverage, 5² + 5 = 30. Those are never findings.
- **Complexity ≥ 31 always fails** — the `+ complexity` tail sits above 30 on its own. No test
  can save it; only splitting can.

Between them the coverage needed to pass is exact, rounded **up** — a target rounded down
still fails when it is hit:

```
required coverage = 1 − ∛((30 − complexity) / complexity²)
```

| Complexity | 6 | 8 | 10 | 12 | 15 | 20 | 25 | 29 | 30 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Needs** | 12.7% | 30.0% | 41.6% | 50.0% | 59.5% | 70.8% | 80.0% | 89.5% | 100% |

That number is the finding. "Add tests for `applyDiscount`" is a wish; "at 34%, needs 50.0%"
is a target somebody can hit.

## 1. Fix the scope, the commit, and the report folder

Record the paths in scope, `git rev-parse --short HEAD`, and whether the tree is dirty.

Settle where everything lands now, because every later step writes there. The report folder is
`<module>/.reports/`, where `<module>` is the nearest directory at or above the scope holding
the project's manifest (`package.json`, `go.mod`, `pyproject.toml`, `pom.xml`, `Cargo.toml`,
`composer.json`, `Gemfile`, `*.csproj`); a run spanning several uses the repository root.
Create it if missing, and add `.reports/` to the root `.gitignore` if nothing there covers it.

Run the suite with coverage off first. It must be green: a failing suite stops early and
leaves whole files unexecuted, and every function in them then scores as untested when it is
only unrun. Skipped tests do the same quietly.

**Done when:** the suite is green on the named scope; the commit, dirty flag, suite counts, and
scope paths are written down; and the report folder exists and is git-ignored.

## 2. Get the two machine files

Some tools ship the metric already — PHPUnit's Clover XML carries `crap`, `complexity`, and
`coverage` per `<method>`, as does any Clover-format report. Take a published value; never
recompute one.

**Look in the report folder before you generate the coverage half.** `/code-coverage` leaves
its machine-readable file there under its own timestamp — `coverage-<timestamp>.lcov`,
`.info`, `.out`, `.xml`, `.json`.

The data file carries no commit of its own. Its commit is in the header of the
`coverage-report-<timestamp>.md` that shares its timestamp — that shared timestamp is the only
thing pairing the two, so read the report to find the commit, and treat a data file with no
matching report as unusable rather than guessing its age. Then check it is still evidence
against the commit from step 1:

```sh
git diff --stat <the coverage report's commit>..HEAD -- <scope>
```

Same commit, or no file in scope changed since — reuse it, and say so in the report header
beside the file and its date. Anything in scope changed since, or the commit is unknown to
this repo — generate a fresh one and say that instead. Re-running a whole suite with coverage
on to rebuild a file that already exists is the most expensive mistake available in this
skill, and on a large suite it is the expensive half of both runs done twice.

Reuse decides only where the numbers come from. The reconciliation in step 5 runs the same
either way, because a reused file can still miss functions the complexity file has.

Otherwise both inputs must be per function. **Complexity** needs a name, file, start line, end
line, and cyclomatic number. **Coverage** needs per-line or per-region hits, or per-method
counters. Read [`joins.md`](joins.md) for the command, the field, and the join key per
language — the universal `lizard` + `lcov` path, the better per-language pairs, and the one
language where a single file holds both.

Install nothing without asking. Look first in the manifest, the lockfile, the CI workflows,
and on `PATH`; where the project has neither tool, put the tool, the install command, and the
download size to the user in one message and wait.

Write down every exclusion and its reason — test files, generated code, vendored code,
migrations. An exclusion nobody can justify moves the score and hides a function.

**Done when:** both files exist in the report folder covering the whole scope, the coverage
file is recorded as reused or generated with the reason, and every exclusion is written down
with its reason.

## 3. Write the script

One file, stdlib only — Python 3 unless the repo has no Python, then Node. Two paths in, CSV
to stdout. No network, no dependency, no config.

Pin all six of these, because each is a place two honest runs could otherwise disagree:

| Decision | The rule |
| --- | --- |
| **Join key** | file path plus declaration line, normalised to repo-relative POSIX paths. Names are not unique — overloads and closures share them |
| **Nested functions** | a function's line set excludes the ranges nested inside it, so an inner closure is never counted twice |
| **In coverage, no lines hit** | coverage 0% — measured, never ran |
| **File absent from coverage** | **unmeasured**: its own list, no score. Scoring it zero invents a number |
| **Zero statements in range** | dropped, and counted in the reconciliation |
| **Rounding and order** | CRAP one decimal half up; required coverage one decimal always up; sort CRAP desc, complexity desc, path, line |

Columns, in this order: `file,function,start_line,end_line,complexity,covered,total,
coverage_pct,crap,band,required_coverage_pct`.

Roll-ups are **max and count, never mean** — one function at 900 disappears behind nine at 2.

**Done when:** the script is one file with no third-party import, takes both paths as
arguments, prints those columns, and holds all six rules.

## 4. Prove the script before it touches the repo

A wrong formula does not crash. It prints a full, plausible, wrong table. So the script
asserts these vectors before it opens either input file:

| Complexity | 1 | 1 | 5 | 10 | 10 | 10 | 20 | 30 | 31 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Coverage** | 100% | 0% | 0% | 100% | 50% | 0% | 80% | 100% | 100% |
| **CRAP** | 1.0 | 2.0 | 30.0 | 10.0 | 22.5 | 110.0 | 23.2 | 30.0 | 31.0 |

Plus three for the required-coverage function: complexity 12 → 50.0%, 25 → 80.0%, 31 → no
answer, it returns "split".

**Done when:** all twelve pass, and the assert block stays in the file so the next run proves
it again.

## 5. Run it and reconcile

An unnoticed join failure is the one bug that makes this report lie while looking complete.
Account for every function on both sides:

- functions in the complexity file;
- of those, matched to coverage;
- of those, unmeasured — their file never appeared in the coverage report;
- of those, unmatched — the file was measured, the declaration line found no lines;
- functions in the coverage file with no complexity row.

A match rate below 95% means the join key is wrong, not that the code is strange. Off-by-one
on the declaration line is the usual cause: some tools point at the signature, others at the
first statement. Fix it in step 3 before reading a single score.

**Done when:** the five counts sum correctly, the match rate is at or above 95% or the join
was fixed, and the CSV sits beside the two input files.

## 6. Bucket and compute the target

Straight from the CSV, no judgement:

- 🔴 **Split** — complexity ≥ 31. Target: parts at complexity ≤ 5 pass at any coverage;
  anything larger carries its own required coverage from the table.
- 🟠 **Test** — CRAP > 30, complexity ≤ 30. Record current coverage, required coverage, and
  the gap in points.
- 🟡 **Watch** — CRAP 20 to 30. Passing with no headroom: one new branch pushes it over.
- 🟢 **Pass** — the rest. Counted, not listed.

Then read the code for 🔴 and 🟠 only, and add one sentence on what each function decides. It
does not move anything up or down — the score set the order. It tells the reader what they are
being asked to test.

**Done when:** every scored function sits in exactly one band, every 🟠 row carries its
required coverage and gap, every 🔴 row carries a split target, and the unmeasured list is
counted separately from all four bands.

## 7. Write the report

Header: the timestamp from `date '+%Y-%m-%d-%H%M%S'`, the commit, and a dirty-tree note — the
run then covers code that commit does not hold.

Write to `crap-report-<timestamp>.md` in the step 1 report folder — one file per run, never
overwriting an older one.

The script, both inputs, and the CSV are already in that folder from steps 2 and 3; give them
the same timestamp, and name all four in the report. A coverage file **reused** from
`/code-coverage` keeps its own earlier timestamp — do not copy or rename it. Link it where it
lies and say it was reused, so a reader can see the two runs shared one measurement rather
than disagreeing about one. Use the tables in [`report.md`](report.md) — every section of that shape, in
that order. Then tell the user the path, the count over 30, the worst
function with its score, and whether it needs tests or splitting.

**Done when:** the report sits beside its script, inputs, and CSV; `.reports/` is git-ignored;
no older report was overwritten; and it holds every 🔴 and 🟠 row, the reconciliation counts,
the unmeasured list, and the exclusions with reasons.

## 8. Bring them down — on a fix signal

Without the signal the work finished at step 7. Work 🔴 first, then 🟠 by score, one function
at a time, suite green after each:

- 🔴 **Split.** Extract branches into named functions until no part is above the step 6 target.
  Extraction only, no behaviour change. The metric improves because the code is genuinely
  simpler, and each part is now small enough for a test to reach.
- 🟠 **Test.** Test the branches, not the lines. Coverage bought by a test with no assertion
  moves this number and changes nothing about the risk — `mutation-test` catches those.

Where a branch cannot be reached by any input, the metric found dead code. Write it up as a
finding; never write a test to reach code the product cannot.

**Done when:** every 🔴 and 🟠 function is under 30 with the suite green, raised as a finding,
or deferred with a stated reason. None are simply unmentioned.

## 9. Write the after report — on a fix signal

Re-run the step 5 command with the **same script** over freshly regenerated inputs: a changed
script and a changed number cannot be told apart.

Fresh timestamp, second file in the same folder, the step 7 report untouched. Lead with "What
moved" — the count over 30 before and after, every function that crossed the threshold with
both scores, and any function whose CRAP **rose**, which is a regression and the first thing
the reader needs.

Then the gate: the count of functions over 30 you have **now**, as a ceiling that can only
fall, plus a check on the CRAP of **changed functions** only. A whole-repo ceiling is a
dishonest gate — deleting a bad function passes the build while a pull request fails for
functions it never touched.

**Done when:** both reports sit side by side, the after report names the before file and states
the differences, the gate is set from the after number, and every 🔴 and 🟠 function from step
7 appears with its outcome.
