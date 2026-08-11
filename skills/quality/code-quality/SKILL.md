---
name: code-quality
description: >
  The front door to the twelve test dimensions: read whichever reports are on disk, say
  which dimensions this project should cover, cross-read them, and give one graded verdict
  on the code's quality.
disable-model-invocation: true
---

Twelve dimensions, each named for what it measures rather than the tool that measured it:

| Dimension | The question it answers | Measured against | Filled by |
| --- | --- | --- | --- |
| **Verified behaviour** | how much of the code runs under test | the suite | `/code-coverage` |
| **Test strength** | would the tests catch a bug, or only run past it | the suite | `/mutation-test` |
| **Change risk** | which functions are dangerous to edit | the code, crossed with the suite | `/crap-test` |
| **Specified behaviour** | does the written spec hold | the suite | `/to-bdd`, `/wire-bdd`, `/run-bdd` |
| **Promised behaviour** | does the deployed API keep the contract it publishes | the running system | `/contract-test` |
| **Proven seams** | does the code work against the real database, broker, and stores | the suite, against real collaborators | `/integration-test` |
| **Resilience** | does it survive those same dependencies failing, and come back | the running system | `/fault-injection-test` |
| **Headroom** | how much load it takes before it stops keeping up | the running system | `/stress-test` |
| **Access** | can everyone operate the interface, keyboard and screen reader included | the running system | `/visual-accessibility` |
| **Exposure** | what can an attacker reach | the code, and the running system | `/security-compliance` |
| **Construction** | what is wrong with the code as written | the code | `/static-analysis` |
| **Single source** | is one piece of knowledge living in several places | the code, crossed with git history | `/dry-test` |

That third column is the one people skip, and it decides more than the project's shape does.
Seven are answered by a codebase and its suite, four need a system that is actually running,
and exposure needs both.

Each alone is easy to misread — 90% coverage looks like health until the mutation score says
the tests assert nothing. This skill reads them together and gives one verdict. On a repo
with no reports at all it does not stop at "unproven": it works out which dimensions this
project should cover and hands over the command for each.

Three rules hold throughout.

**Relevance comes before measurement.** Grading a project against dimensions it has no
surface for manufactures failures and buries the ones that are real.

**The verdict is a floor, not an average.** A repo sound on eleven dimensions and fragile on
the twelfth is fragile. Averaging is how a zero disappears.

**Absent evidence is never good news.** A dimension with no report, a skipped one, and a
stale one all read the same: **unproven**.

## 1. Find the reports

Search every `.reports/` folder in the repository. The twelve siblings write
`coverage-report-`, `mutation-report-`, `crap-report-`, `static-analysis-report-`,
`dry-report-`, `bdd-report-`, `contract-report-`, `integration-report-`, `fault-report-`,
`stress-report-`, `accessibility-report-`, and `security-report-`, timestamped, one file per
run, per module. Take the newest of each kind, per module — on a fix run a sibling writes a
before and an after, and the after is the one that describes the code as it stands.

Set your own past reports aside. `quality-report-*` files are this skill's own output and
they are the **comparison** in step 6, never a dimension. Grading one as evidence pins the
new run to the old floor, so a codebase that has improved keeps reporting last month's grade.

Read anything else in there too. A dependency audit, a benchmark, a type-check log, a
complexity report: each becomes an extra dimension in step 4 rather than a file you
stepped over.

**Done when:** you have every report found with its kind, module, timestamp, and the
commit named in its header; a list of the twelve kinds that turned up nothing; and the
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
A dirty tree alone is not a reason to discard a dozen reports somebody just generated.

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
| the code | construction, single source, and the static half of exposure | **applies** — the analyzers take a path |
| the suite | verified behaviour, test strength, change risk, specified behaviour, proven seams | **applies** where the suite reaches that path |
| the running system | promised behaviour, resilience, headroom, access, and the live half of exposure | **out of scope** — each is a property of a deployed whole, and no report about one folder can exist |

Say so rather than grading those unproven. An unproven grade reads as work somebody skipped;
this is work nobody could have done at the scope they gave you.

Single source is the one dimension a narrow scope weakens rather than rules out. A clone
finder run over one folder cannot see the copy sitting in the next one, so a green result at
module scope means "no duplication inside this folder" and never "no duplication". Say which
you measured.

**Then read the project's shape** from its manifest, its entry points, and what it ships:

| The project | Applies | Does not apply |
| --- | --- | --- |
| A library or package | the six core — verified behaviour, test strength, change risk, single source, exposure, construction | promised behaviour where it serves no API; proven seams where it opens no connection of its own; resilience and headroom, which need a running system to break and to load; access where it renders no interface |
| A CLI or batch job | the same six, plus proven seams and resilience once it touches a database, a queue, or a bucket, plus headroom once throughput is something anybody waits on | promised behaviour, unless it publishes an API; access, which needs something rendered |
| A service with an API | all twelve where it serves pages, the other eleven where it serves only JSON | access, where nothing renders |
| A service with no published contract | the same — `/contract-test` derives one from the routes | — |
| A front end | the six core, plus promised behaviour against the API it consumes, plus access, plus resilience against that API being down or slow | proven seams, where every collaborator is that one API; headroom, which belongs to the API rather than to the browser |

Change risk and single source are in every row's core because both read the code and every
project has code. Neither is ever *not applicable*. Where no suite exists, change risk is
unproven — untested, never dismissed.

Then give every dimension one relevance:

- **Applies** — the project has the surface, so an unproven grade here is a real gap.
- **Out of scope** — the surface exists, but not in the slice you were asked about. It leaves
  the counts, and the report names the scope rather than the surface, because widening the
  scope brings the dimension straight back and a missing surface never does.
- **Not applicable** — the project has no such surface. It leaves the counts entirely, and
  the report says which surface is missing so the reader can disagree.
- **By choice** — a practice the team may take or leave rather than a property of the code.
  Specified behaviour is the one: a team may decide it does not want a written spec. Having
  written no requirements yet is **not** that decision — `/to-bdd` mines a draft from the code
  for exactly that case and the team confirms it. Record the decision and who made it, never a
  grade.

Where an applicable dimension is unproven, say which kind:

| Why it is unproven | How to tell | What fills it |
| --- | --- | --- |
| **Unmeasured** — the tool was never run on what exists | a test suite runs, or `.feature` files exist, or the dimension needs no suite | running the sibling skill |
| **Untested** — there is nothing for the tool to measure | no test files, no test script in the manifest, no `.feature` files | writing the first tests, which is step 7 |

Check rather than assume: look for test files by the project's own convention, a test script
in the manifest, a test job in CI, and `.feature` files anywhere.

Only three dimensions need a suite somebody else wrote — verified behaviour, change risk, and
test strength. `/code-coverage` on a repo with none stops at its own first step for want of a
green run, and `/crap-test` needs that coverage run before it, exactly as `/mutation-test`
does. The other nine are never *untested*: `/static-analysis`, `/security-compliance`, and
`/dry-test` read the code without running it; `/contract-test`, `/visual-accessibility`,
`/fault-injection-test`, and `/stress-test` need a running instance rather than a suite;
`/integration-test` writes its own tests and starts its own containers.

Specified behaviour is the ninth, and the one people wrongly assume is blocked. `/to-bdd` needs
no suite and no written requirements either — it mines a draft from the code where none are
written. `/wire-bdd` *builds* the harness rather than needing one, naming the BDD framework
that fits the stack and asking before it adds the dependency. `/run-bdd` runs what those two
produced. The three go end to end on a repo with no tests at all, so the dimension is
unmeasured, never untested, and never blocked.

Then put the gaps to the user in **one** question — twelve asked one at a time is an
interrogation. But ask only about what they can run today. A dimension whose precondition is
missing is not a decision anybody can make: nobody can weigh mutation testing on a repo with no
tests, and that row costs a real decision its attention. So split the gaps by precondition:

| Precondition | Met when | In the question |
| --- | --- | --- |
| a build | the project compiles | `/static-analysis`, `/security-compliance`, `/dry-test` |
| a running instance | there is one you can point at | `/contract-test`, `/visual-accessibility` |
| an instance you may break, or a realistic load | you have both the environment and permission | `/fault-injection-test`, `/stress-test` |
| nothing but the code | always met | `/to-bdd`, `/wire-bdd`, `/run-bdd` |
| a suite | tests run green | `/code-coverage`, then `/crap-test` and `/mutation-test` |
| containers you can start | Docker is available | `/integration-test`, which brings its own suite |

**Rows only for the ones whose precondition is met.** Give each its relevance, the command,
what it costs in time, and what a skip costs. Mark exactly one **← start here**: the cheapest
one on the list, with a defect-finder beating a measurement on a tie. Costs come from the step
7 table. Below, a repo that has a suite but no running instance and no Docker:

| Dimension | Relevance | State | To fill it | Costs | Skipping it means |
| --- | --- | --- | --- | --- | --- |
| Construction | applies | no report | `/static-analysis` ← start here | minutes | live bugs stay unfound in code nobody has tested |
| Single source | applies | no report | `/dry-test` | minutes, one install | one rule in four files, and the next fix lands in one of them |
| Verified behaviour | applies | no report, suite exists | `/code-coverage` | minutes | no idea which code runs under test |
| Change risk | applies | no report | `/crap-test`, after `/code-coverage` | minutes | no list of the functions that are dangerous to edit |
| Exposure | applies | no report | `/security-compliance` | under an hour | a committed secret or a reachable flaw stays live |
| Test strength | applies | stale, 47 commits behind | `/mutation-test` | an afternoon or more | the coverage number stays unexamined |
| Specified behaviour | by choice | no `.feature` files | `/to-bdd`, `/wire-bdd`, `/run-bdd` | an afternoon or more | nothing states what the code is supposed to do |

**The rest is one line, not rows.** Name them, name the one thing each is waiting for, and ask
nothing: "Promised behaviour and access wait on a running instance you can point at. Resilience
and headroom wait on one you may break or load. Proven seams waits on Docker." The reader sees
the whole map and is asked about the part they can act on.

Specified behaviour is never in that line. It waits on nothing, so it belongs in the rows —
phrased as an offer because it is by choice, and one that stands whether or not the team has
ever written a requirement down.

Not applicable and out of scope dimensions stay out of the question entirely — they belong in
the report, where nobody has to decide anything about them.

The sibling skills are the user's to run — none fires on its own, so hand over the commands
for the ones they picked and let them type them. A previous report's own duration is the best
time estimate you have. Then they call `/code-quality` again with the fresh reports waiting on
disk.

An applicable dimension the user skips is **unproven**, exactly like one never run. Record it
with the decision and who made it, so the next reader sees a choice rather than a blank.

**Done when:** the scope is stated and every dimension carries a relevance with the surface,
the scope, or the decision behind it; every applicable unproven one is marked unmeasured or untested and is either backed by a
report you have read or recorded as skipped with the user's decision; the question held rows
only for dimensions whose precondition is met, with exactly one marked **start here** and the
rest named in a line; and where the user asked for a signal to be filled they have the exact
command.

## 4. Read each dimension

Read each applicable dimension from its report:

| Dimension | Read from |
| --- | --- |
| **Verified behaviour** | coverage report — line %, branch %, files at 0% |
| **Test strength** | mutation report — score, survivors, no-coverage mutants |
| **Change risk** | CRAP report — the count over 30, the 🔴 split list, the 🟠 test list with each gap, the unmeasured count |
| **Specified behaviour** | BDD report — passed, failed, pending, blocked, unwired |
| **Promised behaviour** | contract report — contract coverage, conformance, P1 drift |
| **Proven seams** | integration report — seam coverage, hermetic verdict, unproven seams |
| **Resilience** | fault injection report — hypothesis pass rate, recovery verdict, blast radius per weakness |
| **Headroom** | stress report — the knee, headroom against the expected peak, the soak verdict, what gave first |
| **Access** | accessibility report — criteria coverage, state coverage, P1 barriers |
| **Exposure** | security report — P1 count, reachable CVEs, unrotated secrets, OWASP gaps |
| **Construction** | static analysis report — findings by category, P1 count |
| **Single source** | DRY report — families per bucket, the unsupported and parse-error counts, each 🔴 family's knowledge sentence |

Two of them sound alike and are not. Specified behaviour is the spec the team wrote for
itself, checked from inside. Promised behaviour is the contract the API published to other
people, checked from outside by a caller who cannot see the code.

Grade each. Every band is exhaustive: read top down and take the first that matches, so no
combination of results leaves you inventing a grade.

| Grade | Verified behaviour | Test strength | Change risk | Specified behaviour | Promised behaviour | Proven seams | Resilience | Headroom | Access | Exposure | Construction | Single source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 🔴 **Fragile** | branch < 50%, or any P1 file at 0% | score < 60% | any 🔴 function — complexity ≥ 31, unfixable by testing — or any function over 30 in money, permissions, or data writes | any scenario failing | any P1 breaking drift, or contract coverage < 50% | the hermetic checks failed, or a seam handling money, permissions, or data writes is unproven, or seam coverage < 50% | any experiment that did not recover, or a dependency handling money or data writes that broke outright, or a hypothesis pass rate < 50% | headroom < 1 — it cannot serve today's peak — or the soak run failed, or throughput collapses past the knee | any P1 barrier, or criteria coverage < 50% | any P1 — a reachable flaw, or a secret not yet rotated | P1 bugs in money, permissions, or data writes | any 🔴 family — verbatim, or one shape co-changed three times or more |
| 🟡 **Thin** | branch 50–69% | score 60–79% | any 🟠 function — over 30, and tests alone can bring it under | any scenario pending, blocked, or unwired | any P2 divergent drift, or contract coverage 50–79%, or a derived contract | seam coverage 50–79%, or a container version behind production | any unplanned degradation or collateral damage, or a pass rate 50–79%, or a run covering only some of the ranked dependencies | headroom 1–2×, or a shape that did not run, or a closed-model run | any P2 barrier, or criteria coverage 50–79%, or a rules-engine pass with no driven checks | any P2, or a scan kind that did not run, or an OWASP category nothing checked | bugs present | any 🟠 family, or a language in scope the engine has no grammar for |
| 🟢 **Sound** | branch ≥ 70%, no P1 file at 0% | score ≥ 80% | no function over 30, and the join matched 95% or more | every scenario green | no P1 or P2 drift, contract coverage ≥ 80% | seam coverage ≥ 80%, hermetic passed, no unproven seam in the top rank | pass rate ≥ 80%, every experiment back in band inside its hard stop, no unplanned degradation and no collateral | headroom ≥ 2×, soak passed, all five shapes run under an open model | no P1 or P2 barrier, criteria coverage ≥ 80%, the keyboard and focus checks driven | no P1 or P2, all four scan kinds ran, every OWASP category checked | no bug finding | no 🔴 or 🟠 family, every language in scope scanned |
| ⚫ **Unproven** | no usable report | no usable report | no usable report | no usable report | no usable report | no usable report | no usable report | no usable report | no usable report | no usable report | no usable report | no usable report |

Seven results in that table override the numbers beside them, whatever those numbers say:

| Result | What it forces | Why |
| --- | --- | --- |
| A **blocked** scenario | Thin, alongside pending and unwired | all three mean the behaviour was never exercised, and 19 green with 1 blocked is 19 proven and 1 unknown |
| A failed hermetic check | proven seams Fragile | a green that depends on test order, or on data the last run left behind, is evidence of nothing |
| An experiment that never recovered | resilience Fragile | a fault ends; surviving nine of ten counts for nothing against the tenth that needs a human to restart it |
| A **derived** contract | promised behaviour capped at Thin | it was written from the implementation, so the two agree by construction. A reviewed contract lifts the ceiling |
| A **closed-model** run | headroom capped at Thin | the generator stopped sending while the system stalled, so those percentiles describe a system asked to do less exactly when it was struggling |
| A CRAP join below 95% | change risk **Unproven** | the two input files did not line up, so the table describes a fraction of the functions while looking complete |
| A DRY self-check that did not pass | single source **Unproven** | a clone finder that parsed nothing reports "no duplicates", which reads exactly like good news |

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
| Sound coverage, functions over 30 | the average is fine and the risk is not spread evenly. The uncovered part sits exactly where the branching is, which is the definition of the change nobody dares make |
| High CRAP, low mutation score | those functions are both the hardest to change and the least watched while you change them. Fix here first — every other move touches this code eventually |
| Functions over 30 in the same files as the P1 bugs | the analyzer and the metric agree on where the trouble is. Two independent signals on one file is the strongest pointer either can give |
| A 🔴 clone family across files with different coverage | the same knowledge is tested in one home and untested in the others. The fix lands in the tested copy and the untested copies drift |
| A 🔴 clone family in high-churn files | duplicated knowledge that is being edited. Every commit is a chance to change one copy and forget the rest, and this is where that already happens |
| Duplication found, static analysis clean | the analyzer looks inside a file at a time. Knowledge copied across files is invisible to it, and this says nothing was wrong with the copies individually |
| Many unsupported files in the DRY run, single source Sound | the green covers the languages with a grammar. The rest of the repo was never looked at |
| High coverage, high test count, findings all style | the strongest shape available. Say so plainly |
| Every dimension unproven but one | there is no verdict here yet, only one number |

**Done when:** every pair in the table that both its signals support has been checked, and
each one that fires is written up with its two numbers.

## 6. Give the verdict

One verdict for the codebase, by these rules, in this order. A dimension marked **not
applicable**, **out of scope**, or **by choice** in step 3 is outside every count here, so a
library is judged on the six dimensions it has, one module on the eight its scope can answer,
and a whole service serving pages on all twelve:

1. Two or more applicable dimensions unproven → **Unproven**. One dimension is a number, not
   an assessment.
2. Otherwise the verdict is the **worst** grade any measured dimension carries. Never the
   average, never the majority.
3. State the count beside it, always, out of the number that apply: "Sound, 1 of 7 applicable
   dimensions unproven". Then name what was set aside and why — "1 does not apply: ships as a
   library, serves no API", "4 out of scope: you asked about `src/domain/`, and these describe
   the deployed system, so exposure is graded on its static half alone", "1 by choice: this
   team has decided against a written spec" — so the reader sees
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

**A verdict can fall because the standard widened rather than because the code did.** When
the previous report graded fewer dimensions than this one, and the new verdict is worse only
because of a dimension that report never had, say so in the same breath: "🟡 Thin → ⚫
Unproven. Nothing in the code got worse. Two dimensions were added since the last run and
neither has been measured yet." A reader who is not told this reads a widened standard as a
regression they caused, and the first thing they do is go looking for the commit that broke
it.

**Done when:** the verdict follows the three rules, the dimension that set the floor is
named, the unproven count is stated out of the number that apply, everything set aside names
whether it was scope, surface, or choice, an unproven verdict says whether it is unmeasured
or untested, and a verdict that fell only because the previous report graded fewer dimensions
says so.

## 7. Chart the next moves

A verdict a reader cannot act on is a grade with no lesson attached. Name the starting
position, then order the moves it calls for.

| Starting position | Test |
| --- | --- |
| **Bare** | no tests at all |
| **Thin** | tests exist, and one or more dimensions grade Thin or Fragile |
| **Instrumented** | every applicable dimension measured, none Fragile |

### Which dimensions to cover next

**One move first, the rest behind it.** A reader handed nine commands runs none of them. Open
with a single recommendation and put the others in an ordered list underneath, never as a plan
for one sitting. Say how far the opening move gets them — "this one, then call `/code-quality`
again and it will pick the next" — because a reader who finishes one thing comes back, and a
reader handed a quarter's work does not. The map stays visible; the decision does not.

Every recommendation names the dimension, the command that fills it, what it costs, and what
it would tell you that nothing else does.

**The list is ordered by value. The opening move is chosen for momentum:** the cheapest
dimension on that list whose precondition is already met. The first move has to finish, not
impress. Cost, unless something about this project says otherwise:

| Cost | Skills |
| --- | --- |
| **minutes** | `/static-analysis`, `/dry-test`, `/code-coverage`, `/crap-test` |
| **under an hour** | `/security-compliance`, `/contract-test`, `/visual-accessibility` |
| **an afternoon or more** | `/integration-test`, `/mutation-test`, `/stress-test`, `/fault-injection-test`, and the BDD three |

Two rules break a tie: a skill that finds defects beats one that produces a measurement, and
a dimension describing a system users are hitting today beats one describing code at rest.

**On a bare codebase the ladder below sets the order instead, and the opening move is its move
1.** That ladder is built around preconditions unlocking each other, and cheapest-first would
break the chain. It also overrides rule 3 for specified behaviour: on a repo with nothing
measured the scenarios come second rather than last, because they are the only thing on the
ladder that says what the code is *for*. Still by choice — a team that wants no written spec
skips it — but never skipped merely for having written nothing down yet.

Then order the rest by value:

1. **Applicable, unproven, and describing something already running.** Exposure, promised
   behaviour, and access describe a system users are hitting today, so what they find is
   already costing somebody something.
2. **Then the ones that unlock others.** A suite before coverage, coverage before mutation.
   Recommending mutation testing to a repo with no suite wastes the reader's week.
3. **By choice, last, and phrased as an offer.** "Worth adopting if the team wants a written
   spec — `/to-bdd` drafts one from the code where none exists" — never "missing". A practice
   this team has decided against is not a gap in their code. But offer it to a team with no
   requirements written down: that is the case the skill handles, not one it rules out.

Then close with one line for each dimension that does not apply and the surface it lacks, so
nobody re-raises it next quarter as an oversight.

### From bare

The order runs spec first, and one fact decides it: **almost every dimension here measures the
code against itself.** Coverage, test strength, change risk, single source, construction — all
of them can come back green on an implementation that does the wrong thing correctly. Only the
scenarios say what the code was supposed to do. Testing a wrong implementation thoroughly buys
nothing, so the scenarios come before the tests, and the tests come before the numbers that
judge them.

1. **Run `/static-analysis`.** The cheapest signal there is on day one, and it finds real bugs
   in code nobody has ever tested. A broken *build* is the only thing that stops it.
2. **Write the scenarios and make them run — `/to-bdd`, then `/wire-bdd`, then `/run-bdd`.**
   The requirements move, for the reason just above: after it, everything has something outside
   the code to be judged against. Scenarios written after the tests only encode what the code
   already does. It pays forward too — `/contract-test` derives a contract from the routes where
   none is published, and scenarios in hand make that a review rather than a guess.

   **All three, not just the first.** `/wire-bdd` writes the step definitions, and where the
   project has no BDD framework it names the one that fits the stack and asks before adding it,
   so a bare repo does not block here, it only pays more. `/run-bdd` runs them and writes the
   `bdd-report-` this skill reads; without it specified behaviour stays ⚫ Unproven however good
   the scenarios are. Wiring is also what proves a scenario was written concretely enough to
   execute, and a step nobody can wire is a requirement still too vague to have been agreed —
   worth finding out while the conversation is open. Where this move runs, the project has a
   working test command from here on.

   **One slice, not the repository.** Checkout, or auth, or billing — a bounded area agreed with
   the user first. `/to-bdd`'s own mining process says why: a whole codebase drafted at once
   produces a pile nobody will read closely enough to confirm, and the confirming is what turns
   a draft into requirements. One slice also keeps this move finishable — move 1 is minutes and
   this one is days, and a second move that never ends is where a plan gets abandoned. The other
   slices come round on the next pass.

   **No written requirements is the case this move is for, not a reason to skip it.** Where
   nothing states a behaviour anywhere, `/to-bdd` mines the code — entry points, guards, status
   transitions, existing test names — into a **draft** the team then confirms line by line. That
   confirmation is the requirements-writing, and it is the only safeguard that matters here: a
   mined scenario records what the code *does*, so a bug nobody questions becomes the official
   spec and the next test locks it in. Hand the draft over as questions, never as findings. Skip
   the move only where the team has decided against a written spec at all — a decision to
   record, and not the same thing as having none yet.
3. **Run `/contract-test` where the project serves an API, and `/visual-accessibility` where
   it serves pages.** Both need a running instance and no suite at all, both are under an hour,
   and neither can hurt anything — one sends requests and reads the replies, the other drives
   the interface in a browser. On something with users they find failures that are costing
   somebody something today. The other two running-system skills wait until moves 10 and 11.
4. **Run `/dry-test`, before the suite grows past move 2's one slice.** It needs no suite, and
   it is worth doing in this order rather than later: duplicated knowledge that survives into a
   test suite becomes duplicated tests, and then every one of them has to be changed together
   too.
5. **Run `/integration-test` where the code talks to a database, a queue, or a bucket.** It
   writes the tests, starts the containers, and fills **proven seams** — the dimension nothing
   else on this ladder reaches. A BDD suite wired at move 2 drives the code, not its
   collaborators, so however green it is, no mock in it has ever met a real database.

   Where there are no seams and move 2 built no harness, this move is instead: get any one test
   running, on anything, however trivial. Aim at a runnable suite, not at coverage — the first
   test is the only one that costs setup, and three dimensions are blocked until it exists.
6. **Then `/code-coverage`, straight away.** Do not wait until the suite is worth measuring.
   The first number is low and that is the point: it is the map of what is untouched, and it
   is what move 7 aims at. Running it early also means every later run has a floor to compare
   against.
7. **Write tests where the risk is, not where the code is easy.** The coverage report ranks
   this for you now. Where it has not run, rank by churn × what the code decides:
   ```sh
   git log --since='6 months ago' --name-only --format= | grep . | sort | uniq -c | sort -rn | head -20
   ```
   The `grep .` matters: `--name-only` prints a blank line between commits, and without it
   the blank sorts to the top as your busiest file. Cross that list against the code that
   moves money, checks permissions, or writes data. That intersection is the first week of
   work — a short list, not the whole repo.
8. **Then `/crap-test`, on the same coverage run.** It costs one script over the report you
   already have, and it turns "cover more" into a list of functions with a coverage target
   each. Take it before mutation testing: it is cheaper, and it says where to point the
   expensive run.

   **Why it comes after move 7 and not before it,** when a target list would obviously help
   the test-writing: at near-zero coverage the formula collapses to `complexity² + complexity`,
   so every function ranks by complexity alone. It would flag nearly everything non-trivial and
   say nothing about churn, money, or permissions — a longer list than move 7's and a worse
   one. CRAP discriminates only once there is real coverage to differentiate against. From the
   second pass onward it *is* the aiming tool, which is what the thin ladder below says.
9. **Then `/mutation-test`, on the covered core only.** It has something to bite on now,
   and a small scope keeps the run finishable.

   **Moves 6 to 9 are one lap, not a line.** Measure, write, target, strengthen — then round
   again on the next slice, with the CRAP list aiming the writing this time and the mutation
   survivors saying which existing tests assert nothing. A reader who takes move 9 as the
   finish line has covered one slice and stopped. The "from thin" ladder below is that second
   lap, and it is where most of the improvement actually happens.
10. **Then `/stress-test`.** It needed only a running instance and could have gone at move 3.
    It waits because it asks for two things a codebase in this state rarely has — an
    environment that can take the load, and a peak figure somebody is prepared to defend — and
    because what it finds is capacity work. Changing that with the suite from moves 2 to 8
    behind you is a different proposition from changing it blind.
11. **Then `/fault-injection-test`.** Last of the running-system four, because it is the only
    one that breaks things on purpose. It needs an environment you are *allowed* to break, a
    hard stop, and a steady state — the handful of numbers that say the system is serving
    people — measured before anything is broken. A project with no tests usually has no metrics
    either, and without that baseline the run produces nothing gradeable. Move 10 gives you
    normal load; move 2 gives you what "serving people" means.
12. **Then `/security-compliance`.** It needs no suite and could have run on day one; it sits
    here by choice rather than by precondition.

Moves 10 to 12 are a deliberate departure from the ordering rule above, which puts anything
describing a running system first. Headroom and resilience sit at the end because their
preconditions are the heaviest on the ladder; exposure sits there by choice. Two things follow,
and the report says both rather than letting a reader find them later:

- **A committed secret stays live for the whole ladder.** Every move before 12 is measurement;
  that one finds defects an attacker can already reach. Eleven moves is a long time for a key
  to sit in git history.
- **The verdict clears at the very end.** Headroom, resilience, and exposure stay unproven
  until moves 10, 11 and 12, and any two unproven dimensions hold the verdict at ⚫ Unproven.
  Move 11 is the earliest a bare codebase can be graded, and move 12 the realistic one — proven
  seams is also unproven wherever `/integration-test` never ran. Everything before that reads
  Unproven however much work has landed.

Where the user has not made that trade deliberately, offer the swap: `/security-compliance` is
under an hour, needs nothing but a build, and finds live defects rather than measuring
anything. Run at move 1 it takes exposure out of the unproven count for the whole ladder — the
verdict clears a move sooner, and a committed secret surfaces on day one instead of at the end.
The two that genuinely have to wait are stress and fault injection, and those wait on an
environment rather than on a preference.

Say plainly that this is a body of work. A plan presented as a quick fix gets abandoned at the
first sprint boundary.

Then hand over move 1 alone. Twelve moves is the map, not the ask, and a bare codebase is
exactly the reader most likely to close the report and do nothing. `/static-analysis` on its
own is minutes of work that comes back with real bugs. The rest keeps.

### From thin

One rule decides the order, and it turns on the pair of signals you already have:

| The pair | Go for | Why |
| --- | --- | --- |
| Coverage low, mutation unknown or absent | **breadth** — cover the risky uncovered code first | there is nothing to strengthen yet |
| Coverage high, mutation score low | **strength** — kill survivors in the covered code first | the tests you have do not check what they run, and more of the same makes the number prettier and the suite no better |
| Both middling | **strength** in the P1 modules, breadth everywhere else | risk decides, not the average |

Whichever row fires, the CRAP report picks the functions. Breadth and strength are both
"write tests", and the 🟠 list already says which functions and how much coverage each one
needs — a target beats a direction.

Then order the individual moves across every report by these three, in order:

1. **Exposure findings, and anything already broken.** A committed secret or a live bug
   outranks every measurement, because it is a defect rather than a number about defects.
2. **The dimension that set the floor.** It decided the verdict, so it is what changes the
   verdict.
3. **Highest churn first, inside each.** The code changing fastest breaks soonest.

### From instrumented

The moves are the sibling reports' own P1 lists, merged and ordered by the same three rules.
Add one: recommend the gates each sibling proposed — the coverage ratchet, the mutation
threshold, the CRAP ceiling on changed functions, the analyzer baseline, the DRY check over
changed files, BDD strict mode, the contract run judged on new drift, the
integration suite in CI, the cheap fault experiments on pull requests, the load smoke and the
regression gate, the four accessibility gates, the four security gates — because an
instrumented codebase with no gate drifts straight back to thin.

**Done when:** the starting position is named, exactly one opening move is named and it is
either an outright defect or — where nothing is broken — the cheapest dimension whose
precondition is met, every move is one thing a person can do with the skill or
command that does it, every applicable unproven dimension appears as a recommendation with its
cost and what it would tell them, by-choice dimensions read as offers and not-applicable ones
as closed questions, and a bare codebase's plan says it is a body of work rather than an
afternoon.

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

Then tell the user four things and stop: the file path, the verdict with its unproven count,
the one next move with what it costs, and that calling `/code-quality` again afterwards picks
the one after it. The report holds the whole list; the message holds one move. Reciting the
list in the message undoes the ordering the report just did.

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
| **Starting position** | thin — 11 of 11 applicable dimensions measured, 7 of them Fragile |
| **Bands** | project gates where set, defaults otherwise |
| **Previous** | [`quality-report-2026-07-23-140218.md`](./quality-report-2026-07-23-140218.md) |

## Verdict

# 🔴 Fragile — 0 of 11 applicable dimensions unproven, 1 set aside by choice

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
| Change risk | applies | 🔴 Fragile | 9 functions over 30, 1 needs splitting, worst `applyRefund` at 148.6 | [CRAP](./crap-report-2026-07-30-160244.md) | 0 commits |
| Specified behaviour | by choice | — | — | none | — |
| Promised behaviour | applies | 🔴 Fragile | conformance 78.1%, contract coverage 80.0%, 3 P1 drift | [contract](./contract-report-2026-07-30-144510.md) | 0 commits |
| Proven seams | applies | 🟡 Thin | seam coverage 66.7%, hermetic passed, 2 seams unproven | [integration](./integration-report-2026-07-30-151133.md) | 1 commit |
| Resilience | applies | 🔴 Fragile | pass rate 81.8%, 1 experiment never recovered | [fault injection](./fault-report-2026-08-01-093044.md) | 0 commits |
| Headroom | applies | 🟡 Thin | knee 290 req/s, headroom 1.6× of a 180 req/s peak, soak passed | [stress](./stress-report-2026-08-01-104530.md) | 0 commits |
| Access | applies | 🔴 Fragile | 3 P1 barriers, criteria coverage 72.0%, 22 of 22 states | [accessibility](./accessibility-report-2026-08-01-141005.md) | 0 commits |
| Exposure | applies | 🔴 Fragile | 4 P1 — 1 unrotated secret, 1 reachable CVE, 2 access control | [security](./security-report-2026-07-31-140203.md) | 0 commits |
| Construction | applies | 🔴 Fragile | 14 bug — 3 in the refund path — 61 risk findings | [static analysis](./static-analysis-report-2026-07-30-153001.md) | 0 commits |
| Single source | applies | 🟡 Thin | 2 🟠 families, 0 🔴, 14 files unsupported (`.sql`) | [DRY](./dry-report-2026-07-30-162811.md) | 0 commits |

Exposure, construction, test strength, change risk, promised behaviour, resilience, and access
are jointly at the floor, so the verdict is 🔴 Fragile.

## What is not graded here

| Dimension | Relevance | Why | Decision |
| --- | --- | --- | --- |
| Specified behaviour | by choice | no `.feature` files; the team was offered `/to-bdd` and declined a written spec | their decision, recorded on 2026-07-28. Not a gap in the code, and not counted against the verdict. Having no requirements written down would not have put it on this table — `/to-bdd` drafts those |

Had the ask been `src/domain/` rather than the service, promised behaviour, resilience,
headroom, access, and the live half of exposure would sit here too, marked **out of scope**.

## What the signals say together

| The pair | The numbers | What it means |
| --- | --- | --- |
| High coverage, low mutation score | 78.4% covered, 61.4% killed | the tests run the code and check about six lines in ten of it |
| Green suite, breaking contract drift | 412 tests green, `GET /orders/{id}` returns `total` as a string | the suite checks the code against itself. The promise to callers broke and nothing in CI noticed |
| Functions over 30 in the same files as the P1 bugs | 6 of the 9 sit in `src/billing/`, as do 3 of the 14 bugs | two independent signals agree on one folder. That is where the next defect comes from |

## Dimensions to cover next

| Dimension | Relevance | Run | Costs | What it would tell you |
| --- | --- | --- | --- | --- |
| Specified behaviour | by choice | `/to-bdd`, `/wire-bdd`, `/run-bdd` | an afternoon or more | whether the code does what it is supposed to, rather than what it happens to do. Nothing else here asks that. No requirements are written down, which is what `/to-bdd` mines a draft for; nothing is wrong with the code for lacking it |

**Not applicable here:** none — this service has all twelve surfaces. On a library, promised
behaviour, proven seams, resilience, headroom, and access would sit on this line instead;
change risk and single source never do.

## The next moves

**Start here:** rotate the signing key and take it out of the source. Minutes of work, and
nothing else on this list matters while a live key sits in git history.

The rest of the list keeps. Run `/code-quality` again when that one is done and it will name
the move after it.

Thin start, so the pair of signals decides the order. Strength before breadth: coverage is
78% and the mutation score is 61%, so the tests already reach the code and adding more of the
same would move the wrong number.

| # | Do this | Why it is here | Costs | Command |
| --- | --- | --- | --- | --- |
| 1 | Rotate the signing key, then remove it from the source | a committed secret is live until the key changes, and git history keeps it | minutes | — |
| 2 | Make the order consumer recover on its own, and alert on lag | any broker blip stalls it for good. Checkout keeps returning 200, so orders are accepted and never processed and nothing reports it | a day | `/fault-injection-test` |
````

Drop any empty section, and lead the body with the verdict. The dimension that set the floor
is named in the verdict and appears first among the moves that are not outright defects.

A **bare** codebase's report is the same shape with two differences: the verdict is
"Unproven — untested", and the moves table holds the step 7 ladder in that order rather than a
merge of sibling lists, with move 7 naming the actual high-churn modules and their commit
counts. It closes on the three things step 7 says a bare plan must state: that this is a body
of work rather than an afternoon, that the verdict stays Unproven until the end of the ladder,
and that `/security-compliance` can be pulled forward to move 1 for a graded verdict sooner.
