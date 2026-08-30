---
name: release-quality
description: >
  The front door to the five release dimensions: read whichever reports are on disk, say
  which dimensions this system should cover, cross-read them, and give one graded verdict
  on whether the running system is ready to carry real traffic.
disable-model-invocation: true
---

Five dimensions, each named for what it measures rather than the tool that measured it:

| Dimension | The question it answers | Measured against | Filled by |
| --- | --- | --- | --- |
| **Promised behaviour** | does the deployed API keep the contract it publishes | the running system | `/contract-test` |
| **Proven seams** | does the code work against the real database, broker, and stores | the suite, against real collaborators | `/integration-test` |
| **Resilience** | does it survive those same dependencies failing, and come back | the running system | `/fault-injection-test` |
| **Headroom** | how much load it takes before it stops keeping up | the running system | `/stress-test` |
| **Exposure** | what can an attacker reach | the code, and the running system | `/security-compliance` |

One fact decides everything about this skill: **each of the five is a property of a deployed
whole, not of a file.** Four need a running system, one needs containers it can start, and
exposure needs both. None can be run at module scope or answered on a laptop with the service
stopped. They belong at a release gate, not in the middle of an afternoon's development.

**Two sets sit outside this skill.** `/code-quality` covers the seven measured against the code
and its suite; `/visual-quality` the two that need a rendered interface. Name both at the end of
the report so nobody reads five green rows as a whole-system pass.

Each dimension alone is easy to misread — 99% contract conformance looks like health until the
coverage line says it was measured on a fifth of the API. Three rules hold throughout.

**Relevance comes before measurement.** Grading a system against dimensions it has no surface
for manufactures failures and buries the real ones.

**The verdict is a floor, not an average.** Sound on four and fragile on the fifth is fragile.

**Absent evidence is never good news.** No report, a skipped one, and a stale one all read as
**unproven**. That bites hardest here: "we have never tested what happens when the database goes
away" and "the database going away is fine" are not the same statement, and only the first is
ever true before the run.

## 1. Find the reports

Search every `.reports/` folder in the repository. The five siblings write
`contract-report-`, `integration-report-`, `fault-report-`, `stress-report-`, and
`security-report-`, timestamped, one file per run, per module. Take the newest of each kind,
per module — on a fix run a sibling writes a before and an after, and the after is the one
that describes the system as it stands.

Set your own past reports aside. `release-quality-report-*` files are this skill's own output
and they are the **comparison** in step 6, never a dimension. Grading one as evidence pins the
new run to the old floor, so a system that has improved keeps reporting last month's grade.

Leave the other two phases' reports alone as dimensions too. `code-quality-report-*`,
`visual-quality-report-*`, and the seven development and two visual sibling reports belong to
`/code-quality` and `/visual-quality`. Note in step 5 that they exist — a `coverage-report-`
sitting there changes what a mocked seam means — but never grade one here.

Read anything else in there too. A dependency audit, a benchmark, a load profile from
production, an incident review: each becomes an extra dimension in step 4 rather than a file
you stepped over.

**Done when:** you have every report found with its kind, module, timestamp, and the commit
named in its header; a list of the five kinds that turned up nothing; the newest
`release-quality-report-*` held aside as the comparison rather than counted as a dimension; and
any development or visual reports noted as cross-reading material rather than as dimensions.

## 2. Check each report is still evidence

A report describes the commit in its header, not the commit you are standing on. For each one:

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

**Then check the second thing, the one only this phase has.** A report that describes a
*running system* is only half described by its commit. The other half is the environment: the
deployed version, the dependency versions, the instance size, the data volume, the feature
flags. A stress report from an environment with a fortieth of the database production holds
measured a system nobody has since run.

**Three dimensions run against a deployed instance, and only those three carry this check.**
Each sibling records it under its own field name — read that field, not a field you expect:

| Dimension | Sibling | The field to read |
| --- | --- | --- |
| Promised behaviour | `contract-test` | **Target** — the base URL and which environment it is |
| Resilience | `fault-injection-test` | **Environment**, with **Blast radius** and **Load** beside it |
| Headroom | `stress-test` | **Environment**, with **Expected peak** and **Stubbed** beside it |

Rate each of those three:

| Environment state | Test | Weight |
| --- | --- | --- |
| **Same** | the field is there and matches the environment being released | full evidence |
| **Changed** | the field is there and something material differs — instance size, dependency version, data volume | a lead, not evidence, whatever the commit distance says |
| **Unnamed** | the field is missing from a report that must have one | a lead, not evidence, and say the header was incomplete |

A report can be Current on the commit and Changed on the environment. Take the weaker of the
two. A contract run against staging says nothing about production where the two differ.

**The other two dimensions are exempt, and grading them Unnamed is a mistake this skill has to
name.** Neither sibling has a deployment environment to record, so a missing row is correct
rather than incomplete:

| Dimension | Why it is exempt | Read instead |
| --- | --- | --- |
| Proven seams | `integration-test` starts its own containers, so there is no environment to match — the containers *are* the environment, and they are named in its **Harness** row | the **Harness** row against production's own versions. The 🟡 Thin band in step 4 already covers a container version behind production, so this is a grade, not a weight |
| Exposure | `security-compliance` reads the code for three of its four scan kinds and needs no running system for them | its **DAST** row, and only for the live half. A report with no DAST row ran no DAST, which step 4 already grades 🟡 Thin as a scan kind that did not run — never Unproven for a missing environment |

Every sibling writes "dirty working tree" into its header when the tree was dirty. That note
means the run covered code the commit does not hold, so compare against the working tree
instead: run `git status --porcelain -- <the report's scope>` and rate the report **Current**
when nothing in its scope has been touched since, **Stale** when something has.

Scope matters as much as age. A contract report on `/orders` says nothing about `/payments`,
however fresh. Record what each report covered and what it left out.

**Done when:** every report carries a commit state and its commit distance; the three reports
that run against a deployed instance each carry an environment state read from that sibling's
own field, and the weaker of the two states is the one carried into step 4; the integration and
security reports are recorded as exempt rather than Unnamed; every dirty-tree report was rated
against uncommitted changes in its own scope rather than discarded; and every gap between a
report's scope and the system you were asked about is written down.

## 3. Judge relevance, then settle the gaps

Two questions decide this, and the scope settles most of it before the project's shape is read.

**What is the scope you were asked about?** A deployed system, a service, or one module:

| Measured against | Dimensions | At module scope |
| --- | --- | --- |
| the code | the static half of exposure | **applies** — analyzers and secret scanners take a path |
| the suite, against real collaborators | proven seams | **applies** where that path opens a connection of its own |
| the running system | promised behaviour, resilience, headroom, the live half of exposure | **out of scope** — each is a property of a deployed whole, and no report about one folder can exist |

Say that rather than grading them unproven. An unproven grade reads as work somebody skipped;
this is work nobody could have done at the scope they gave you. It is the most common mistake
with this skill — somebody points it at a folder and gets four unproven rows that read as
failure.

**Then read the project's shape** from its manifest, entry points, and what it ships:

| The project | Applies | Does not apply |
| --- | --- | --- |
| A service with an API | all five | — |
| A service with no published contract | all five — `/contract-test` derives one from the routes | — |
| A CLI or batch job | exposure always; proven seams and resilience once it touches a database, queue, or bucket; headroom once throughput is something anybody waits on | promised behaviour, unless it publishes an API |
| A library or package | exposure — its own code and dependencies | promised behaviour, serving no API; proven seams, opening no connection of its own; resilience and headroom, which need a running system |
| A front end | promised behaviour against the API it consumes, resilience against that API being down or slow, exposure | proven seams, where every collaborator is that one API; headroom, which belongs to the API |

Exposure is in every row: every project has code, and code has dependencies. It is never *not
applicable*. Where nothing is deployed it is graded on its static half alone, and says so.

Then give every dimension one relevance:

- **Applies** — the surface exists, so an unproven grade is a real gap.
- **Out of scope** — the surface exists but not in this slice. It leaves the counts, and the
  report names the scope rather than the surface: widening the scope brings it straight back,
  and a missing surface never does.
- **Not applicable** — no such surface. It leaves the counts entirely, and the report says which
  surface is missing so the reader can disagree.
- **Deferred** — the surface exists and the team decided not to prove it before this release.
  **Never record this as *not applicable*.** Name the person and the date; it stays in the
  unproven count.

There is no *by choice* here. A team can decide not to write a spec and nothing about the code
changes; a team that decides not to test resilience still has whatever resilience it has,
unmeasured.

Where an applicable dimension is unproven, say what it waits on rather than what is missing:

| Precondition | Met when | The dimensions |
| --- | --- | --- |
| a build | the project compiles | the static half of exposure |
| containers you can start | Docker is available | proven seams |
| a running instance you can point at | there is one, and you know its URL | promised behaviour, the live half of exposure |
| an instance you may load, and a peak figure somebody will defend | you have the environment and the number | headroom |
| an instance you may break, a hard stop, and a steady state | you have the environment, the permission, and metrics saying what "serving people" means | resilience |

That column is the whole difficulty of this phase. None of these is blocked on a suite or on
taste — they are blocked on an environment and on permission. Say which, per dimension: "we need
an environment we are allowed to break" is a request a team can act on, "resilience is unproven"
is not.

Then put the gaps to the user in **one** question. **Rows only for the ones whose precondition
is met**, each with its relevance, command, cost, and what a skip costs. Mark exactly one
**← start here**: the cheapest, a defect-finder winning a tie. Below, a service with staging and
Docker but no environment anybody may break:

| Dimension | Relevance | State | To fill it | Costs | Skipping it means |
| --- | --- | --- | --- | --- | --- |
| Exposure | applies | no report | `/security-compliance` ← start here | under an hour | a committed secret or a reachable flaw stays live |
| Promised behaviour | applies | no report | `/contract-test` | under an hour | callers break on a release nothing in CI flagged |
| Proven seams | applies | stale, 31 commits behind | `/integration-test` | an afternoon or more | every green test talks to a mock, and no mock has met the real database |
| Headroom | applies | no report | `/stress-test` | an afternoon or more | nobody knows what traffic it takes before it stops keeping up |

**The rest is one line, not rows.** Name each and what it waits for, and ask nothing:
"Resilience waits on an instance you are allowed to break, a hard stop, and a steady state
measured before anything is broken."

Not applicable and out of scope dimensions stay out of the question entirely — they belong in
the report, where nobody has to decide anything about them.

The siblings are the user's to run; none fires on its own. Hand over the commands they picked,
then they call `/release-quality` again with the fresh reports on disk. A previous report's own
duration is the best time estimate you have.

A dimension the user skips is **unproven**, exactly like one never run. Record it as deferred
with the decision and who made it.

**Done when:** the scope is stated and every dimension carries a relevance with the surface, the
scope, or the deferral behind it; every applicable unproven one names the precondition it waits
on; the question held rows only for dimensions whose precondition is met, with exactly one
marked **start here** and the rest named in a line; and where the user asked for a signal to be
filled they have the exact command.

## 4. Read each dimension

Read each applicable dimension from its report:

| Dimension | Read from |
| --- | --- |
| **Promised behaviour** | contract report — contract coverage, conformance, P1 drift |
| **Proven seams** | integration report — seam coverage, hermetic verdict, unproven seams |
| **Resilience** | fault injection report — hypothesis pass rate, recovery verdict, blast radius per weakness |
| **Headroom** | stress report — the knee, headroom against the expected peak, the soak verdict, what gave first |
| **Exposure** | security report — P1 count, reachable CVEs, unrotated secrets, OWASP gaps |

Grade each. Every band is exhaustive: read top down and take the first that matches, so no
combination of results leaves you inventing a grade.

| Grade | Promised behaviour | Proven seams | Resilience | Headroom | Exposure |
| --- | --- | --- | --- | --- | --- |
| 🔴 **Fragile** | any P1 breaking drift, or contract coverage < 50% | the hermetic checks failed, or a seam handling money, permissions, or data writes is unproven, or seam coverage < 50% | any experiment that did not recover, or a dependency handling money or data writes that broke outright, or a hypothesis pass rate < 50% | headroom < 1 — it cannot serve today's peak — or the soak run failed, or throughput collapses past the knee | any P1 — a reachable flaw, or a secret not yet rotated |
| 🟡 **Thin** | any P2 divergent drift, or contract coverage 50–79%, or a derived contract | seam coverage 50–79%, or a container version behind production | any unplanned degradation or collateral damage, or a pass rate 50–79%, or a run covering only some of the ranked dependencies | headroom 1–2×, or a shape that did not run, or a closed-model run | any P2, or a scan kind that did not run, or an OWASP category nothing checked |
| 🟢 **Sound** | no P1 or P2 drift, contract coverage ≥ 80% | seam coverage ≥ 80%, hermetic passed, no unproven seam in the top rank | pass rate ≥ 80%, every experiment back in band inside its hard stop, no unplanned degradation and no collateral | headroom ≥ 2×, soak passed, all five shapes run under an open model | no P1 or P2, all four scan kinds ran, every OWASP category checked |
| ⚫ **Unproven** | no usable report | no usable report | no usable report | no usable report | no usable report |

Five results in that table override the numbers beside them, whatever those numbers say:

| Result | What it forces | Why |
| --- | --- | --- |
| A failed hermetic check | proven seams Fragile | a green that depends on test order, or on data the last run left behind, is evidence of nothing |
| An experiment that never recovered | resilience Fragile | a fault ends; surviving nine of ten counts for nothing against the tenth that needs a human to restart it |
| A **derived** contract | promised behaviour capped at Thin | it was written from the implementation, so the two agree by construction. A reviewed contract lifts the ceiling |
| A **closed-model** run | headroom capped at Thin | the generator stopped sending while the system stalled, so those percentiles describe a system asked to do less exactly when it was struggling |
| An environment rated **Changed** or **Unnamed** in step 2 | that dimension **Unproven** | the numbers describe a system that is not the one being released, and a number from the wrong environment is worse than no number, because it reads as evidence. **Only promised behaviour, resilience, and headroom can be forced this way** — proven seams and exposure carry no environment field, so this row never fires on them |

These bands are a default. Where the project has its own gates — an SLO, an error budget, a
contract-drift policy, a published peak — those are the project's own standard and they win.
Say in the report which you used. Headroom especially: the default 2× is a rule of thumb, and a
team with a real peak figure and a real growth rate has a better one.

The direction matters more than the digit. A dimension that fell since the last report is worth
more of the reader's attention than one sitting a point below a band.

**Done when:** every dimension carries a grade and the numbers behind it, every grade drawn
from a project gate rather than the default band says so, and every dimension whose environment
did not match is Unproven rather than graded.

## 5. Cross-read the signals

This is the step no single report can do, and the reason to read them together. A pair of
signals often says something neither says alone:

| The pair | What it means |
| --- | --- |
| Proven seams, resilience unproven | the code works against a real database and nobody has asked what it does when that database refuses a connection. Seam tests prove the crossing, never the loss |
| Thin headroom, unproven resilience | it already runs close to its limit and nobody has asked what a slow dependency does to it. In practice overload and failure arrive together |
| Sound headroom, seams mocked | the load never reached the real database, so the knee measured is the stub's knee rather than the system's |
| Low contract coverage, high conformance | the clean result covers a fraction of the API. Most of the promise has never been tested at all |
| A P1 exposure finding on an endpoint that also drifts | the endpoint is both reachable and wrong. Whichever gets fixed first, the other is still live on the same URL |
| Unproven seams in the highest-churn module | the code changing fastest is the code whose collaborators are least tested. Mocks go stale silently, and this is where they are staling |
| Breaking contract drift and an unproven seam on the same dependency | the promise broke at the edge nobody has tested at all. The drift is what you can see of it |
| Sound resilience, unproven headroom | it recovers from a broken dependency at whatever load the experiments ran at, which was not peak. Recovery under load is a different question and nobody has asked it |
| An experiment that recovered slowly, headroom under 2× | the recovery window and the peak window overlap. A fault during peak does not get the slack the experiment had |
| A reachable CVE in a dependency the seam tests never start | the vulnerable path is both live and untested, so the upgrade that fixes it lands with nothing watching |
| Every dimension unproven but one | there is no verdict here yet, only one number |
| All five Sound | the strongest shape available at this phase. Say so plainly, then say what it still does not cover |

### If the other phases have reports on disk

Do not grade them. Read them for these pairs only, and label each one as crossing a phase
boundary so nobody mistakes it for a dimension of this report:

| The pair | What it means |
| --- | --- |
| Green suite, breaking contract drift (`bdd-report-`, `coverage-report-`) | the tests check the code against itself and never against the published promise. Consumers are broken while CI stays green |
| High coverage, seams mocked (`coverage-report-`) | the covered lines talk to mocks, so the coverage number describes code that has never met a real database |
| High coverage on an operation that drifts (`coverage-report-`) | well tested inside, wrong at the boundary. The tests encode what the code does, not what the contract says it does |
| Green suite, an experiment that never recovered (`bdd-report-`) | every test starts from a healthy system and leaves one behind, so nothing in the suite can see a system that does not come back |
| High coverage, a dependency that broke outright (`coverage-report-`) | the covered line calls out and waits forever. Coverage counts the call, not the timeout missing from it |
| Reachable flaw in code with no tests (`coverage-report-`) | nothing would catch the fix breaking it, so the flaw is both live and awkward to close |
| Clean static analysis, P1 exposure (`static-analysis-report-`) | the code reads well and something reachable is still open. Tidy code is not safe code |

**Done when:** every pair in the first table that both its signals support has been checked,
each one that fires is written up with its two numbers, and any cross-phase pair that fired is
marked as such.

## 6. Give the verdict

One verdict for the system, by these rules, in this order. A dimension marked **not applicable**
or **out of scope** in step 3 is outside every count here, so a library is judged on the one
dimension it has and a service on all five:

1. Two or more applicable dimensions unproven → **Unproven**. One dimension is a number, not an
   assessment.
2. Otherwise the verdict is the **worst** grade any measured dimension carries. Never the
   average, never the majority.
3. State the count beside it, always, out of the number that apply: "Sound, 1 of 5 applicable
   dimensions unproven". Then name what was set aside and why — "1 does not apply: consumes one
   API, so every collaborator is that API and there are no seams of its own to prove", "3 out of
   scope: you asked about `src/domain/`, and these describe the deployed system, so exposure is
   graded on its static half alone" — so the reader sees dimensions that were weighed rather
   than dimensions that were forgotten.

Then write the verdict out in two sentences: what the system is, and the one thing that most
needs attention. Lead with the dimension that set the floor, because that is the dimension that
decided the verdict.

**Then answer the question this skill exists for, in one line: is this safe to release?** A
grade is not an answer. Say it plainly:

| Verdict | The release line |
| --- | --- |
| 🟢 Sound, nothing unproven | **Ready.** Every applicable dimension measured on this environment, none below band |
| 🟡 Thin | **Ready with known limits** — name each limit and who accepted it. A 1.6× headroom is releasable if somebody has looked at the peak figure and said so |
| 🔴 Fragile | **Not ready.** Name the one finding that says so. A single unrotated secret is enough |
| ⚫ Unproven | **Unknown.** Not "probably fine" — nobody has measured it. Name the two or more dimensions and the precondition each waits on |

Never soften ⚫ Unproven into 🟡 Thin because the system has run in production for a year
without incident. That is a year of no *observed* incidents at the loads and failures that
happened to occur — the argument that precedes the first one.

An **Unproven** verdict names what each unproven dimension waits on, because those preconditions
are the real work. "Unproven — waiting on a staging environment nobody may break" is a request to
a platform team; "Unproven" alone is a shrug.

Where a previous report sits beside this one, say which way the verdict moved and which dimension
moved it — and whether the environment was the same. A headroom number that fell because the
database shrank is not a regression in the code. **A verdict can also fall because the standard
widened**: when the previous report graded fewer dimensions and the new verdict is worse only
because of one it never had, say so in the same breath, or the reader goes hunting for the commit
that broke it.

**Done when:** the verdict follows the three rules, the dimension that set the floor is named,
the unproven count is stated out of the number that apply, everything set aside names whether
it was scope or surface, the release line is stated plainly, an unproven verdict names the
precondition each unproven dimension waits on, the two phases outside this skill are named as
not covered, and a verdict that fell only because the previous report graded fewer dimensions
says so.

## 7. Chart the next moves

Name the starting position, then order the moves it calls for.

| Starting position | Test |
| --- | --- |
| **Unproven** | no dimension measured on this environment |
| **Thin** | some measured, and one or more grade Thin or Fragile |
| **Proven** | every applicable dimension measured on this environment, none Fragile |

### Which dimensions to cover next

**One move first, the rest behind it.** Name one recommendation, put the others in an ordered
list under it, and say that calling `/release-quality` again picks the next.

Every recommendation names the dimension, the command, the cost, **and what it needs before it
can run** — that last column matters more here than in the other two phases, because four of the
five are blocked on an environment rather than on effort.

| Cost | Skills |
| --- | --- |
| **under an hour** | `/security-compliance`, `/contract-test` |
| **an afternoon or more** | `/integration-test`, `/stress-test`, `/fault-injection-test` |

Two rules break a tie: a defect-finder beats a measurement, and something users are hitting
today beats a hypothetical.

### From unproven

**Ordered by precondition weight, cheapest favour first.** Every step needs something from
somebody else — a URL, a Docker daemon, a load environment, permission to break things.

1. **`/security-compliance`.** Needs only a build, under an hour, and finds defects rather than
   producing a number. **A committed secret is live from the moment it lands until the key is
   rotated**, and every other move here is measurement — put the one defect-finder first.
2. **`/contract-test`.** Needs a running instance and no suite, under an hour, and cannot hurt
   anything — it sends requests and reads the replies.

   Where nothing is published it derives a contract from the routes. That is capped at 🟡 Thin
   because contract and implementation then agree by construction, but the derived contract is
   itself the deliverable: review it once and every later run grades against a real promise.
3. **`/integration-test`.** Brings its own tests and containers, so it needs Docker and nothing
   else — no suite, no environment, no permission. It fills proven seams, which nothing else
   here reaches: however green a suite is, no mock in it has met a real database.
4. **`/stress-test`.** Needs two things this ladder has not asked for: an environment that can
   take the load, and a peak figure somebody will defend. Get the figure first — a load run
   against no target produces a knee and no verdict. It comes before move 5, which measures
   against the normal load it establishes.
5. **`/fault-injection-test`.** Last, the only one that breaks things on purpose. Needs an
   environment you are *allowed* to break, a hard stop, and a steady state measured before
   anything is broken. Move 4 gives you the load.

**The verdict stays ⚫ Unproven until move 4 lands.** Rule 1 holds it there while two or more
dimensions are unproven, and this ladder fills one per move: four unproven after move 1, three
after 2, two after 3. Move 4 is the first leaving only one. Say that up front, with the count,
or a team two moves in reads the third report as a failure of the skill rather than as
arithmetic.

Say plainly which moves are blocked and on what. On most projects 4 and 5 wait on an environment
nobody has yet: three moves you can do this week, two that need a platform conversation. Then
hand over move 1 alone.

### From thin

Order every move across every report by these three:

1. **Exposure findings, and anything already broken** — a committed secret, a reachable CVE, a
   breaking drift on a live endpoint. A defect outranks a number about defects, and each is
   costing somebody something now.
2. **The dimension that set the floor.** It decided the verdict, so it changes the verdict.
3. **Whatever the highest-traffic path touches, inside each.** Volume decides blast radius here,
   the way churn decides it during development.

### From proven

The siblings' own P1 lists, merged and ordered by those three rules. Add the gates each sibling
proposed — the contract run judged on new drift, the integration suite in CI, the cheap fault
experiments on pull requests, the load smoke and regression gate, the four security gates —
because a proven system with no gate drifts back to thin, and silently, since nobody watches a
deployed system the way they watch a diff.

Add a second: **re-run before the next release, not on a schedule.** These five describe an
environment as much as a codebase, and what invalidates them is a deploy, a dependency upgrade,
or an instance resize — not the passage of a month.

Close with the pointer to the other two phases: `/code-quality`, `/visual-quality`.

**Done when:** the starting position is named, exactly one opening move is named and it is
either an outright defect or the cheapest dimension whose precondition is met, every move names
what it needs before it can run, every applicable unproven dimension appears with its cost and
what it would tell them, blocked moves are named as blocked with the thing they wait on, and the
two other phases are named with their commands.

## 8. Write the report

Header: `date '+%Y-%m-%d-%H%M%S'` for the timestamp, `git rev-parse --short HEAD` for the
commit, a note if the working tree is dirty, **and the environment every report ran against** —
this phase's reports are worthless without it.

Write to `<module>/.reports/release-quality-report-<timestamp>.md`, where `<module>` is the
nearest directory at or above the module assessed holding the project's manifest
(`package.json`, `go.mod`, `pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`,
`Gemfile`, a `*.csproj`). An assessment spanning several modules writes to the repository root.
Create the folder if missing and add `.reports/` to the root `.gitignore` if nothing there
covers it. One file per run; never overwrite an older one.

Every source report is named and linked, with its commit distance and its environment. A verdict
whose evidence a reader cannot open is a verdict they have to take on trust.

Use the tables in [`report.md`](report.md) — every section of that shape, in that order. The
prose left over is the verdict, the release line, and one sentence per cross-read pair.

Then tell the user four things and stop: the file path, the release line with the verdict and
its unproven count, the one next move with what it costs and what it needs, and that calling
`/release-quality` again afterwards picks the one after it.

**Done when:** the report sits in the module's `.reports` folder, `.reports/` is git-ignored,
no older report was overwritten, and it holds every section of [`report.md`](report.md), with no
dimension, cross-read pair, or step 7 move left out.
