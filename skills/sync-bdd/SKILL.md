---
name: sync-bdd
description: >
  Diff the current requirements against the existing `.feature` files and report
  the drift.
disable-model-invocation: true
---

Find the **drift** between what the project now requires and what the
`.feature` files still say. Both sides get read in full, because drift hides in
what nobody thought to look at.

## 1. Fix both sides

**Requirements** — the current ones. Look in this order: the conversation, the
repo (PRDs, specs, ADRs, `README.md`, `CLAUDE.md`), then the project's issue
tracker for anything that changed the behaviour — reached the same way `to-bdd`
step 1 describes, whichever tracker and tool that turns out to be. If you find
nothing stating a behaviour, ask the user where the requirements live.

**Features** — every `.feature` file in scope.

For a large set, `git log` on the requirement docs and on the feature directory
tells you which side moved last and narrows where drift is likely. The
comparison itself still covers everything in scope.

**Done when:** you have both lists — every behaviour the requirements state, and
every scenario the feature files specify.

## 2. Match them

Pair each requirement behaviour with the scenario that covers it. Match on
behaviour — actor, trigger, outcome — rather than on wording, since a rename is
itself a kind of drift.

**Done when:** every requirement behaviour and every scenario is either paired or
left unpaired on purpose. An item you skipped because it was hard to place is
drift you failed to report.

## 3. Classify the drift

Each unpaired or mismatched item lands in one bucket:

- **Uncovered** — a requirement behaviour with no scenario. Something the
  project promises and nothing specifies.
- **Stale** — a paired scenario that no longer matches its requirement: a
  changed rule, a changed value, a changed outcome, or the project's own
  terminology moved on and the scenario kept the old word.
- **Orphaned** — a scenario with no requirement behind it. Either the behaviour
  was dropped, or it is real behaviour nobody wrote down. These two need
  opposite fixes, so name which one you believe it is and why.

**Done when:** every item from step 2 sits in a bucket, and every stale item
quotes the requirement's wording against the scenario's wording.

## 4. Report the drift

Report in the conversation, shaped like this — write it to a Markdown file
instead when the user asks or when it runs long:

```markdown
## Drift summary

| Bucket | Count |
| --- | --- |
| 🟠 Uncovered | 3 |
| 🟡 Stale | 2 |
| ⚪ Orphaned | 1 |
| ✅ In sync | 14 |

### 🟠 Uncovered

- **Refund window shortened to 14 days** (`docs/refunds-prd.md` §3) — no
  scenario covers the window at all.

### 🟡 Stale

- `checkout.feature` › Customer pays with an expired card
  - **Requirement now:** decline reason is `expired_card` (issue #212)
  - **Scenario still:** `Then the payment is declined with reason "card expired"`

### ⚪ Orphaned

- `loyalty.feature` › Points expire after 12 months — no requirement mentions
  expiry. Reads like real behaviour that was never written down, not a dropped
  feature, because `LoyaltyPoint.expiresAt` exists in the code.
```

**Done when:** every item from step 3 appears in the report, and both totals from
step 1 reconcile — every requirement behaviour is Uncovered, Stale, or In sync,
and every scenario is Orphaned, Stale, or In sync.

## 5. Fix what the user approves

Propose one fix per item and wait for the user's call:

- **Uncovered** → writing scenarios is the `to-bdd` skill's job, so tell the
  user to call `/to-bdd` and list the behaviours it needs to cover.
- **Stale** → edit the scenario to match the current requirement.
- **Orphaned, real behaviour** → the requirement doc is what is missing; offer to
  write it, and leave the scenario alone.
- **Orphaned, dropped feature** → deleting a scenario throws away the only
  record of that behaviour, so confirm each deletion with the user and quote the
  scenario before removing it.

**Done when:** every approved fix is applied, and every item the user left alone
is named back to them so nothing drops silently.
