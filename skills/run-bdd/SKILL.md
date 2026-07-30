---
name: run-bdd
description: >
  Run the project's `.feature` files and report each scenario as passed, failed,
  pending, blocked, or unwired, with captured output as evidence and a suggested
  fix under every failure.
disable-model-invocation: true
---

Take the `.feature` files as the spec, exercise the behaviours they describe, and report
each one against **evidence** — the output you actually captured. A verdict without
evidence is a guess wearing a green tick.

## This skill reports

Steps 1 to 6 run the scenarios and write up what happened. The product and the spec both
stay exactly as they are. That report is the whole deliverable.

Steps 7 and 8 run only on a **fix signal**: "fix them", "make them pass", "fix the
failures", "go ahead". The step 6 report is the *before*, so it is written on a fix run
too, and written before any code is touched.

## 1. Collect the scenarios

Find the `.feature` files in scope — the ones the user named, or every one in the
repository. They sit under `features/`, at the root in a single-module project and under
each module in a monorepo, so search for the extension rather than one directory. Read
them.

**Done when:** you have every scenario to run, each with its `Given` context, its `When`
action, and the `Then` outcomes you must check. A `Scenario Outline` contributes one entry
per `Examples` row.

## 2. Find the runner

Find the command the project already uses — `package.json` scripts, `Makefile`, `Rakefile`,
CI config, or the test config for `cucumber-js`, `playwright-bdd`, `pytest-bdd`, `behave`,
`godog`, `cucumber-jvm`, Ruby `cucumber`, or `reqnroll`/SpecFlow — and the step definitions
behind it. The framework table in `wire-bdd` step 2 lists where each keeps its glue.

Read the runner's own docs for current flags — names drift between versions, and a command
written from memory fails in ways that look like broken glue.

Scenarios with no step definition are **unwired**. They belong in the report as unwired,
and writing their glue is `wire-bdd`'s job — tell the user to call `/wire-bdd` when unwired
scenarios show up.

**Done when:** you have the exact command to run, and the list of scenarios it will leave
unwired.

## 3. Check the preconditions

Note any scenario the run cannot satisfy — seed data you lack, an external service that is
down, a missing credential — and settle it with the user before running.

**Done when:** the environment the runner needs is up, or the scenarios it blocks are named.

## 4. Execute and capture

Run the command. Capture the full output — stdout, stderr, exit code, and the runner's own
report file if it writes one.

**Done when:** every scenario in scope has captured output attached, or is recorded as
blocked or unwired. Silence is not a pass — a scenario with no output is unrun, not green.

## 5. Verify and suggest the fix

Compare, per scenario, what the `Then` steps demand against what you captured. A scenario is
**green** only when every `Then` outcome matched observed output. Anything else splits four
ways:

- **Failed** — the behaviour ran and produced the wrong result. The product is wrong, or the
  spec is. The only bucket that means a regression.
- **Pending** — a step is marked pending because the product has no code behind it yet.
  Known work, not a defect, so it stays out of the failure count.
- **Blocked** — setup never completed, so the behaviour never ran.
- **Unwired** — no step definition, so the scenario was never executable.

For each failed scenario, name the step it broke on, quote expected against observed, and
give your reading of the cause. Then say what would fix it, and settle which of two kinds of
failure it is:

- **Product fix** — the spec is right and the code is wrong. Name the file, the function,
  and the change. This is what a fix run acts on.
- **Spec question** — the code may be right and the scenario may describe behaviour nobody
  intended. Quote both sides and ask. Only the user can settle which one moves, so the
  answer belongs in the report, not in a diff.

Every other bucket gets a suggestion too, and each points somewhere different:

| Bucket | The fix, and whose job it is |
| --- | --- |
| **Pending** | the product owes a capability. Name what it owes, and treat building it as work to plan rather than a fix to apply |
| **Blocked** | name the missing fixture, seed row, service, or credential, and what would supply it |
| **Unwired** | `/wire-bdd` writes the glue. Name the missing step and hand it over |

The `.feature` files are the spec, so they stay as they are. A red scenario turned green by
editing its `Then` step is a spec bent to fit a bug, and the next reader has no way to tell
that happened.

**Done when:** every scenario carries a verdict backed by captured output, every failed one
names its broken step, its expected-vs-observed, a cause, and a suggested fix, and every
failed one is marked either product fix or spec question.

## 6. Write the report

Header: the timestamp from `date '+%Y-%m-%d-%H%M%S'`, the commit from `git rev-parse --short
HEAD` — a report naming the wrong commit sends a later bisect to the wrong place — and a
note if the working tree is dirty, since the run then covers code that commit does not hold.

Write to `<module>/.reports/bdd-report-<timestamp>.md`. `<module>` is the nearest directory
at or above the feature files holding the project's manifest (`package.json`, `go.mod`,
`pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`, `*.csproj`); a run
spanning several writes to the repository root. Create the folder if missing, add
`.reports/` to the root `.gitignore` if nothing there covers it, one file per run, never
overwrite an older one.

Write this report on a fix run too, and *before* you touch any code. This is the before;
without it there is nothing to compare against, and a count you remember is not a count you
can show.

Check one thing about the runner and put it in the report: **does an undefined or pending
scenario fail the build, or pass quietly?** A green CI run over three scenarios that never
executed is the lie this skill exists to catch. Read the runner's own docs, because the
answer differs and some already do the right thing:

| Runner | How undefined and pending are treated |
| --- | --- |
| `cucumber-js` | strict **by default** — undefined and pending already fail. Check for a `--no-strict` or `strict: false` already set in the config or profile |
| `cucumber-jvm` | undefined steps fail the scenario by default. Check for a lenient `@CucumberOptions`/plugin setup |
| `behave` | `--strict`, or `strict = true` under `[behave]` in `behave.ini`/`setup.cfg` |
| `godog` | `--strict` |
| `pytest-bdd` | **no** strict setting. Undefined steps raise a collection error, so they already fail; pending is whatever your step code does. The gate is a `--strict-markers`-style pytest config plus keeping steps from silently passing |
| `Reqnroll` / SpecFlow | undefined steps fail as inconclusive. Check whether the CI step treats inconclusive as a pass |

So recommend either turning strictness on, or — where it is already on — confirming nothing
has turned it off. Both go in the report as the exact file and setting, and the config stays
untouched unless a fix signal comes.

Use the shape below and put the data in tables — counts, features, scenarios, steps,
buckets, and outcomes belong in cells where they can be scanned. The prose left over is the
cause of a failure, the spec question, and the captured output in its code block.

Then tell the user the file path, the counts, and the single most important failure. On a
report-only run, say the report is all this run changed, so they can ask for the failures to
be fixed next.

**Done when:** the report sits in the module's `.reports` folder, `.reports/` is git-ignored,
no older report was overwritten, every scenario from step 1 appears with its verdict, every
non-green scenario carries its evidence and suggested fix, and the strict-mode gate is
recommended.

## 7. Fix the failures — on a fix signal

Without the signal the work finished at step 6. The signal reaches two of the five buckets;
the other three each need something a fix run cannot give:

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

Step 3 is the one that matters. A scenario made green by a change that reddens another has
moved the failure, not fixed it.

Then apply the strict-mode gate from step 6.

The `.feature` files stay as they are throughout. Where the only way to make a scenario pass
is to change what it demands, that scenario is a spec question — move it to that bucket and
leave it for the user.

**Done when:** every failed scenario marked product fix is green with the whole suite green,
or deferred with a stated reason; every blocked scenario is either running or still blocked
with its reason recorded; and the spec questions, pending scenarios, and unwired scenarios
are untouched and still listed. None are simply unmentioned.

## 8. Write the after report — on a fix signal

Re-run the step 2 command over the same scenarios. Fresh timestamp, second file in the same
`.reports` folder; the step 6 report stays untouched, so anyone can read the before for
themselves.

Lead the body with a "What moved" section naming the step 6 file, and give each of these its
own table:

- the counts per bucket, before and after;
- what happened to each non-green scenario — fixed, unblocked, deferred, left as a spec
  question, still failing;
- any scenario green before and red now. That is a regression the fixes caused, and the
  first thing the reader needs.

Then tell the user both file paths, the two sets of counts, and what is still red.

**Done when:** both reports sit side by side, the after report names the before file and
states the change per bucket, every non-green scenario from step 6 appears with its outcome,
and the full suite result is recorded at the end.

---

# Report shape

A TypeScript after-report. The tables, columns, and buckets are what transfers — swap in
your own runner, paths, and step syntax. Every table here is shown with one data row; a real
report lists them all.

````markdown
# BDD Test Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Command** | `<the command you ran>` |
| **Commit** | `<short sha>` (dirty working tree) |
| **Scope** | `features/` — 6 files, 20 scenarios |
| **Before** | [`bdd-report-2026-07-30-091412.md`](./bdd-report-2026-07-30-091412.md) |

## What moved

Against the before report, taken before any code was touched.

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

One outcome per scenario, so the rows sum to the total. The spec-question scenario is the
single red left in the Results table — counted on its own row, not twice.

**Green before, red now:** none. The total rose by one because a `Scenario Outline` gained an
`Examples` row while the fixes were made.

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

**Cause:** the decline reason from the gateway is not mapped, so it falls through to the
`unknown` default.

A spec-question failure uses the same table with **Kind** `spec question`, **Suggested fix**
`none until the question below is settled`, and **Outcome** `❓ left as a spec question`.

---

## ❓ Spec questions

| Feature · scenario | The spec says | The code does | Question |
| --- | --- | --- | --- |
| `checkout.feature` › Customer pays with a lapsed subscription | order is `held` for review | order is `rejected` | should a lapsed subscription hold the order, or reject it? |

This needs an answer before code or spec moves, and nothing was changed for it. Only
scenarios whose **Kind** is `spec question` appear here — a scenario settled as a product fix
appears once, in the Failures section.

---

## 🔵 Pending

| Feature | Scenario | Pending step | The product owes | Outcome |
| --- | --- | --- | --- | --- |
| `refunds.feature` | Partial refund of a shipped order | `When the agent refunds 25.00 of the order` | a partial-refund path in `RefundService` | ⏸️ work to plan |

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

Run `/wire-bdd` to write the glue. Until then they are not executable, so they are neither
passing nor failing.

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

`cucumber-js` is strict by default, so this project has explicitly turned it off. That is why
the last CI run exited 0 with 3 unwired and 2 pending scenarios — green over 5 scenarios that
never ran. Removing the override is the whole fix.
````

Every scenario appears in exactly one bucket. Drop any empty section, keep the summary table,
and lead the body with the reds.

The before report is the same shape, shorter: no "Before" row, no "What moved", no "Outcome"
rows or columns, and the gate row reading "not applied".
