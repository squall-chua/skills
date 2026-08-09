---
name: to-bdd
description: >
  Turn requirements into domain-driven Gherkin/Cucumber BDD scenarios.
disable-model-invocation: true
---

Turn requirements into `.feature` files that speak the project's **domain language**
and end on **observable** outcomes. A scenario nobody can check is prose, not a spec.

## 1. Find the requirement source

A requirement is usable only if it states a behaviour: an actor, an action, and an
expected outcome. Look in this order and stop when you have enough:

1. **This conversation** — what the user just described.
2. **The repo** — requirement docs, PRDs, specs, ADRs, existing `.feature` files,
   `README.md`, `CLAUDE.md`, linked design docs.
3. **The issue tracker** — whichever one this project uses. Find the ticket reference
   first: the branch name, recent commit messages, and PR descriptions usually carry it
   as `#42` or a key like `ABC-123`. Then read the ticket with whatever reaches that
   tracker — a CLI such as `gh`, `glab`, or `jira`, an MCP tool for Jira, Linear, Azure
   DevOps, or Shortcut, or a plain URL fetch for a public tracker. `ToolSearch` finds
   the MCP tools available in this session. When nothing can reach it, ask the user to
   paste the ticket.

If nothing you find states a behaviour, ask the user where the requirements live before
writing anything. Offer the places you searched, so they can point you at a doc path,
an issue number, or describe the behaviour directly.

When the answer is that no requirements exist anywhere — an undocumented codebase —
read [`mining-from-code.md`](mining-from-code.md) and follow it. The running code is
the last source, and it needs its own process.

**Done when:** you can name every behaviour to be specified, and each has an actor, a
trigger, and an expected outcome. Guessing at a missing outcome makes a scenario that
passes review and tests nothing.

## 2. Learn the project's language

Read enough of the project to speak its terms: `README.md`, `CLAUDE.md`, domain models,
existing `.feature` files, core type and entity names. A scenario that invents its own
words for the project's concepts is a scenario the team cannot read.

**Done when:** you have the project's word for every actor, entity, and state your
scenarios will mention, and you know what the project is for — so you can say whether
each scenario serves that goal or drifts off it.

## 3. Write the scenarios

One `.feature` file per behaviour area, kebab-case name, one `Feature` block per file.
Follow the rules below.

**Where the files go.** Where the project already holds `.feature` files, write beside
them — a spec split across two locations is a spec nobody can read whole. Otherwise
write to `<module>/features/`, where `<module>` is the nearest directory at or above the
code you are describing that holds the project's manifest (`package.json`, `go.mod`,
`pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`, a `*.csproj`).
Behaviour spanning several modules goes to the repository root `features/`. These files
are the spec, so they are committed like any other source.

Then say where the runner will look, because `features/` at the root is the default for
some frameworks and wrong for others. A runner pointed at a directory your files are not
in reports zero scenarios and exits green — a passing build over a spec that never ran.

| Framework | Where it expects `.feature` files |
| --- | --- |
| `cucumber-js`, `behave`, `godog`, Ruby `cucumber` | `features/` at the root — the default, nothing to configure |
| `cucumber-jvm` | on the test classpath, normally `src/test/resources/features/` |
| `pytest-bdd` | relative to the test module, or wherever `bdd_features_base_dir` points |
| `Reqnroll` / SpecFlow | inside the test project, as project items |
| any of them, in a monorepo module | wherever you put them — the path has to be set |

Tell the user which case they are in. Where the path needs setting, say so plainly and
name `/wire-bdd` as the skill that does it — it never fires on its own, so an unspoken
hand-off is a hand-off that does not happen.

Where a file already covers the behaviour area, read it and add to it, keeping every
scenario already there. Those are the project's spec, and often the only written record
of the behaviour they describe. A scenario that now looks wrong is a drift finding for
the user — say so and leave it standing, or run `/sync-bdd` for a full reconciliation.

**Done when:** every behaviour from step 1 appears in a scenario, every scenario passes
the step 4 checklist, every file you wrote still holds the scenarios it held before,
every file sits beside the project's existing `.feature` files or in the module's
`features/`, and the user has been told where their framework expects to find them —
including that `/wire-bdd` sets the path when it differs.

## 4. Check before you finish

Walk the checklist against each scenario, one at a time. Fix what fails.

**Done when:** each scenario has been checked against every item, and any requirement you
could not turn into a testable scenario is reported to the user with the reason — an
unobservable outcome, a missing rule, a conflict — rather than filled in by guesswork.

---

# Rules

## Structure

```gherkin
Feature: <behaviour area>
  As a <role>
  I want <goal>
  So that <reason>

  Background:
    Given <starting state shared by every scenario below>

  Scenario: <one behaviour>
    Given <context>
    When <the single action>
    Then <observable outcome>
```

- `Background` only for state that two or more scenarios share.
- Tags only when they carry real organising value. No decorative tags.
- Under 10 steps per scenario. Longer means two behaviours; split them.
- Blank line between scenarios, none between steps.

## Domain level, not implementation level

Steps describe what the business does, not how the software does it. No CSS selectors,
no endpoints, no SQL, no framework mechanics — unless the behaviour under test is itself
about that layer.

Prefer state over navigation. `Given the customer has an active subscription` beats a
click-by-click tour of the account page, unless the click path is what the scenario
specifies.

## One behaviour per scenario

Exactly one `When`. Two actions means two scenarios.

Keep `Given → When → Then` in order and never repeat a phase. A second `When` after a
`Then` is a second scenario wearing a disguise.

Use `And` and `But` sparingly. Never `Or`. One step never combines two actions or two
assertions with a conjunction — split it.

Do not bundle unrelated concerns. A functional check and a performance check belong in
separate scenarios.

## Observable outcomes

Every `Then` names a signal someone can check: a state, a message, a returned value, a
recorded event. "It works" and "the system behaves correctly" state nothing and test
nothing.

## Data

Parameters live in `Given`, not `When`. Use a data table when a `Given` carries two or
more fields or would otherwise become a chain of `And` steps. Use a doc string (`"""`)
for multiline payloads.

Use concrete, realistic values — real product names, amounts, dates. `foo` and `bar`
belong only where invalid input is the point.

## Scenario Outline

Reserve `Scenario Outline` for one behaviour genuinely driven by varying input, where
each row is a distinct case. Rows that produce the same behaviour with different
spellings add rows, not coverage. Plain `Scenario` is the default.

## Wording

Third person, present tense, subject then predicate: `the customer submits the order`.
Double quotes around string parameters. Correct grammar and spelling. The same word for
the same concept everywhere — no synonym drift.

---

# Checklist

- Every behaviour in the requirement source is covered.
- Each scenario tests one behaviour and runs independently of the others.
- Exactly one `When` per scenario.
- Every `Then` names an observable signal.
- Steps use the project's own vocabulary, consistently.
- No UI selectors, endpoints, or automation mechanics in step text.
- Parameters sit in `Given`; tables used for two or more fields.
- Example data is concrete and realistic.
- `Scenario Outline` used only for real input variation.
- Under 10 steps; strict `Given → When → Then` order.
- Each scenario serves the project's goal, not an invented one.
