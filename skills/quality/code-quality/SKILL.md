---
name: code-quality
description: >
  The front door to the seven development dimensions: read whichever reports are on disk,
  say which dimensions this project should cover, cross-read them, and give one graded
  verdict on the code as written and tested.
disable-model-invocation: true
---

Seven dimensions, each named for what it measures rather than the tool that measured it:

| Dimension | The question it answers | Measured against | Filled by |
| --- | --- | --- | --- |
| **Verified behaviour** | how much of the code runs under test | the suite | `/code-coverage` |
| **Test strength** | would the tests catch a bug, or only run past it | the suite | `/mutation-test` |
| **Change risk** | which functions are dangerous to edit | the code, crossed with the suite | `/crap-test` |
| **Specified behaviour** | does the written spec hold | the suite | `/to-bdd`, `/wire-bdd`, `/run-bdd` |
| **Construction** | what is wrong with the code as written | the code | `/static-analysis` |
| **Single source** | is one piece of knowledge living in several places | the code, crossed with git history | `/dry-test` |
| **Readability** | can the next person read this and change it safely | the code, read as a reader | `/clean-code` |

These are the seven a developer can answer without deploying anything. Every one is measured
against the code or the suite, so all seven work on a laptop, on a branch, at module scope, in
the middle of an afternoon. That is what makes this the set to keep green during development
rather than at a release gate.

**Two sets sit outside this skill.** `/release-quality` covers the five that need a running
system; `/visual-quality` the two that need a rendered interface. Name both at the end of the
report so nobody reads seven green rows as a whole-system pass.

Each dimension alone is easy to misread — 90% coverage looks like health until the mutation
score says the tests assert nothing. On a repo with no reports at all this skill does not stop
at "unproven": it works out which dimensions the project should cover and hands over the command
for each. Three rules hold throughout.

**Relevance comes before measurement.** Grading a project against dimensions it has no surface
for manufactures failures and buries the real ones.

**The verdict is a floor, not an average.** Sound on six and fragile on the seventh is fragile.

**Absent evidence is never good news.** No report, a skipped one, and a stale one all read as
**unproven**.

## 1. Find the reports

Search every `.reports/` folder in the repository. The seven siblings write
`coverage-report-`, `mutation-report-`, `crap-report-`, `bdd-report-`,
`static-analysis-report-`, `dry-report-`, and `clean-code-report-`, timestamped, one file per
run, per module. Take the newest of each kind, per module — on a fix run a sibling writes a
before and an after, and the after is the one that describes the code as it stands.

Set your own past reports aside. `code-quality-report-*` files are this skill's own output and
they are the **comparison** in step 6, never a dimension. Grading one as evidence pins the new
run to the old floor, so a codebase that has improved keeps reporting last month's grade.

`quality-report-*` is this skill's **former** name, from before the twelve dimensions were split
across three phases. Treat one as the comparison too, and say in step 6 that it graded a wider
set — a verdict that looks worse beside it may only be a narrower one, which is exactly the
widened-standard case that step warns about, running in reverse.

Leave the other two phases' reports alone as dimensions too. `release-quality-report-*`,
`visual-quality-report-*`, and the five release and two visual sibling reports belong to
`/release-quality` and `/visual-quality`. Note in step 5 that they exist — a `security-report-`
sitting there is worth cross-reading — but never grade one here.

Read anything else in there too. A dependency audit, a benchmark, a type-check log, a
complexity report: each becomes an extra dimension in step 4 rather than a file you
stepped over.

**Done when:** you have every report found with its kind, module, timestamp, and the commit
named in its header; a list of the seven kinds that turned up nothing; the newest
`code-quality-report-*` held aside as the comparison rather than counted as a dimension; and
any release or visual reports noted as cross-reading material rather than as dimensions.

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
| **Partial** | under half the files in scope changed since | full evidence for the unchanged files, none for the changed ones |
| **Stale** | half the scope or more changed since | a lead, not evidence |
| **Unusable** | the commit is unknown to this repo | no evidence |

**Partial is the normal state during development, and it is the row that protects the day.**
A report does not stop being evidence because one file moved. It stops being evidence *for that
file*. So name the changed files rather than the report:

```sh
git diff --name-only <report commit>..HEAD -- <the report's scope>
```

That list is the only thing a re-run has to cover. A coverage report on forty files with three
of them touched is thirty-seven files of standing evidence and three to measure again — not a
whole run thrown away. Carry the report's grade for the untouched files, mark the touched ones
unproven, and say both in step 4: "Sound on 37 of 40 files; 3 changed since and unmeasured."

**The half is a floor, and both directions matter.** Marking a report stale because any file
in it moved is what makes these seven feel expensive: on a branch that moves every day it
condemns every report every day, and the reader re-runs the repo to learn what a diff would
have told them. But a grade earned by one file in forty is not evidence either, however
carefully you qualify it — past half, the report describes a codebase that no longer exists
and the honest word for it is Stale.

Every sibling writes "dirty working tree" into its header when the tree was dirty. That note
means the run covered code the commit does not hold, so add the working tree to the check —
**as well as** the commit diff, never instead of it. Run `git status --porcelain -- <the
report's scope>`, union its files with the `<report commit>..HEAD` list, and read the states
off the union. Skipping the commit half is how a report generated five commits ago on a tree
that is clean today grades **Current** and carries stale numbers forward as full evidence.

The union over-reports in one direction: a file already dirty when the sibling ran is a file
that run *did* measure. Where the sibling's header names what it read, trust that over the
porcelain. A dirty tree alone is not a reason to discard the reports somebody just generated.

Staleness bites harder here than in the other two phases. These seven are read during
development, on a branch that moves every day, so a report three days old is often already
describing code that no longer exists. Check the distance every run; do not carry a grade
forward because it was fresh last time — but check it file by file, so what you carry forward
is the part that is still true rather than the whole report or nothing.

Scope matters as much as age. A coverage report on `src/domain/` says nothing about
`src/http/`, however fresh. Record what each report covered and what it left out.

**Done when:** every report carries a state and its commit distance, every Partial one names
the changed files that need re-measuring rather than being condemned whole, every dirty-tree
report was rated against uncommitted changes in its own scope rather than discarded, and every
gap between a report's scope and the code you were asked about is written down.

## 3. Judge relevance, then settle the gaps

All seven apply to every project that has code, and all seven survive a narrow scope. That is
the point of this set, and it makes this step short: no *not applicable* row here and no *out of
scope* row either, unlike the other two phases.

| Measured against | Dimensions | At module scope |
| --- | --- | --- |
| the code | construction, single source, readability | **applies** — the analyzers and the reader take a path |
| the suite | verified behaviour, test strength, change risk, specified behaviour | **applies** where the suite reaches that path |

Single source is the one a narrow scope weakens rather than rules out: a clone finder over one
folder cannot see the copy in the next one, so a green there means "no duplication inside this
folder", never "no duplication". Say which you measured.

Then give every dimension one relevance:

- **Applies** — the default for all seven, so an unproven grade is a real gap.
- **By choice** — specified behaviour only, where the team has decided against a written spec.
  Having written no requirements *yet* is not that decision — `/to-bdd` mines a draft from the
  code for exactly that case. Record the decision and who made it, never a grade.

Where an applicable dimension is unproven, say which kind:

| Why it is unproven | How to tell | What fills it |
| --- | --- | --- |
| **Unmeasured** — the tool was never run on what exists | a suite runs, or `.feature` files exist, or the dimension needs no suite | running the sibling skill |
| **Untested** — there is nothing to measure | no test files, no test script in the manifest, no `.feature` files | writing the first tests, which is step 7 |

Check rather than assume: test files by the project's convention, a test script in the manifest,
a test job in CI, `.feature` files anywhere.

**Only three need a suite somebody else wrote** — verified behaviour, change risk, test
strength. `/static-analysis`, `/dry-test`, and `/clean-code` read the code without running it.
And specified behaviour is the one people wrongly assume is blocked: `/to-bdd` needs no suite
and no written requirements, `/wire-bdd` *builds* the harness rather than needing one, `/run-bdd`
runs the result. The three go end to end on a repo with no tests, so that dimension is
unmeasured, never untested.

Then put the gaps to the user in **one** question — seven asked one at a time is an
interrogation — but ask only about what they can run today. Nobody can weigh mutation testing on
a repo with no tests, and that row costs a real decision its attention.

| Precondition | Met when | In the question |
| --- | --- | --- |
| nothing but the code | always | `/clean-code`, `/to-bdd`, `/wire-bdd`, `/run-bdd` |
| a build | the project compiles | `/static-analysis`, `/dry-test` |
| a suite | tests run green | `/code-coverage`, then `/crap-test` and `/mutation-test` |

**Rows only for the ones whose precondition is met**, each with its relevance, command, cost,
and what a skip costs. Mark exactly one **← start here**: the cheapest, a defect-finder winning
a tie. Costs come from the step 7 table. Below, a repo that has a suite:

| Dimension | Relevance | State | To fill it | Costs | Skipping it means |
| --- | --- | --- | --- | --- | --- |
| Construction | applies | no report | `/static-analysis` ← start here | minutes | live bugs stay unfound in code nobody has tested |
| Single source | applies | no report | `/dry-test` | minutes, one install | one rule in four files, and the next fix lands in one of them |
| Readability | applies | no report | `/clean-code` | under an hour | the next person guesses, and guesses wrong in the code that moves money |
| Verified behaviour | applies | no report, suite exists | `/code-coverage` | minutes | no idea which code runs under test |
| Change risk | applies | no report | `/crap-test`, after `/code-coverage` | minutes | no list of the functions dangerous to edit |
| Test strength | applies | stale, 47 commits behind | `/mutation-test` | minutes on the branch diff | the coverage number stays unexamined |
| Specified behaviour | by choice | no `.feature` files | `/to-bdd`, `/wire-bdd`, `/run-bdd` | an afternoon or more | nothing states what the code is supposed to do |

**Anything waiting on a precondition is one line, not rows.** On a repo with no suite: "Verified
behaviour, change risk, and test strength wait on a suite that runs green — step 7 says how to
get the first test running."

Specified behaviour is never in that line. It waits on nothing, so it belongs in the rows,
phrased as an offer — and it stands whether or not the team has written a requirement down.

The siblings are the user's to run; none fires on its own. Hand over the commands they picked
and let them type them, then they call `/code-quality` again with the fresh reports on disk. A
previous report's own duration is the best time estimate you have.

A dimension the user skips is **unproven**, exactly like one never run. Record it with the
decision and who made it, so the next reader sees a choice rather than a blank.

**Done when:** the scope is stated and every dimension carries a relevance with the scope or the
decision behind it; every applicable unproven one is marked unmeasured or untested and is either
backed by a report you have read or recorded as skipped with the user's decision; the question
held rows only for dimensions whose precondition is met, with exactly one marked **start here**
and the rest named in a line; and where the user asked for a signal to be filled they have the
exact command.

## 4. Read each dimension

Read each applicable dimension from its report:

| Dimension | Read from |
| --- | --- |
| **Verified behaviour** | coverage report — line %, branch %, files at 0% |
| **Test strength** | mutation report — score, survivors, no-coverage mutants |
| **Change risk** | CRAP report — the count over 30, the 🔴 split list, the 🟠 test list with each gap, the unmeasured count |
| **Specified behaviour** | BDD report — passed, failed, pending, blocked, unwired |
| **Construction** | static analysis report — findings by category, P1 count |
| **Single source** | DRY report — families per bucket, the unsupported and parse-error counts, each 🔴 family's knowledge sentence |
| **Readability** | clean code report — P1 and P2 counts, the smell totals, the dropped count |

Two of them sound alike and are not. Single source is the same knowledge written out in two
files, found by a clone finder crossed with git history. Readability is one reader failing to
follow one function, found by reading it. A file can be perfectly unique and unreadable.

Grade each. Every band is exhaustive: read top down and take the first that matches, so no
combination of results leaves you inventing a grade.

| Grade | Verified behaviour | Test strength | Change risk | Specified behaviour | Construction | Single source | Readability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 🔴 **Fragile** | branch < 50%, or any P1 file at 0% | score < 60% | any 🔴 function — complexity ≥ 31, unfixable by testing — or any function over 30 in money, permissions, or data writes | any scenario failing | P1 bugs in money, permissions, or data writes | any 🔴 family — verbatim, or one shape co-changed three times or more | any P1 — rigidity or fragility, or any break in money, permissions, or data writes |
| 🟡 **Thin** | branch 50–69% | score 60–79% | any 🟠 function — over 30, and tests alone can bring it under | any scenario pending, blocked, or unwired | bugs present | any 🟠 family, or a language in scope the engine has no grammar for | any P2 — immobility, needless complexity, needless repetition, or opacity in a file changed 5 or more times in 6 months |
| 🟢 **Sound** | branch ≥ 70%, no P1 file at 0% | score ≥ 80% | no function over 30, and the join matched 95% or more | every scenario green | no bug finding | no 🔴 or 🟠 family, every language in scope scanned | no P1 and no P2 |
| ⚫ **Unproven** | no usable report | no usable report | no usable report | no usable report | no usable report | no usable report | no usable report |

Four results in that table override the numbers beside them, whatever those numbers say:

| Result | What it forces | Why |
| --- | --- | --- |
| A **blocked** scenario | Thin, alongside pending and unwired | all three mean the behaviour was never exercised, and 19 green with 1 blocked is 19 proven and 1 unknown |
| A CRAP join below 95% | change risk **Unproven** | the two input files did not line up, so the table describes a fraction of the functions while looking complete |
| A DRY self-check that did not pass | single source **Unproven** | a clone finder that parsed nothing reports "no duplicates", which reads exactly like good news |
| A clean code run whose scope was one folder of many | readability graded on that folder alone, and the report says so | the skill reads the paths it was given, so a green here is never a statement about the repository |

**A Partial report grades on the files it still covers.** Give the dimension the grade its
unchanged files earn, and say how many files that was out of the scope: "🟢 Sound on 37 of 40
files; 3 changed since." The changed files are unproven, not a grade of their own, so they do
not drag the band down — they narrow what the band is a statement about. Where the changed
files are the P1 ones the report singled out, say that too: a green over everything except the
code somebody is editing today is the weakest green in this report.

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
| Sound coverage, functions over 30 | the average is fine and the risk is not spread evenly. The uncovered part sits exactly where the branching is, which is the definition of the change nobody dares make |
| High CRAP, low mutation score | those functions are both the hardest to change and the least watched while you change them. Fix here first — every other move touches this code eventually |
| Functions over 30 in the same files as the P1 bugs | the analyzer and the metric agree on where the trouble is. Two independent signals on one file is the strongest pointer either can give |
| 🔴 CRAP functions and P1 rigidity in the same functions | the functions hardest to change are the ones a reader cannot follow either. One split serves both, and neither dimension moves until it happens |
| Clean static analysis, P1 readability findings | the analyzer checks the code against a grammar and the reader checks it against a person. Passing the first says nothing about the second |
| Needless repetition inside files, a 🔴 DRY family across them | the same knowledge is copied at both scales. Fixing one scale leaves the other, and the next edit still misses a copy |
| Opacity findings in high-churn files, low coverage | code nobody can read, nothing verifies, and everybody keeps changing |
| A 🔴 clone family across files with different coverage | the same knowledge is tested in one home and untested in the others. The fix lands in the tested copy and the untested copies drift |
| A 🔴 clone family in high-churn files | duplicated knowledge that is being edited. Every commit is a chance to change one copy and forget the rest, and this is where that already happens |
| Duplication found, static analysis clean | the analyzer looks inside a file at a time. Knowledge copied across files is invisible to it, and this says nothing was wrong with the copies individually |
| Many unsupported files in the DRY run, single source Sound | the green covers the languages with a grammar. The rest of the repo was never looked at |
| High coverage, high test count, findings all style | the strongest shape available. Say so plainly |
| Every dimension unproven but one | there is no verdict here yet, only one number |

### If the other phases have reports on disk

Do not grade them. Read them for these pairs only, and label each one as crossing a phase
boundary so nobody mistakes it for a dimension of this report:

| The pair | What it means |
| --- | --- |
| Green suite, breaking contract drift (`contract-report-`) | the tests check the code against itself and never against the published promise. Consumers are broken while CI stays green |
| High coverage, seams mocked (`integration-report-`) | the covered lines talk to mocks, so the coverage number describes code that has never met a real database |
| Reachable flaw in code with no tests (`security-report-`) | nothing would catch the fix breaking it, so the flaw is both live and awkward to close |
| Clean static analysis, P1 exposure (`security-report-`) | the code reads well and something reachable is still open. Tidy code is not safe code |
| Green suite, a P1 access barrier (`accessibility-report-`) | the tests reach the control by calling it, and a person using a keyboard cannot reach it at all. Covering a control says nothing about operating it |

**Done when:** every pair in the first table that both its signals support has been checked,
each one that fires is written up with its two numbers, and any cross-phase pair that fired is
marked as such.

## 6. Give the verdict

One verdict for the codebase, by these rules, in this order. A dimension marked **by choice**
in step 3 is outside every count here, so a team that has decided against a written spec is
judged on six:

1. Two or more applicable dimensions unproven → **Unproven**. One dimension is a number, not
   an assessment.
2. Otherwise the verdict is the **worst** grade any measured dimension carries. Never the
   average, never the majority.
3. State the count beside it, always, out of the number that apply: "Sound, 1 of 7 applicable
   dimensions unproven". Then name what was set aside and why — "1 by choice: this team has
   decided against a written spec" — so the reader sees dimensions that were weighed rather
   than dimensions that were forgotten.

Then write the verdict out in two sentences: what the code is, and the one thing that most
needs attention. Lead with the dimension that set the floor, because that is the dimension
that decided the verdict.

**Say what this verdict does not cover, in the same breath.** These seven describe the code
and its suite. A 🟢 Sound here is a statement about a codebase, never about a running service:
it says nothing about whether the deployed API keeps its contract, whether a real database is
ever touched, what happens when it is not, how much load the thing takes, what an attacker can
reach, or whether anybody can operate the interface. One line naming `/release-quality` and
`/visual-quality` keeps a good grade from being read as a release sign-off.

An **Unproven** verdict says which kind it is, because the two mean opposite things about the
work ahead. "Unproven — unmeasured" is a codebase with tests nobody has pointed a tool at, and
one afternoon settles it. "Unproven — untested" is a codebase with no tests at all, and it is
a body of work. Never let the first phrasing stand in for the second.

Where a previous code quality report sits beside this one, say which way the verdict moved and
which dimension moved it.

**A verdict can fall because the standard widened rather than because the code did.** When the
previous report graded fewer dimensions than this one, and the new verdict is worse only
because of a dimension that report never had, say so in the same breath: "🟡 Thin → ⚫
Unproven. Nothing in the code got worse. Readability was added since the last run and has not
been measured yet." A reader who is not told this reads a widened standard as a regression they
caused, and the first thing they do is go looking for the commit that broke it.

**Done when:** the verdict follows the three rules, the dimension that set the floor is named,
the unproven count is stated out of the number that apply, anything set aside by choice says
so, the two phases outside this skill are named as not covered, an unproven verdict says
whether it is unmeasured or untested, and a verdict that fell only because the previous report
graded fewer dimensions says so.

## 7. Chart the next moves

Name the starting position, then order the moves it calls for.

| Starting position | Test |
| --- | --- |
| **Bare** | no tests at all |
| **Thin** | tests exist, and one or more dimensions grade Thin or Fragile |
| **Instrumented** | every applicable dimension measured, none Fragile |

### Which dimensions to cover next

**One move first, the rest behind it.** A reader handed seven commands runs none of them. Name
one recommendation, put the others in an ordered list under it, and say that calling
`/code-quality` again picks the next. The map stays visible; the decision does not.

Every recommendation names the dimension, the command, the cost, and what it would tell you
that nothing else does.

**The list is ordered by value; the opening move is chosen for momentum** — the cheapest
dimension whose precondition is met. The first move has to finish, not impress.

| Cost | Skills |
| --- | --- |
| **minutes** | `/static-analysis`, `/dry-test`, `/code-coverage`, `/crap-test`, `/mutation-test` over the branch diff |
| **under an hour** | `/clean-code` |
| **an afternoon or more** | `/mutation-test` over a module or the repo, and the BDD three |

`/mutation-test` is the one whose cost is set by the scope you give it, because it runs the
suite once per mutant. On the files changed against the default branch — which is what it
now takes when nobody names paths — it is minutes, and that is the version to recommend
during development. Say which scope your estimate assumes; "an afternoon" for a module and
"minutes" for a branch are the same skill.

Two rules break a tie: a defect-finder beats a measurement, and code somebody is editing today
beats code at rest. Then order the rest by value:

1. **Defect-finders that need no suite** — construction and readability.
2. **Then what unlocks others** — a suite before coverage, coverage before CRAP, CRAP before
   mutation. Recommending mutation testing to a repo with no suite wastes the reader's week.
3. **By choice, last, phrased as an offer** — "worth adopting if the team wants a written spec;
   `/to-bdd` drafts one from the code where none exists", never "missing".

Close with one line naming the two phases this skill does not cover and the command for each.

**A bare codebase uses the ladder below instead**, because its order is preconditions unlocking
each other and cheapest-first would break the chain.

### From bare

**Almost every dimension here measures the code against itself.** Coverage, test strength,
change risk, single source, construction, readability — all can come back green on an
implementation that does the wrong thing correctly. Only the scenarios say what the code was
*for*. So the scenarios come before the tests, and the tests before the numbers that judge them.

1. **`/static-analysis`.** The cheapest signal on day one, and it finds real bugs in code nobody
   has tested. Only a broken build stops it.
2. **`/to-bdd`, then `/wire-bdd`, then `/run-bdd`** — on **one slice**, agreed with the user
   first: checkout, or auth, or billing.

   **All three, not just the first.** `/wire-bdd` writes the step definitions and, where there
   is no BDD framework, names the one that fits and asks before adding it. `/run-bdd` writes the
   `bdd-report-` this skill reads; without it the dimension stays ⚫ Unproven however good the
   scenarios are. Wiring also proves a scenario was written concretely enough to execute — a
   step nobody can wire is a requirement still too vague to have been agreed. **From here on the
   project has a working test command**, which unlocks moves 5 to 8.

   **One slice, because** a whole codebase drafted at once produces a pile nobody confirms
   closely enough, and confirming is what turns a draft into requirements. It also keeps the
   move finishable — move 1 is minutes, this one is days.

   **No written requirements is the case this move is for.** `/to-bdd` mines entry points,
   guards, status transitions, and test names into a **draft** the team confirms line by line.
   Hand it over as questions, never findings: a mined scenario records what the code *does*, so
   a bug nobody questions becomes the official spec. Skip only where the team has decided
   against a written spec — a decision to record, not the same as having none yet.

   **Where they have decided that,** this move is instead: get any one test running, on
   anything. Aim at a runnable suite, not coverage — three dimensions are blocked until it
   exists.
3. **`/clean-code` on the same slice.** Needs nothing but the code, and belongs before the suite
   grows: a name that lies gets copied into every test that calls it.
4. **`/dry-test`, before the suite grows past move 2's slice.** Duplicated knowledge that
   survives into a suite becomes duplicated tests, and then every one changes together too.
5. **`/code-coverage`, straight away.** The first number is low and that is the point: it is the
   map of what is untouched, and what move 6 aims at. It also gives every later run a floor.
6. **Write tests where the risk is, not where the code is easy.** The coverage report ranks this
   now. Where it has not run, rank by churn × what the code decides:
   ```sh
   git log --since='6 months ago' --name-only --format= | grep . | sort | uniq -c | sort -rn | head -20
   ```
   The `grep .` matters: `--name-only` prints a blank line between commits, and without it the
   blank sorts to the top as your busiest file. Cross that against code that moves money, checks
   permissions, or writes data. That intersection is the first week — a short list, not the repo.
7. **`/crap-test`, on the same coverage run.** One script over the report you have, and it turns
   "cover more" into a list of functions with a coverage target each.

   **Why after move 6:** at near-zero coverage the formula collapses to `complexity² +
   complexity`, so everything ranks by complexity alone — a longer list than move 6's and a
   worse one. CRAP discriminates only once there is coverage to differentiate against. From the
   second pass on it *is* the aiming tool.
8. **`/mutation-test`, on the covered core only.** It has something to bite on now, and a small
   scope keeps the run finishable.

**Moves 5 to 8 are one lap, not a line.** Measure, write, target, strengthen — then round again
on the next slice, with the CRAP list aiming the writing and the mutation survivors saying which
tests assert nothing. A reader who takes move 8 as the finish line has covered one slice and
stopped. The thin ladder below is that second lap, and where most of the improvement happens.

Say plainly this is a body of work. A plan presented as a quick fix is abandoned at the first
sprint boundary. **And say what the ladder never reaches:** eight moves, all seven green, and
the service is still ungraded on contracts, dependencies, load, and access. Then hand over move
1 alone.

### From thin

The pair of signals you already have decides breadth or strength:

| The pair | Go for | Why |
| --- | --- | --- |
| Coverage low, mutation unknown or absent | **breadth** — cover the risky uncovered code | there is nothing to strengthen yet |
| Coverage high, mutation score low | **strength** — kill survivors in the covered code | more of the same makes the number prettier and the suite no better |
| Both middling | **strength** in the P1 modules, breadth elsewhere | risk decides, not the average |

Whichever fires, the CRAP report picks the functions — its 🟠 list already says which and how
much coverage each needs, and a target beats a direction. Then order every move by:

1. **Anything already broken** — a P1 bug, or P1 rigidity in the refund path. A defect outranks
   a number about defects.
2. **The dimension that set the floor.** It decided the verdict, so it changes the verdict.
3. **Highest churn first, inside each.**

### From instrumented

The siblings' own P1 lists, merged and ordered by those three rules. Add the gates each sibling
proposed — the coverage ratchet, the mutation threshold, the CRAP ceiling on changed functions,
the analyzer baseline, the DRY check over changed files, the clean code check on changed paths,
BDD strict mode — because an instrumented codebase with no gate drifts straight back to thin.

An instrumented codebase is also ready for the next phase: `/release-quality`, `/visual-quality`.

**Done when:** the starting position is named, exactly one opening move is named and it is
either an outright defect or the cheapest dimension whose precondition is met, every move is one
thing a person can do with the command that does it, every applicable unproven dimension appears
with its cost and what it would tell them, by-choice dimensions read as offers, the two other
phases are named with their commands, and a bare codebase's plan says it is a body of work.

## 8. Write the report

Header: `date '+%Y-%m-%d-%H%M%S'` for the timestamp, `git rev-parse --short HEAD` for the
commit, and a note if the working tree is dirty.

Write to `<module>/.reports/code-quality-report-<timestamp>.md`, where `<module>` is the
nearest directory at or above the module assessed holding the project's manifest
(`package.json`, `go.mod`, `pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`,
`Gemfile`, a `*.csproj`). An assessment spanning several modules writes to the repository root.
Create the folder if missing and add `.reports/` to the root `.gitignore` if nothing there
covers it. One file per run; never overwrite an older one.

Every source report is named and linked, with its commit distance. A verdict whose evidence
a reader cannot open is a verdict they have to take on trust.

Use the tables in [`report.md`](report.md) — every section of that shape, in that order.
Grades, numbers, states, commit distances, and next moves belong in cells. The prose left over
is the verdict itself and one sentence per cross-read pair.

Then tell the user four things and stop: the file path, the verdict with its unproven count,
the one next move with what it costs, and that calling `/code-quality` again afterwards picks
the one after it. The report holds the whole list; the message holds one move. Reciting the
list in the message undoes the ordering the report just did.

**Done when:** the report sits in the module's `.reports` folder, `.reports/` is git-ignored,
no older report was overwritten, and it holds every section of [`report.md`](report.md), with no
dimension, cross-read pair, or step 7 move left out.
