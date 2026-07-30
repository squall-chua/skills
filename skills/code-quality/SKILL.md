---
name: code-quality
description: >
  Read the coverage, mutation, static analysis, and BDD reports already on disk,
  cross-read them against each other, and give one graded verdict on the code's
  quality.
disable-model-invocation: true
---

Every sibling report answers one question. Coverage says which lines ran, mutation
says whether they are checked, static analysis says what is wrong without running
anything, BDD says whether the specified behaviour holds. Each alone is easy to
misread — 90% coverage looks like health until the mutation score says the tests
assert nothing.

This skill reads them together and gives one verdict, on two rules that hold
throughout.

**The verdict is a floor, not an average.** A repo sound on three dimensions and
fragile on the fourth is fragile. Averaging is how a zero disappears.

**Absent evidence is never good news.** A dimension with no report, a skipped one,
and a stale one all read the same: **unproven**. Silence has never yet meant a suite
was passing.

## 1. Find the reports

Search every `.reports/` folder in the repository. The four siblings write
`coverage-report-`, `mutation-report-`, `static-analysis-report-`, and `bdd-report-`,
timestamped, one file per run, per module. Take the newest of each kind, per module —
on a fix run a sibling writes a before and an after, and the after is the one that
describes the code as it stands.

Set your own past reports aside. `quality-report-*` files are this skill's own output
and they are the **comparison** in step 6, never a dimension. Grading one as evidence
makes the skill read its own verdict back and pin the new run to the old floor, so a
codebase that has genuinely improved would keep reporting last month's grade.

Read anything else in there too. A dependency audit, a benchmark, a type-check log, a
complexity report: each becomes an extra dimension in step 4 rather than a file you
stepped over.

**Done when:** you have every report found with its kind, module, timestamp, and the
commit named in its header; a list of the four kinds that turned up nothing; and the
newest `quality-report-*` held aside as the comparison rather than counted as a
dimension.

## 2. Check each report is still evidence

A report describes the commit in its header, not the commit you are standing on. For
each one:

```sh
git rev-list --count <report commit>..HEAD
git diff --stat <report commit>..HEAD -- <the report's scope>
```

| State | Test | Weight |
| --- | --- | --- |
| **Current** | the report's commit is HEAD, and no file in scope has changed since | full evidence |
| **Near** | commits since, but none touching the report's scope | full evidence |
| **Stale** | files in scope changed since | a lead, not evidence |
| **Unusable** | the commit is unknown to this repo | no evidence |

A working tree is dirty most of the time, and every sibling writes "dirty working
tree" into its header when it is. That note means the run covered code the commit does
not hold, so compare against the working tree instead: run `git status --porcelain --
<the report's scope>` and rate the report **Current** when nothing in its scope has
been touched since, **Stale** when something has. A dirty tree alone is not a reason to
discard four reports somebody just generated.

Scope matters as much as age. A coverage report on `src/domain/` says nothing about
`src/http/`, however fresh. Record what each report covered and what it left out.

**Done when:** every report carries a state and its commit distance, every dirty-tree
report was rated against uncommitted changes in its own scope rather than discarded, and
every gap between a report's scope and the code you were asked about is written down.

## 3. Settle the gaps with the user

A dimension can be unproven for two very different reasons, and the advice for each is
nothing like the other. Find out which first:

| Why it is unproven | How to tell | What fills it |
| --- | --- | --- |
| **Unmeasured** — the tool was never run on what exists | a test suite runs, or `.feature` files exist, or the dimension is Construction | running the sibling skill |
| **Untested** — there is nothing for the tool to measure | no test files, no test script in the manifest, no `.feature` files | writing the first tests, which is step 7 |

Check rather than assume: look for test files by the project's own convention, a test
script in the manifest, a test job in CI, and `.feature` files anywhere.

Construction is never *untested*: `/static-analysis` reads code without running it, so it
is always runnable on a project that builds. The other three need something to exist
first — pointing someone at `/code-coverage` on a repo with no suite wastes their time,
because that skill stops at its own first step for want of a green run.

Then put the unmeasured gaps to the user in **one** question — four questions asked one at
a time is an interrogation, and the user cannot weigh the cost of one skip without seeing
the others. Each gets the command that fills it and what a skip costs:

| Dimension | State | To fill it | Skipping it means |
| --- | --- | --- | --- |
| Verified behaviour | no report, suite exists | `/code-coverage` | no idea which code runs under test |
| Test strength | stale, 47 commits behind | `/mutation-test` | the coverage number stays unexamined |
| Specified behaviour | no `.feature` files | nothing to run — see step 7 | no idea whether the written spec holds |
| Construction | current | — | — |

The sibling skills are the user's to run — none fires on its own, so hand over the commands
for the ones they picked and let them type them. Say what each will cost in time; a mutation
run reaches an hour, and a previous report's own duration is the best estimate you have.
Then they call `/code-quality` again with the fresh reports waiting on disk.

Every dimension the user skips is **unproven**, exactly like one never run. Record it with
the decision and who made it, so the next reader sees a choice rather than a blank.

**Done when:** every unproven dimension is marked unmeasured or untested, every unmeasured
one is either backed by a report you have read or recorded as skipped with the user's
decision beside it, and where the user asked for a signal to be filled they have the exact
command. None are quietly dropped.

## 4. Read each dimension

Four dimensions, each named for what it measures rather than the tool that measured it:

| Dimension | What it measures | Read from |
| --- | --- | --- |
| **Verified behaviour** | how much of the code runs under test | coverage report — line %, branch %, files at 0% |
| **Test strength** | whether the tests would catch a bug | mutation report — score, survivors, no-coverage mutants |
| **Specified behaviour** | whether the written spec holds | BDD report — passed, failed, pending, blocked, unwired |
| **Construction** | what is wrong with the code as written | static analysis report — findings by category, P1 count |

Grade each. Every band is exhaustive: read top down and take the first that matches, so no
combination of results leaves you inventing a grade.

| Grade | Verified behaviour | Test strength | Specified behaviour | Construction |
| --- | --- | --- | --- | --- |
| 🔴 **Fragile** | branch < 50%, or any P1 file at 0% | score < 60% | any scenario failing | any security finding, or P1 bugs in money, permissions, or data writes |
| 🟡 **Thin** | branch 50–69% | score 60–79% | any scenario pending, blocked, or unwired | bugs present, no security finding |
| 🟢 **Sound** | branch ≥ 70%, no P1 file at 0% | score ≥ 80% | every scenario green | no bug or security finding |
| ⚫ **Unproven** | no usable report | no usable report | no usable report | no usable report |

A **blocked** scenario grades Thin alongside pending and unwired, because all three mean
the same thing: the behaviour was never exercised. A suite of 19 green and 1 blocked is 19
proven and 1 unknown, and the grade has to show the unknown.

These bands are a default. Where the project has its own gates — a coverage threshold in
its config, a mutation threshold, a CI rule — those are the project's own standard and they
win. Say in the report which you used.

The direction matters more than the digit. A dimension that fell since the last report is
worth more of the reader's attention than one sitting a point below a band.

**Done when:** every dimension carries a grade and the numbers behind it, and every grade
drawn from a project gate rather than the default band says so.

## 5. Cross-read the signals

This is the step no single report can do, and the reason to read them together. A pair of
signals often says something neither says alone:

| The pair | What it means |
| --- | --- |
| High coverage, low mutation score | the tests run the code and assert almost nothing. The coverage number is decoration |
| High coverage, no mutation report | nothing yet says the coverage means anything |
| Line coverage far above branch coverage | the tests walk the happy path and never turn off it |
| Green scenarios, low branch coverage | the specified behaviour holds and the edges around it are unexamined |
| Clean static analysis, low coverage | tidy code nobody has verified |
| Many findings, high coverage | verified behaviour in decaying construction. It works, and it is getting harder to change |
| Unwired scenarios, green suite | the green tick covers fewer scenarios than the count suggests. Part of the spec never ran |
| Files at 0% concentrated in high-churn modules | the code that changes most often is the least verified. This is where the next outage comes from |
| High coverage, high test count, findings all style | the strongest shape available. Say so plainly |
| Every dimension unproven but one | there is no verdict here yet, only one number |

**Done when:** every pair in the table that both its signals support has been checked, and
each one that fires is written up with its two numbers.

## 6. Give the verdict

One verdict for the codebase, by these rules, in this order:

1. Two or more dimensions unproven → **Unproven**. One dimension is a number, not an
   assessment.
2. Otherwise the verdict is the **worst** grade any measured dimension carries. Never the
   average, never the majority.
3. State the count of unproven dimensions beside it, always. "Sound, 1 of 4 unproven" is an
   honest verdict; "Sound" alone with a dimension missing is not.

Then write the verdict out in two sentences: what the code is, and the one thing that most
needs attention. Lead with the dimension that set the floor, because that is the dimension
that decided the verdict.

An **Unproven** verdict says which kind it is, because the two mean opposite things about
the work ahead. "Unproven — unmeasured" is a codebase with tests nobody has pointed a tool
at, and one afternoon settles it. "Unproven — untested" is a codebase with no tests at all,
and it is a body of work. Never let the first phrasing stand in for the second.

Where a previous quality report sits beside this one, say which way the verdict moved and
which dimension moved it.

**Done when:** the verdict follows the three rules, the dimension that set the floor is
named, the unproven count is stated, and an unproven verdict says whether it is unmeasured
or untested.

## 7. Chart the next moves

A verdict a reader cannot act on is a grade with no lesson attached. Name the starting
position, then order the moves it calls for.

| Starting position | Test |
| --- | --- |
| **Bare** | no tests at all |
| **Thin** | tests exist, and one or more dimensions grade Thin or Fragile |
| **Instrumented** | every dimension measured, none Fragile |

### From bare

`/code-coverage` and `/mutation-test` need a suite to measure and `/run-bdd` needs
`.feature` files, so only `/static-analysis` runs on day one. That makes the order almost
pick itself:

1. **Run `/static-analysis`.** The one signal available on day one, and it finds real bugs
   in code nobody has ever tested. Cheapest first move there is. It reports the missing
   suite as a fact and analyses anyway; a broken *build* is the only thing that stops it.
2. **Get one test running.** Any test, on anything, however trivial. The harness is the
   precondition for two more dimensions, and the first test is the only one that costs
   setup. Aim at a runnable suite, not at coverage.
3. **Write tests where the risk is, not where the code is easy.** Rank by churn × what the
   code decides — the same ranking `code-coverage` uses, and it works before any coverage
   number exists:
   ```sh
   git log --since='6 months ago' --name-only --format= | grep . | sort | uniq -c | sort -rn | head -20
   ```
   The `grep .` matters: `--name-only` prints a blank line between commits, and without it
   the blank sorts to the top as your busiest file. Cross that list against the code that
   moves money, checks permissions, or writes data. That intersection is the first week of
   work — a short list, not the whole repo.
4. **Then `/code-coverage`.** Once a suite exists the number means something, and it says
   where to go next.
5. **Then `/mutation-test`, on the covered core only.** It has something to bite on now,
   and a small scope keeps the run finishable.
6. **BDD when there are requirements worth pinning.** `/to-bdd` writes the scenarios,
   `/wire-bdd` makes them run. Skip it entirely on a project with no written requirements,
   and record that as a deliberate skip rather than a gap.

Say plainly that this is a body of work, and that the verdict stays Unproven until move 4
lands. A plan presented as a quick fix gets abandoned at the first sprint boundary.

### From thin

One rule decides the order, and it turns on the pair of signals you already have:

| The pair | Go for | Why |
| --- | --- | --- |
| Coverage low, mutation unknown or absent | **breadth** — cover the risky uncovered code first | there is nothing to strengthen yet |
| Coverage high, mutation score low | **strength** — kill survivors in the covered code first | the tests you have do not check what they run, and more of the same makes the number prettier and the suite no better |
| Both middling | **strength** in the P1 modules, breadth everywhere else | risk decides, not the average |

Then order the individual moves across every report by these three, in order:

1. **Security findings, and anything already broken.** A committed secret or a live bug
   outranks every measurement, because it is a defect rather than a number about defects.
2. **The dimension that set the floor.** It decided the verdict, so it is what changes the
   verdict.
3. **Highest churn first, inside each.** The code changing fastest breaks soonest.

### From instrumented

The moves are the sibling reports' own P1 lists, merged and ordered by the same three rules.
Add one: recommend the gates each sibling proposed — the coverage ratchet, the mutation
threshold, the analyzer baseline, BDD strict mode — because an instrumented codebase with no
gate drifts straight back to thin.

**Done when:** the starting position is named, every move is one thing a person can do with
the skill or command that does it, the moves are ordered by the rules above, and a bare
codebase's plan says it is a body of work rather than an afternoon.

## 8. Write the report

Header: `date '+%Y-%m-%d-%H%M%S'` for the timestamp, `git rev-parse --short HEAD` for the
commit, and a note if the working tree is dirty.

Write to `<module>/.reports/quality-report-<timestamp>.md`, where `<module>` is the nearest
directory at or above the module assessed holding the project's manifest (`package.json`,
`go.mod`, `pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`, a
`*.csproj`). An assessment spanning several modules writes to the repository root. Create
the folder if missing and add `.reports/` to the root `.gitignore` if nothing there covers
it. One file per run; never overwrite an older one.

Every source report is named and linked, with its commit distance. A verdict whose evidence
a reader cannot open is a verdict they have to take on trust.

Use the shape below and put the data in tables — grades, numbers, states, commit distances,
and next moves belong in cells. The prose left over is the verdict itself and one sentence
per cross-read pair.

Then tell the user the file path, the verdict with its unproven count, and the one next move
at the top of the list.

**Done when:** the report sits in the module's `.reports` folder, `.reports/` is git-ignored,
no older report was overwritten, and it holds every section of the shape below — every
dimension with its grade and evidence link, every cross-read pair that fired, every unproven
dimension marked unmeasured or untested with the user's decision, and the step 7 moves in
order with the command for each.

---

# Report shape

A TypeScript example. The tables, grades, and dimensions are what transfers — swap in your
own tools and paths. Tables are shown with one or two rows; a real report lists them all.

````markdown
# Code Quality Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Commit** | `a1b2c3d` (clean) |
| **Scope** | `src/**` — 84 files |
| **Starting position** | instrumented — 3 of 4 dimensions measured |
| **Bands** | project gates where set, defaults otherwise |
| **Previous** | [`quality-report-2026-07-23-140218.md`](./quality-report-2026-07-23-140218.md) |

## Verdict

# 🔴 Fragile — 1 of 4 dimensions unproven

The tests reach most of the code and check very little of it: 78% line coverage sits behind
a 61% mutation score, and two survivors are in the refund path. Construction is the more
urgent half — a signing key is committed in `src/http/session.ts:18`, and that needs
rotating before anything else on this list.

Last week's verdict was 🟡 Thin. Test strength set the floor then and construction sets it
now, on a security finding that did not exist in the previous run.

## Dimensions

| Dimension | Grade | The numbers | Evidence | Behind HEAD |
| --- | --- | --- | --- | --- |
| Verified behaviour | 🟡 Thin | lines 78.4%, branches 60.8%, 3 files at 0% | [coverage](./coverage-report-2026-07-30-142205.md) | 0 commits |
| Test strength | 🔴 Fragile | score 61.4%, 12 survivors, 3 no-coverage | [mutation](./mutation-report-2026-07-30-091412.md) | 2 commits |
| Specified behaviour | ⚫ Unproven | — | none | — |
| Construction | 🔴 Fragile | 1 security, 14 bug, 61 risk findings | [static analysis](./static-analysis-report-2026-07-30-153001.md) | 0 commits |

Construction and test strength are jointly at the floor, so the verdict is 🔴 Fragile.

## Unproven dimensions

| Dimension | Why | Kind | Decision |
| --- | --- | --- | --- |
| Specified behaviour | no `bdd-report-*` anywhere, and no `.feature` files to run | untested | user chose to skip — this project keeps no written scenarios |

Nothing here says the written spec holds, because there is no written spec to hold. Recorded
so the next reader does not read the blank as a pass.

## What the signals say together

| The pair | The numbers | What it means |
| --- | --- | --- |
| High coverage, low mutation score | 78.4% covered, 61.4% killed | the tests run the code and check about six lines in ten of it |
| Findings concentrated where churn is highest | `refunds/` — 96 findings, 11 commits in 6 months | the code changing fastest is the code least verified. This is where the next outage comes from |

## The next moves

Instrumented start, so these are the sibling P1 lists merged. Strength before breadth:
coverage is 78% and the mutation score is 61%, so the tests already reach the code and
adding more of the same would move the wrong number.

| # | Do this | Why it is here | Command |
| --- | --- | --- | --- |
| 1 | Rotate the signing key, then remove it from the source | a committed secret is live until the key changes, and git history keeps it | — |
| 2 | Fix the 14 bug findings | defects in the code as written, not opinions about it | `/static-analysis` |
| 3 | Kill the 12 mutation survivors, refunds first | the tests around refund money do not check it, and this is the floor dimension | `/mutation-test` |
| 4 | Cover the 3 files at 0% | all three are in `src/domain/refunds`, the highest-churn module | `/code-coverage` |
| 5 | Set the coverage ratchet and the analyzer baseline | both were recommended and neither is applied, so today's numbers can slide back | `/code-coverage`, `/static-analysis` |
| 6 | Decide whether this project wants written scenarios | one dimension stays empty until this is settled either way | `/to-bdd` |
````

Drop any empty section, and lead the body with the verdict. The dimension that set the floor
is named in the verdict and appears first among the moves that are not outright defects.

A **bare** codebase's report is the same shape with two differences: the verdict is
"Unproven — untested", and the moves table holds the step 7 ladder in that order rather than
a merge of sibling lists — with move 3 naming the actual high-churn modules and their commit
counts. It closes on the line that the first three moves are a body of work, not an
afternoon, and that the verdict stays Unproven until move 4 lands.
