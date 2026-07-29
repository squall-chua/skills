---
name: run-bdd
description: >
  Run the project's `.feature` files as tests and write a rich Markdown report.
disable-model-invocation: true
---

Take the `.feature` files as the spec, exercise the behaviours they describe,
and report each one against **evidence** — the output you actually captured.
A verdict without evidence is a guess wearing a green tick.

## 1. Collect the scenarios

Find the `.feature` files in scope — the ones the user named, or every file
under the project's feature directory. Read them.

**Done when:** you have a list of every scenario to run, each with its `Given`
context, its `When` action, and the `Then` outcomes you must check. A
`Scenario Outline` contributes one entry per `Examples` row.

## 2. Find the runner

Find the command the project already uses — `package.json` scripts, `Makefile`,
`Rakefile`, CI config, the test config for `cucumber-js`, `playwright-bdd`,
`pytest-bdd`, `behave`, `godog`, `cucumber-jvm`, Ruby `cucumber`, or
`reqnroll`/SpecFlow — and the step definitions behind it. The framework table in
`wire-bdd` step 2 lists where each one keeps its glue.

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

## 5. Verify against expected

Compare, per scenario, what the `Then` steps demand against what you captured.
A scenario is **green** only when every one of its `Then` outcomes matched
observed output. Anything else splits four ways:

- **Failed** — the behaviour ran and produced the wrong result. The product is
  wrong, or the spec is. This is the only bucket that means a regression.
- **Pending** — a step is marked pending because the product has no code behind
  it yet. Known work, not a defect, so it stays out of the failure count.
- **Blocked** — setup never completed, so the behaviour never ran.
- **Unwired** — no step definition, so the scenario was never executable.

For each failed scenario, name the step it broke on, quote the expected value
and the observed value side by side, and give your reading of the cause. For
each pending one, name the step and what the product still owes it.

The `.feature` files are the spec, so they stay as they are. A scenario that
fails is a finding for the report, and any scenario you believe specifies the
wrong behaviour goes in the report as a spec question for the user to settle.

**Done when:** every scenario carries a verdict backed by the output you
captured, and every failed one names its broken step, its expected-vs-observed,
and a cause.

## 6. Write the report

Run `date '+%Y-%m-%d-%H%M%S'` for the timestamp and `git rev-parse --short HEAD`
for the commit — both go in the report header, and a report that names the wrong
commit sends a later bisect to the wrong place. Note in the header when the
working tree is dirty, since the run then covers code that commit does not hold.

Write the report to `bdd-report-<timestamp>.md` — in the project's reports or
docs directory, or alongside the feature files. One file per run, so past runs
stay readable and two runs can be compared.

Use the shape below. Then tell the user the file path, the counts, and the
single most important failure.

When an earlier report sits beside the new one, say what moved since it: which
scenarios turned red, and which turned green.

**Done when:** the report file exists, every scenario from step 1 appears in it
with its verdict, and every scenario that is not green carries its evidence.

---

# Report shape

````markdown
# BDD Test Report

**Run:** <YYYY-MM-DD HH:MM:SS> · **Command:** `<the command you ran>` ·
**Commit:** `<short sha>` (dirty working tree)

| Result | Count |
| --- | --- |
| 🟢 Passed | 12 |
| 🔴 Failed | 2 |
| 🔵 Pending | 2 |
| 🟡 Blocked | 1 |
| ⚪ Unwired | 3 |
| **Total** | **20** |

## Summary by feature

| Feature | Passed | Failed | Pending | Blocked | Unwired |
| --- | --- | --- | --- | --- | --- |
| `checkout.feature` | 5 | 1 | 0 | 0 | 0 |

---

## 🔴 Failures

### `checkout.feature` › Customer pays with an expired card

**Broke on:** `Then the payment is declined with reason "card expired"`

| | |
| --- | --- |
| **Expected** | payment status `declined`, reason `card expired` |
| **Observed** | payment status `declined`, reason `unknown` |

```
<the captured output — stack trace, response body, log lines>
```

**Cause:** the decline reason from the gateway is not mapped, so it falls
through to the `unknown` default.

---

## 🔵 Pending

| Feature | Scenario | Pending step | Waiting on |
| --- | --- | --- | --- |
| `refunds.feature` | Partial refund of a shipped order | `When the agent refunds 25.00 of the order` | no partial-refund path in `RefundService` |

---

## 🟡 Blocked

### `refunds.feature` › Refund a settled order

**Blocked at:** `Given a settled order exists` — the settlement job runs
nightly and no settled order exists in the test data.

---

## ⚪ Unwired

| Feature | Scenario | Missing step |
| --- | --- | --- |
| `loyalty.feature` | Points expire after 12 months | `Given the customer earned 500 points on "2025-01-15"` |

Run `/wire-bdd` to write the glue for these.

---

## 🟢 Passed

| Feature | Scenario |
| --- | --- |
| `checkout.feature` | Customer pays with a valid card |

---

## Spec questions

- `checkout.feature` › Customer pays with an expired card expects reason
  `card expired`, but the gateway returns `expired_card`. Which is the intended
  contract?
````

Drop any section with no entries. Keep the summary table, and lead the body with
the reds.
