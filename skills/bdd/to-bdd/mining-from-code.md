# Mining requirements from code

The code encodes the rules already; it just writes them in a language no stakeholder
reads. Mining recovers them.

What you recover is **observed** behaviour — what the code does, not what it should do. A
bug you fail to notice becomes the official spec and gets locked in by a passing test. So
mining produces a draft the user confirms, never a finished feature file.

## 1. Pick one slice

One bounded area — checkout, auth, billing, one service. A whole codebase mined at once
produces a pile nobody will read closely enough to confirm, and confirmation is the part
that makes this worth doing. Agree the slice with the user before digging.

**Done when:** the slice has a named boundary — these routes, this module, this service —
and the user has agreed to it.

## 2. Inventory the surface

List what an actor can do in this slice. Read, in this order:

1. **Existing tests** — the closest thing to a spec you have. A test name plus its
   assertions is a scenario in disguise, and the assertions are already observable
   outcomes.
2. **Entry points** — HTTP routes, CLI commands, message and event handlers, exported
   service methods, scheduled jobs. These are your `When` steps.
3. **Guards** — validation, permission checks, thrown errors, error messages, early
   returns. Each guard is a business rule, and usually two scenarios: the path that passes
   it and the refusal that does not.
4. **Domain types** — entities, their status enums, and the transitions between them. A
   status field is a lifecycle, and each legal transition is a behaviour.
5. **Edges** — OpenAPI or Swagger specs, database constraints, UI strings, analytics
   events. Cheap, specific, and often the only place a rule is stated in words.
6. **History** — `git log` on the slice's core files. Commit and PR messages explain why a
   rule exists when nothing else does.

**Done when:** every entry point in the slice is listed with the guards it enforces and the
outcomes it can produce, including the refusals.

## 3. Derive the rules

Turn the inventory into behaviour statements: actor, trigger, outcome. Group them by the
entity or capability they belong to.

Note what the code does **not** settle: a magic number with no explanation, a branch no
test covers, two paths that look contradictory, dead code that may or may not still matter.
These become questions, not scenarios.

**Done when:** every entry point and guard from step 2 has either a behaviour statement or a
question against it.

## 4. Draft and confirm

Write the scenarios, and mark the whole set as observed behaviour awaiting confirmation — an
`@observed` tag on each scenario, or a header note on the file.

Then walk the user through them in batches, grouped by capability, and get a verdict on each
rule:

- **Intended** — the tag comes off; it is a spec.
- **Wrong** — the code has a bug. The scenario stays, written as the behaviour the user
  wants, and it will fail on first run. That failure is the finding.
- **Unknown** — nobody remembers. It stays tagged `@observed` and stays honest.

Your questions from step 3 go to the user in the same pass.

**Done when:** every drafted scenario carries a verdict, and every scenario still tagged
`@observed` is named back to the user as unconfirmed.

## 5. Hand off

Report the slice covered, the counts by verdict, and the questions still open. Say which
slice is worth mining next.

From here the normal chain continues: `/wire-bdd` writes the glue, `/run-bdd` runs it.
Expect scenarios marked **wrong** to fail on that first run — that is the point of them.
