---
name: run-bdd
description: >
  Run the project's `.feature` files and report each scenario as passed, failed,
  pending, blocked, or unwired, with captured output as evidence and a suggested
  fix under every failure.
disable-model-invocation: true
---

Take the `.feature` files as the spec, exercise the behaviours they describe,
and report each one against **evidence** — the output you actually captured.
A verdict without evidence is a guess wearing a green tick.

## This skill reports

It runs the scenarios and writes up what happened. The product and the spec both
stay exactly as they are. A report the user did not ask to act on is the whole
deliverable — run steps 1 to 6 and hand it over.

Fix the failures only when the user gives a **fix signal**: "fix them", "make
them pass", "fix the failures", "go ahead". Steps 7 and 8 then follow, and they
end in a second report that sits beside the first. The step 6 report is the
before, so it gets written on a fix run too, and it gets written before any code
is touched.

## 1. Collect the scenarios

Find the `.feature` files in scope — the ones the user named, or every one in
the repository. They sit under `features/`, at the root in a single-module
project and under each module in a monorepo, so search for the extension rather
than one directory. Read them.

**Done when:** you have a list of every scenario to run, each with its `Given`
context, its `When` action, and the `Then` outcomes you must check. A
`Scenario Outline` contributes one entry per `Examples` row.

## 2. Find the runner

Find the command the project already uses — `package.json` scripts, `Makefile`,
`Rakefile`, CI config, the test config for `cucumber-js`, `playwright-bdd`,
`pytest-bdd`, `behave`, `godog`, `cucumber-jvm`, Ruby `cucumber`, or
`reqnroll`/SpecFlow — and the step definitions behind it. The framework table in
`wire-bdd` step 2 lists where each one keeps its glue.

Read the runner's own documentation for its current flags. Names drift between
versions, and a command written from memory fails in ways that look like broken
glue.

Scenarios with no step definition are **unwired**. They belong in the report as
unwired, and writing their glue is the `wire-bdd` skill's job — tell the user to
call `/wire-bdd` when unwired scenarios show up.

**Done when:** you have the exact command to run, and the list of scenarios it
will leave unwired.

## 3. Check the preconditions

Note any scenario the run cannot satisfy — seed data you lack, an external
service that is down, a missing credential — and settle it with the user before
running.

**Done when:** the environment the runner needs is up, or the scenarios it
blocks are named.

## 4. Execute and capture

Run the command. Capture the full output — stdout, stderr, exit code, and the
runner's own report file if it writes one.

**Done when:** every scenario in scope has captured output attached to it, or is
recorded as blocked or unwired. Silence is not a pass — a scenario with no
output is unrun, not green.

## 5. Verify and suggest the fix

Compare, per scenario, what the `Then` steps demand against what you captured.
A scenario is **green** only when every one of its `Then` outcomes matched
observed output. Anything else splits four ways:

- **Failed** — the behaviour ran and produced the wrong result. The product is
  wrong, or the spec is. This is the only bucket that means a regression.
- **Pending** — a step is marked pending because the product has no code behind
  it yet. Known work, not a defect, so it stays out of the failure count.
- **Blocked** — setup never completed, so the behaviour never ran.
- **Unwired** — no step definition, so the scenario was never executable.

For each failed scenario, name the step it broke on, quote the expected value and
the observed value side by side, and give your reading of the cause.

Then say what would fix it, and settle which of two kinds of failure it is:

- **Product fix** — the spec is right and the code is wrong. Name the file, the
  function, and the change. This is what a fix run acts on.
- **Spec question** — the code may be right and the scenario may describe
  behaviour nobody intended. Quote both sides and ask. Only the user can settle
  which one moves, so the answer belongs in the report, not in a diff.

Every other bucket gets a suggestion too, and each one points somewhere
different:

| Bucket | The fix, and whose job it is |
| --- | --- |
| **Pending** | the product owes a capability. Name what it owes, and treat building it as work to plan rather than a fix to apply |
| **Blocked** | name the missing fixture, seed row, service, or credential, and what would supply it |
| **Unwired** | `/wire-bdd` writes the glue. Name the missing step and hand it over |

The `.feature` files are the spec, so they stay as they are. A red scenario
turned green by editing its `Then` step is a spec bent to fit a bug, and the
next reader has no way to tell that happened.

**Done when:** every scenario carries a verdict backed by the output you
captured, every failed one names its broken step, its expected-vs-observed, a
cause, and a suggested fix, and every failed one is marked either product fix or
spec question.

## 6. Write the report

Run `date '+%Y-%m-%d-%H%M%S'` for the timestamp and `git rev-parse --short HEAD`
for the commit — both go in the report header, and a report that names the wrong
commit sends a later bisect to the wrong place. Note in the header when the
working tree is dirty, since the run then covers code that commit does not hold.

Write the report to `<module>/.reports/bdd-report-<timestamp>.md`, where
`<module>` is the root of the module holding the feature files — the nearest
directory at or above them that holds the project's manifest (`package.json`,
`go.mod`, `pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`,
a `*.csproj`). A run spanning several modules writes to the repository root.

Create the folder if it is missing, and keep it out of version control: add
`.reports/` to the repository's root `.gitignore` when nothing there covers it
already. One file per run, so past runs stay readable and two runs can be
compared.

Write this report even on a fix run, and write it *before* you touch any code.
This is the before. Without it there is nothing to compare the after against,
and a count you remember is not a count you can show.

Check one thing about the runner and put it in the report: does an undefined or
pending scenario fail the build, or does it pass quietly? A green CI run over
three scenarios that never executed is the lie this skill exists to catch.

Read the runner's own documentation for how it handles this, because the answer
differs and some runners already do the right thing:

| Runner | How undefined and pending are treated |
| --- | --- |
| `cucumber-js` | strict **by default** — undefined and pending already fail. What to check for is a `--no-strict` or `strict: false` already set in the config or profile |
| `cucumber-jvm` | undefined steps fail the scenario by default. Check for a lenient `@CucumberOptions`/plugin setup |
| `behave` | `--strict`, or `strict = true` under `[behave]` in `behave.ini`/`setup.cfg` |
| `godog` | `--strict` |
| `pytest-bdd` | it has **no** strict setting. Undefined steps raise a collection error, so they already fail; pending is whatever your step code does. The gate here is a `--strict-markers`-style pytest config plus keeping steps from silently passing |
| `Reqnroll` / SpecFlow | undefined steps fail as inconclusive. Check whether the CI step treats inconclusive as a pass |

So recommend either turning strictness on, or — where it is already on —
confirming nothing has turned it off. Both go in the report as the exact file and
setting, and the config stays untouched unless a fix signal comes.

Use the shape below, and put the data in tables. Counts, features, scenarios,
steps, buckets, and outcomes belong in table cells where they can be scanned. The
prose left over is the cause of a failure, the spec question, and the captured
output in its code block.

Then tell the user the file path, the counts, and the single most important
failure. On a report-only run, say that the report is all this run changed, so
they can ask for the failures to be fixed if they want that next.

**Done when:** the report file sits in the module's `.reports` folder, `.reports/`
is ignored by git, no older report was overwritten, every scenario from step 1
appears in it with its verdict, every scenario that is not green carries its
evidence and its suggested fix, and the strict-mode gate is recommended.

## 7. Fix the failures — on a fix signal

Without the signal, the work is finished at step 6. Hand over the report.

The signal reaches two of the five buckets. The other three each need something
a fix run cannot give them:

| Bucket | On a fix signal |
| --- | --- |
| **Failed — product fix** | change the product code so the behaviour matches the spec |
| **Blocked** | supply the missing fixture, seed row, service, or credential |
| **Failed — spec question** | left standing. Only the user can settle which side is wrong, and guessing writes the wrong answer into the code |
| **Pending** | left standing. The product owes a capability, and building it is a piece of work to plan |
| **Unwired** | left to `/wire-bdd`. A scenario with no glue was never executable, so there is nothing here to fix |

Work the product fixes one at a time:

1. Make the change in the product code.
2. Re-run that scenario alone. It goes green.
3. Re-run the whole suite. Every scenario that was green before is still green.

Step 3 is the one that matters. A scenario made green by a change that reddens
another has moved the failure, not fixed it.

Then apply the strict-mode gate from step 6.

The `.feature` files stay as they are throughout. When the only way to make a
scenario pass is to change what it demands, that scenario is a spec question —
move it to that bucket and leave it for the user.

**Done when:** every failed scenario marked product fix is green with the whole
suite green, or deferred with a stated reason; every blocked scenario is either
running or still blocked with its reason recorded; and the spec questions,
pending scenarios, and unwired scenarios are untouched and still listed. None are
simply unmentioned.

## 8. Write the after report — on a fix signal

Re-run the same command from step 2 over the same scenarios. Take a fresh
timestamp and write a second file into the same `.reports` folder. The step 6
report stays where it is, untouched. Two files, so the move is on the record and
anyone can read the before for themselves.

Lead the body with a "What moved" section that names the step 6 file, and give
each of these its own table:

- the counts per bucket, before and after;
- what happened to each non-green scenario — fixed, unblocked, deferred, left as
  a spec question, still failing;
- any scenario that was green before and is red now. That is a regression the
  fixes caused, and it is the first thing the reader needs.

Then tell the user both file paths, the two sets of counts, and what is still red.

**Done when:** both report files exist side by side, the after report names the
before file and states the change per bucket, every non-green scenario from the
step 6 report appears in it with its outcome, and the full suite result is
recorded at the end.

---

# Report shape

The example below is a TypeScript project. The tables, the columns, and the
buckets are what transfers — swap in the runner, the paths, and the step syntax
your project actually uses.

````markdown
# BDD Test Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Command** | `<the command you ran>` |
| **Commit** | `<short sha>` (dirty working tree) |
| **Scope** | `features/` — 6 files, 20 scenarios |
| **Duration** | 2m 18s |
| **Before** | [`bdd-report-2026-07-30-091412.md`](./bdd-report-2026-07-30-091412.md) |

## What moved

Against `bdd-report-2026-07-30-091412.md`, taken before any code was touched.

| Result | Before | After | Change |
| --- | --- | --- | --- |
| 🟢 Passed | 12 | **17** | **+5** |
| 🔴 Failed | 4 | 1 | −3 |
| 🔵 Pending | 2 | 2 | 0 |
| 🟡 Blocked | 1 | 0 | −1 |
| ⚪ Unwired | 3 | 3 | 0 |
| **Total** | **22** | **23** | **+1** |

| Outcome | Scenarios |
| --- | --- |
| 🟢 Fixed in the product | 3 |
| 🔓 Unblocked | 1 |
| ❓ Left as a spec question — still red | 1 |
| ⏸️ Deferred | 0 |
| 🔴 Still failing, no decision needed | 0 |
| **Non-green before** | **5** |

One outcome per scenario, so the rows sum to the total. The spec-question
scenario is the single red left in the Results table — it is counted on its own
row, not twice.

**Green before, red now:** none. **Full suite:** 17 passed, 1 failed, 2 pending,
3 unwired.

The total rose by one because a `Scenario Outline` gained an `Examples` row while
the fixes were made.

## Results

| Result | Count |
| --- | --- |
| 🟢 Passed | 17 |
| 🔴 Failed | 1 |
| 🔵 Pending | 2 |
| 🟡 Blocked | 0 |
| ⚪ Unwired | 3 |
| **Total** | **23** |

## Summary by feature

| Feature | Scenarios | Passed | Failed | Pending | Blocked | Unwired |
| --- | --- | --- | --- | --- | --- | --- |
| `features/checkout.feature` | 6 | 5 | 1 | 0 | 0 | 0 |
| `features/refunds.feature` | 8 | 6 | 0 | 2 | 0 | 0 |
| `features/loyalty.feature` | 9 | 6 | 0 | 0 | 0 | 3 |

---

## 🔴 Failures

### 1. `features/checkout.feature` › Customer pays with an expired card

| | |
| --- | --- |
| **Broke on** | `Then the payment is declined with reason "card expired"` |
| **Expected** | payment status `declined`, reason `card expired` |
| **Observed** | payment status `declined`, reason `unknown` |
| **Kind** | product fix |
| **Suggested fix** | map the gateway's `expired_card` code in `DeclineReason.from()` at `src/payments/decline.ts:31` |
| **Outcome** | 🟢 fixed |

```
<the captured output — stack trace, response body, log lines>
```

**Cause:** the decline reason from the gateway is not mapped, so it falls
through to the `unknown` default.

### 2. `features/checkout.feature` › Customer pays with a lapsed subscription

| | |
| --- | --- |
| **Broke on** | `Then the order is held for review` |
| **Expected** | order status `held` |
| **Observed** | order status `rejected` |
| **Kind** | spec question |
| **Suggested fix** | none until the question below is settled |
| **Outcome** | ❓ left as a spec question |

```
<the captured output>
```

**Cause:** the code rejects outright. Either the scenario is describing a
review step nobody built, or the product is meant to hold and does not.

---

## ❓ Spec questions

| Feature · scenario | The spec says | The code does | Question |
| --- | --- | --- | --- |
| `checkout.feature` › Customer pays with a lapsed subscription | order is `held` for review | order is `rejected` | should a lapsed subscription hold the order, or reject it? |

This needs an answer before code or spec moves, and nothing was changed for it.
It is the one scenario still red in the Results table above.

Only scenarios whose **Kind** is `spec question` appear here. The expired-card
scenario is not among them: it was settled as a product fix and appears once, in
the Failures section.

---

## 🔵 Pending

| Feature | Scenario | Pending step | The product owes | Outcome |
| --- | --- | --- | --- | --- |
| `refunds.feature` | Partial refund of a shipped order | `When the agent refunds 25.00 of the order` | a partial-refund path in `RefundService` | ⏸️ work to plan |

Building these is a piece of work, not a fix. They stay pending.

---

## 🟡 Blocked

| Feature | Scenario | Blocked at | Missing | Suggested fix | Outcome |
| --- | --- | --- | --- | --- | --- |
| `refunds.feature` | Refund a settled order | `Given a settled order exists` | the settlement job runs nightly, so no settled order is in the test data | add a settled order to the seed fixture in `test/fixtures/orders.ts` | 🔓 unblocked |

---

## ⚪ Unwired

| Feature | Scenario | Missing step |
| --- | --- | --- |
| `loyalty.feature` | Points expire after 12 months | `Given the customer earned 500 points on "2025-01-15"` |

Run `/wire-bdd` to write the glue for these. Until then they are not executable,
so they are neither passing nor failing.

---

## 🟢 Passed

| Feature | Scenario |
| --- | --- |
| `features/checkout.feature` | Customer pays with a valid card |

---

## The gate

| Setting | Found | Should be | Where | State |
| --- | --- | --- | --- | --- |
| `strict` | `false` | `true` | `cucumber.json`, `default` profile | not applied |

`cucumber-js` is strict by default, so this project has explicitly turned it off.
That is why the last CI run exited 0 with 3 unwired and 2 pending scenarios —
green over 5 scenarios that never ran. Removing the override is the whole fix.
````

Every scenario appears in exactly one bucket. Drop any section with no entries,
keep the summary table, and lead the body with the reds.

The before report is the same shape, shorter: no "Before" row, no "What moved",
no "Outcome" rows or columns, and the gate row reads "not applied".

On a fix run, the after report adds the **Outcome** row to each failure and the
**Outcome** column to the bucket tables.
