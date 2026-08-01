---
name: code-quality
description: >
  The front door to the ten test dimensions: read whichever reports are on disk, say
  which dimensions this project should cover, cross-read them, and give one graded verdict
  on the code's quality.
disable-model-invocation: true
---

Ten dimensions, each named for what it measures rather than the tool that measured it:

| Dimension | The question it answers | Measured against | Filled by |
| --- | --- | --- | --- |
| **Verified behaviour** | how much of the code runs under test | the suite | `/code-coverage` |
| **Test strength** | would the tests catch a bug, or only run past it | the suite | `/mutation-test` |
| **Specified behaviour** | does the written spec hold | the suite | `/to-bdd`, `/wire-bdd`, `/run-bdd` |
| **Promised behaviour** | does the deployed API keep the contract it publishes | the running system | `/contract-test` |
| **Proven seams** | does the code work against the real database, broker, and stores | the suite, against real collaborators | `/integration-test` |
| **Resilience** | does it survive those same dependencies failing, and come back | the running system | `/fault-injection-test` |
| **Headroom** | how much load it takes before it stops keeping up | the running system | `/stress-test` |
| **Access** | can everyone operate the interface, keyboard and screen reader included | the running system | `/visual-accessibility` |
| **Exposure** | what can an attacker reach | the code, and the running system | `/security-compliance` |
| **Construction** | what is wrong with the code as written | the code | `/static-analysis` |

That third column is the one people skip, and it decides more than the project's shape does.
Five are answered by a codebase and its suite, four need a system that is actually running, and
exposure needs both.

Each alone is easy to misread — 90% coverage looks like health until the mutation score says
the tests assert nothing. This skill reads them together and gives one verdict. On a repo
with no reports at all it does not stop at "unproven": it works out which dimensions this
project should cover and hands over the command for each.

Three rules hold throughout.

**Relevance comes before measurement.** Grading a project against dimensions it has no
surface for manufactures failures and buries the ones that are real.

**The verdict is a floor, not an average.** A repo sound on nine dimensions and fragile on
the tenth is fragile. Averaging is how a zero disappears.

**Absent evidence is never good news.** A dimension with no report, a skipped one, and a
stale one all read the same: **unproven**.

## 1. Find the reports

Search every `.reports/` folder in the repository. The ten siblings write
`coverage-report-`, `mutation-report-`, `static-analysis-report-`, `bdd-report-`,
`contract-report-`, `integration-report-`, `fault-report-`, `stress-report-`,
`accessibility-report-`, and `security-report-`, timestamped, one file per run, per module.
Take the newest of each kind, per module — on a fix run a sibling writes a before and an after,
and the after is the one that describes the code as it stands.

Set your own past reports aside. `quality-report-*` files are this skill's own output and
they are the **comparison** in step 6, never a dimension. Grading one as evidence pins the
new run to the old floor, so a codebase that has improved keeps reporting last month's grade.

Read anything else in there too. A dependency audit, a benchmark, a type-check log, a
complexity report: each becomes an extra dimension in step 4 rather than a file you
stepped over.

**Done when:** you have every report found with its kind, module, timestamp, and the
commit named in its header; a list of the ten kinds that turned up nothing; and the
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

Every sibling writes "dirty working tree" into its header when the tree was dirty. That note
means the run covered code the commit does not hold, so compare against the working tree
instead: run `git status --porcelain -- <the report's scope>` and rate the report
**Current** when nothing in its scope has been touched since, **Stale** when something has.
A dirty tree alone is not a reason to discard ten reports somebody just generated.

Scope matters as much as age. A coverage report on `src/domain/` says nothing about
`src/http/`, however fresh. Record what each report covered and what it left out.

**Done when:** every report carries a state and its commit distance, every dirty-tree
report was rated against uncommitted changes in its own scope rather than discarded, and
every gap between a report's scope and the code you were asked about is written down.

## 3. Judge relevance, then settle the gaps

Before asking about a gap, decide whether the dimension applies at all. Two questions, and the
scope settles half of them before the project's shape is read at all.

**What is the scope you were asked about?** A repository, a service, or one module. It rules
whole families in or out:

| Measured against | Dimensions | At a module or folder scope |
| --- | --- | --- |
| the code | construction, and the static half of exposure | **applies** — the analyzers take a path |
| the suite | verified behaviour, test strength, specified behaviour, proven seams | **applies** where the suite reaches that path |
| the running system | promised behaviour, resilience, headroom, access, and the live half of exposure | **out of scope** — each is a property of a deployed whole, and no report about one folder can exist |

Say so rather than grading those unproven. An unproven grade reads as work somebody skipped;
this is work nobody could have done at the scope they gave you.

**Then read the project's shape** from its manifest, its entry points, and what it ships:

| The project | Applies | Does not apply |
| --- | --- | --- |
| A library or package | verified behaviour, test strength, exposure, construction | promised behaviour where it serves no API; proven seams where it opens no connection of its own; resilience and headroom, which need a running system to break and to load; access where it renders no interface |
| A CLI or batch job | the same four, plus proven seams and resilience once it touches a database, a queue, or a bucket, plus headroom once throughput is something anybody waits on | promised behaviour, unless it publishes an API; access, which needs something rendered |
| A service with an API | all ten where it serves pages, the other nine where it serves only JSON | access, where nothing renders |
| A service with no published contract | the same — `/contract-test` derives one from the routes | — |
| A front end | the four core, plus promised behaviour against the API it consumes, plus access, plus resilience against that API being down or slow | proven seams, where every collaborator is that one API; headroom, which belongs to the API rather than to the browser |

Then give every dimension one relevance:

- **Applies** — the project has the surface, so an unproven grade here is a real gap.
- **Out of scope** — the surface exists, but not in the slice you were asked about. It leaves
  the counts, and the report names the scope rather than the surface, because widening the
  scope brings the dimension straight back and a missing surface never does.
- **Not applicable** — the project has no such surface. It leaves the counts entirely, and
  the report says which surface is missing so the reader can disagree.
- **By choice** — a practice the team may take or leave rather than a property of the code.
  Specified behaviour is the one: BDD is worth having where requirements are written down and
  worth nothing where they are not. Record the decision and who made it, never a grade.

Where an applicable dimension is unproven, say which kind:

| Why it is unproven | How to tell | What fills it |
| --- | --- | --- |
| **Unmeasured** — the tool was never run on what exists | a test suite runs, or `.feature` files exist, or the dimension needs no suite | running the sibling skill |
| **Untested** — there is nothing for the tool to measure | no test files, no test script in the manifest, no `.feature` files | writing the first tests, which is step 7 |

Check rather than assume: look for test files by the project's own convention, a test script
in the manifest, a test job in CI, and `.feature` files anywhere.

Seven dimensions are never *untested*, because their skills need no existing suite.
`/static-analysis` and `/security-compliance` read the code without running it, so they run
on any project that builds. `/contract-test`, `/visual-accessibility`,
`/fault-injection-test`, and `/stress-test` need a running instance rather than a suite — the
first derives a contract from the routes where the project publishes none, the second drives the
interface in a browser, the third breaks the environment underneath it, and the fourth raises
the load until it stops keeping up. `/integration-test` writes its own
tests and starts its own containers. The other three need a suite first — `/code-coverage` on
a repo with none stops at its own first step for want of a green run.

Then put the gaps to the user in **one** question — ten asked one at a time is an
interrogation, and nobody can weigh the cost of one skip without seeing the others. Give each
its relevance, the command that fills it, and what a skip costs. Every dimension gets a row;
these four show the range of states one can be in:

| Dimension | Relevance | State | To fill it | Skipping it means |
| --- | --- | --- | --- | --- |
| Verified behaviour | applies | no report, suite exists | `/code-coverage` | no idea which code runs under test |
| Test strength | applies | stale, 47 commits behind | `/mutation-test` | the coverage number stays unexamined |
| Specified behaviour | by choice | no `.feature` files | `/to-bdd`, then `/wire-bdd` | nothing, if this team does not write scenarios |
| Promised behaviour | not applicable | ships as a library, serves no API | — | — |

The sibling skills are the user's to run — none fires on its own, so hand over the commands
for the ones they picked and let them type them. Say what each will cost in time; a mutation
run reaches an hour, and a previous report's own duration is the best estimate you have. Then
they call `/code-quality` again with the fresh reports waiting on disk.

An applicable dimension the user skips is **unproven**, exactly like one never run. Record it
with the decision and who made it, so the next reader sees a choice rather than a blank.

**Done when:** the scope is stated and every dimension carries a relevance with the surface,
the scope, or the decision behind it; every applicable unproven one is marked unmeasured or untested and is either backed by a
report you have read or recorded as skipped with the user's decision; and where the user
asked for a signal to be filled they have the exact command.

## 4. Read each dimension

Read each applicable dimension from its report:

| Dimension | Read from |
| --- | --- |
| **Verified behaviour** | coverage report — line %, branch %, files at 0% |
| **Test strength** | mutation report — score, survivors, no-coverage mutants |
| **Specified behaviour** | BDD report — passed, failed, pending, blocked, unwired |
| **Promised behaviour** | contract report — contract coverage, conformance, P1 drift |
| **Proven seams** | integration report — seam coverage, hermetic verdict, unproven seams |
| **Resilience** | fault injection report — hypothesis pass rate, recovery verdict, blast radius per weakness |
| **Headroom** | stress report — the knee, headroom against the expected peak, the soak verdict, what gave first |
| **Access** | accessibility report — criteria coverage, state coverage, P1 barriers |
| **Exposure** | security report — P1 count, reachable CVEs, unrotated secrets, OWASP gaps |
| **Construction** | static analysis report — findings by category, P1 count |

Two of them sound alike and are not. Specified behaviour is the spec the team wrote for
itself, checked from inside. Promised behaviour is the contract the API published to other
people, checked from outside by a caller who cannot see the code.

Grade each. Every band is exhaustive: read top down and take the first that matches, so no
combination of results leaves you inventing a grade.

| Grade | Verified behaviour | Test strength | Specified behaviour | Promised behaviour | Proven seams | Resilience | Headroom | Access | Exposure | Construction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 🔴 **Fragile** | branch < 50%, or any P1 file at 0% | score < 60% | any scenario failing | any P1 breaking drift, or contract coverage < 50% | the hermetic checks failed, or a seam handling money, permissions, or data writes is unproven, or seam coverage < 50% | any experiment that did not recover, or a dependency handling money or data writes that broke outright, or a hypothesis pass rate < 50% | headroom < 1 — it cannot serve today's peak — or the soak run failed, or throughput collapses past the knee | any P1 barrier, or criteria coverage < 50% | any P1 — a reachable flaw, or a secret not yet rotated | P1 bugs in money, permissions, or data writes |
| 🟡 **Thin** | branch 50–69% | score 60–79% | any scenario pending, blocked, or unwired | any P2 divergent drift, or contract coverage 50–79%, or a derived contract | seam coverage 50–79%, or a container version behind production | any unplanned degradation or collateral damage, or a pass rate 50–79%, or a run covering only some of the ranked dependencies | headroom 1–2×, or a shape that did not run, or a closed-model run | any P2 barrier, or criteria coverage 50–79%, or a rules-engine pass with no driven checks | any P2, or a scan kind that did not run, or an OWASP category nothing checked | bugs present |
| 🟢 **Sound** | branch ≥ 70%, no P1 file at 0% | score ≥ 80% | every scenario green | no P1 or P2 drift, contract coverage ≥ 80% | seam coverage ≥ 80%, hermetic passed, no unproven seam in the top rank | pass rate ≥ 80%, every experiment back in band inside its hard stop, no unplanned degradation and no collateral | headroom ≥ 2×, soak passed, all five shapes run under an open model | no P1 or P2 barrier, criteria coverage ≥ 80%, the keyboard and focus checks driven | no P1 or P2, all four scan kinds ran, every OWASP category checked | no bug finding |
| ⚫ **Unproven** | no usable report | no usable report | no usable report | no usable report | no usable report | no usable report | no usable report | no usable report | no usable report | no usable report |

Five results in that table override the numbers beside them, whatever those numbers say:

| Result | What it forces | Why |
| --- | --- | --- |
| A **blocked** scenario | Thin, alongside pending and unwired | all three mean the behaviour was never exercised, and 19 green with 1 blocked is 19 proven and 1 unknown |
| A failed hermetic check | proven seams Fragile | a green that depends on test order, or on data the last run left behind, is evidence of nothing |
| An experiment that never recovered | resilience Fragile | a fault ends; surviving nine of ten counts for nothing against the tenth that needs a human to restart it |
| A **derived** contract | promised behaviour capped at Thin | it was written from the implementation, so the two agree by construction. A reviewed contract lifts the ceiling |
| A **closed-model** run | headroom capped at Thin | the generator stopped sending while the system stalled, so those percentiles describe a system asked to do less exactly when it was struggling |

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
| Green suite, breaking contract drift | the tests check the code against itself and never against the published promise. Consumers are broken while CI stays green |
| High coverage, seams mocked | the covered lines talk to mocks, so the coverage number describes code that has never met a real database |
| Reachable flaw in code with no tests | nothing would catch the fix breaking it, so the flaw is both live and awkward to close |
| Clean static analysis, P1 exposure | the code reads well and something reachable is still open. Tidy code is not safe code |
| Green suite, a P1 access barrier | the tests reach the control by calling it, and a person using a keyboard cannot reach it at all. Covering a control says nothing about operating it |
| Clean rules-engine pass, barriers found by hand | the engine covered the third of WCAG it can see, and the barriers were in the other two thirds |
| Unproven seams in the highest-churn module | the code changing fastest is the code whose collaborators are least tested. Mocks go stale silently, and this is where they are staling |
| Proven seams, resilience unproven | the code works against a real database and nobody has asked what it does when that database refuses a connection. Seam tests prove the crossing, never the loss |
| Green suite, an experiment that never recovered | every test starts from a healthy system and leaves one behind, so nothing in the suite can see a system that does not come back |
| High coverage, a dependency that broke outright | the covered line calls out and waits forever. Coverage counts the call, not the timeout missing from it |
| Thin headroom, unproven resilience | it already runs close to its limit and nobody has asked what a slow dependency does to it. In practice overload and failure arrive together |
| Sound headroom, seams mocked | the load never reached the real database, so the knee measured is the stub's knee rather than the system's |
| High coverage on an operation that drifts | well tested inside, wrong at the boundary. The tests encode what the code does, not what the contract says it does |
| Low contract coverage, high conformance | the clean result covers a fraction of the API. Most of the promise has never been tested at all |
| Files at 0% concentrated in high-churn modules | the code that changes most often is the least verified. This is where the next outage comes from |
| High coverage, high test count, findings all style | the strongest shape available. Say so plainly |
| Every dimension unproven but one | there is no verdict here yet, only one number |

**Done when:** every pair in the table that both its signals support has been checked, and
each one that fires is written up with its two numbers.

## 6. Give the verdict

One verdict for the codebase, by these rules, in this order. A dimension marked **not
applicable**, **out of scope**, or **by choice** in step 3 is outside every count here, so a
library is judged on the four dimensions it has, one module on the six its scope can answer,
and a whole service serving pages on all ten:

1. Two or more applicable dimensions unproven → **Unproven**. One dimension is a number, not
   an assessment.
2. Otherwise the verdict is the **worst** grade any measured dimension carries. Never the
   average, never the majority.
3. State the count beside it, always, out of the number that apply: "Sound, 1 of 7 applicable
   dimensions unproven". Then name what was set aside and why — "1 does not apply: ships as a
   library, serves no API", "4 out of scope: you asked about `src/domain/`, and these describe
   the deployed system, so exposure is graded on its static half alone", "1 by choice: this
   team writes no scenarios" — so the reader sees
   dimensions that were weighed rather than dimensions that were forgotten.

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
named, the unproven count is stated out of the number that apply, everything set aside names
whether it was scope, surface, or choice, and an unproven verdict says whether it is unmeasured
or untested.

## 7. Chart the next moves

A verdict a reader cannot act on is a grade with no lesson attached. Name the starting
position, then order the moves it calls for.

| Starting position | Test |
| --- | --- |
| **Bare** | no tests at all |
| **Thin** | tests exist, and one or more dimensions grade Thin or Fragile |
| **Instrumented** | every applicable dimension measured, none Fragile |

### Which dimensions to cover next

Every recommendation names the dimension, the command that fills it, and what it would tell
you that nothing else does. Order them like this:

1. **Applicable, unproven, and describing something already running.** Exposure, promised
   behaviour, and access describe a system users are hitting today, so what they find is
   already costing somebody something.
2. **Then the ones that unlock others.** A suite before coverage, coverage before mutation.
   Recommending mutation testing to a repo with no suite wastes the reader's week.
3. **By choice, last, and phrased as an offer.** "Worth adopting if the team writes
   requirements down" — never "missing". A practice this team has decided against is not a
   gap in their code.

Then close with one line for each dimension that does not apply and the surface it lacks, so
nobody re-raises it next quarter as an oversight.

### From bare

`/code-coverage` and `/mutation-test` need a suite to measure and `/run-bdd` needs
`.feature` files, so only the seven skills that need no suite run on day one. That makes the
order almost pick itself:

1. **Run `/static-analysis`, then `/security-compliance`.** The cheapest signals there are
   on day one, and between them they find real bugs and reachable flaws in code nobody has
   ever tested. A broken *build* is the only thing that stops the first.
2. **Run `/contract-test` where the project serves an API, `/visual-accessibility` where it
   serves pages, `/stress-test` where somebody already cares about a peak, and
   `/fault-injection-test` where it calls anything it does not own.** All four need a running
   instance and no suite at all. On something with users they find the failures that are
   costing somebody something today. The last two ask the most of you — an environment you are
   allowed to break, and a realistic load — so take them after the first two.
3. **Get one test running.** Any test, on anything, however trivial. The harness is the
   precondition for two more dimensions, and the first test is the only one that costs
   setup. Aim at a runnable suite, not at coverage. On a service with a database or a queue,
   `/integration-test` stands that first suite up, because it writes the harness and starts
   the containers as well as the tests.
4. **Write tests where the risk is, not where the code is easy.** Rank by churn × what the
   code decides — the same ranking `code-coverage` uses, and it works before any coverage
   number exists:
   ```sh
   git log --since='6 months ago' --name-only --format= | grep . | sort | uniq -c | sort -rn | head -20
   ```
   The `grep .` matters: `--name-only` prints a blank line between commits, and without it
   the blank sorts to the top as your busiest file. Cross that list against the code that
   moves money, checks permissions, or writes data. That intersection is the first week of
   work — a short list, not the whole repo.
5. **Then `/code-coverage`.** Once a suite exists the number means something, and it says
   where to go next.
6. **Then `/mutation-test`, on the covered core only.** It has something to bite on now,
   and a small scope keeps the run finishable.
7. **BDD when there are requirements worth pinning.** `/to-bdd` writes the scenarios,
   `/wire-bdd` makes them run. Skip it entirely on a project with no written requirements,
   and record that as a deliberate skip rather than a gap.

Say plainly that this is a body of work, and that the verdict stays Unproven until move 5
lands. A plan presented as a quick fix gets abandoned at the first sprint boundary.

### From thin

One rule decides the order, and it turns on the pair of signals you already have:

| The pair | Go for | Why |
| --- | --- | --- |
| Coverage low, mutation unknown or absent | **breadth** — cover the risky uncovered code first | there is nothing to strengthen yet |
| Coverage high, mutation score low | **strength** — kill survivors in the covered code first | the tests you have do not check what they run, and more of the same makes the number prettier and the suite no better |
| Both middling | **strength** in the P1 modules, breadth everywhere else | risk decides, not the average |

Then order the individual moves across every report by these three, in order:

1. **Exposure findings, and anything already broken.** A committed secret or a live bug
   outranks every measurement, because it is a defect rather than a number about defects.
2. **The dimension that set the floor.** It decided the verdict, so it is what changes the
   verdict.
3. **Highest churn first, inside each.** The code changing fastest breaks soonest.

### From instrumented

The moves are the sibling reports' own P1 lists, merged and ordered by the same three rules.
Add one: recommend the gates each sibling proposed — the coverage ratchet, the mutation
threshold, the analyzer baseline, BDD strict mode, the contract run judged on new drift, the
integration suite in CI, the cheap fault experiments on pull requests, the load smoke and the
regression gate, the four accessibility gates, the four security gates — because an
instrumented codebase with no gate drifts straight back to thin.

**Done when:** the starting position is named, every move is one thing a person can do with
the skill or command that does it, every applicable unproven dimension appears as a
recommendation with what it would tell them, by-choice dimensions read as offers and
not-applicable ones as closed questions, and a bare codebase's plan says it is a body of work
rather than an afternoon.

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
no older report was overwritten, and it holds every section of the shape below, with no
dimension, cross-read pair, or step 7 move left out.

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
| **Starting position** | thin — 9 of 9 applicable dimensions measured, 6 of them Fragile |
| **Bands** | project gates where set, defaults otherwise |
| **Previous** | [`quality-report-2026-07-23-140218.md`](./quality-report-2026-07-23-140218.md) |

## Verdict

# 🔴 Fragile — 0 of 9 applicable dimensions unproven, 1 set aside by choice

The tests reach most of the code and check very little of it: 78% line coverage sits behind
a 61% mutation score, and two survivors are in the refund path. Exposure is the more urgent
half — a signing key is committed in `src/http/session.ts:18` and has not been rotated, and
that outranks everything else on this list.

Last week's verdict was 🟡 Thin. Test strength set the floor then and exposure sets it now,
on a live secret that did not exist in the previous run.

## Dimensions

| Dimension | Relevance | Grade | The numbers | Evidence | Behind HEAD |
| --- | --- | --- | --- | --- | --- |
| Verified behaviour | applies | 🟡 Thin | lines 78.4%, branches 60.8%, 3 files at 0% | [coverage](./coverage-report-2026-07-30-142205.md) | 0 commits |
| Test strength | applies | 🔴 Fragile | score 61.4%, 12 survivors, 3 no-coverage | [mutation](./mutation-report-2026-07-30-091412.md) | 2 commits |
| Specified behaviour | by choice | — | — | none | — |
| Promised behaviour | applies | 🔴 Fragile | conformance 78.1%, contract coverage 80.0%, 3 P1 drift | [contract](./contract-report-2026-07-30-144510.md) | 0 commits |
| Proven seams | applies | 🟡 Thin | seam coverage 66.7%, hermetic passed, 2 seams unproven | [integration](./integration-report-2026-07-30-151133.md) | 1 commit |
| Resilience | applies | 🔴 Fragile | pass rate 81.8%, 1 experiment never recovered | [fault injection](./fault-report-2026-08-01-093044.md) | 0 commits |
| Headroom | applies | 🟡 Thin | knee 290 req/s, headroom 1.6× of a 180 req/s peak, soak passed | [stress](./stress-report-2026-08-01-104530.md) | 0 commits |
| Access | applies | 🔴 Fragile | 3 P1 barriers, criteria coverage 72.0%, 22 of 22 states | [accessibility](./accessibility-report-2026-08-01-141005.md) | 0 commits |
| Exposure | applies | 🔴 Fragile | 4 P1 — 1 unrotated secret, 1 reachable CVE, 2 access control | [security](./security-report-2026-07-31-140203.md) | 0 commits |
| Construction | applies | 🔴 Fragile | 14 bug — 3 in the refund path — 61 risk findings | [static analysis](./static-analysis-report-2026-07-30-153001.md) | 0 commits |

Exposure, construction, test strength, promised behaviour, resilience, and access are jointly
at the floor, so the verdict is 🔴 Fragile.

## What is not graded here

| Dimension | Relevance | Why | Decision |
| --- | --- | --- | --- |
| Specified behaviour | by choice | no `.feature` files and no written requirements to draw them from | the team writes none. Not a gap in the code, and not counted against the verdict |

Had the ask been `src/domain/` rather than the service, promised behaviour, resilience,
headroom, access, and the live half of exposure would sit here too, marked **out of scope**.

## What the signals say together

| The pair | The numbers | What it means |
| --- | --- | --- |
| High coverage, low mutation score | 78.4% covered, 61.4% killed | the tests run the code and check about six lines in ten of it |
| Green suite, breaking contract drift | 412 tests green, `GET /orders/{id}` returns `total` as a string | the suite checks the code against itself. The promise to callers broke and nothing in CI noticed |

## Dimensions to cover next

| Dimension | Relevance | Run | What it would tell you |
| --- | --- | --- | --- |
| Specified behaviour | by choice | `/to-bdd`, then `/wire-bdd` | whether the written requirements hold. Worth adopting if this team starts writing them down; nothing is wrong with the code for lacking it |

**Not applicable here:** none — this service has all ten surfaces. On a library, promised
behaviour, proven seams, resilience, headroom, and access would sit on this line instead.

## The next moves

Thin start, so the pair of signals decides the order. Strength before breadth: coverage is
78% and the mutation score is 61%, so the tests already reach the code and adding more of the
same would move the wrong number.

| # | Do this | Why it is here | Command |
| --- | --- | --- | --- |
| 1 | Rotate the signing key, then remove it from the source | a committed secret is live until the key changes, and git history keeps it | — |
| 2 | Make the order consumer recover on its own, and alert on lag | any broker blip stalls it for good. Checkout keeps returning 200, so orders are accepted and never processed and nothing reports it | `/fault-injection-test` |
````

Drop any empty section, and lead the body with the verdict. The dimension that set the floor
is named in the verdict and appears first among the moves that are not outright defects.

A **bare** codebase's report is the same shape with two differences: the verdict is
"Unproven — untested", and the moves table holds the step 7 ladder in that order rather than
a merge of sibling lists — with move 4 naming the actual high-churn modules and their commit
counts. It closes on the line that the first four moves are a body of work, not an
afternoon, and that the verdict stays Unproven until move 5 lands.
