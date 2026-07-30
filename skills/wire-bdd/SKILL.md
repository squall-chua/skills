---
name: wire-bdd
description: >
  Write the step definitions that make the project's `.feature` files runnable,
  in whichever BDD framework the project uses.
disable-model-invocation: true
---

Write the **glue** — the step definitions that bind each Gherkin step to real code.
Glue stays thin: a step matches its text, calls the project's own code, and holds no
logic of its own.

## 1. Gather the undefined steps

Read the `.feature` files in scope, list every distinct step, then find the existing
step definitions and mark which steps they already cover.

The fastest way to the true list is the runner itself — most BDD runners print undefined
steps with a snippet for each. Run it if the project has one wired.

**Done when:** you have the list of steps still needing glue, deduplicated — steps that
differ only in a parameter value are one step with a parameter.

## 2. Read the project's setup

Find the framework from what the project already has: the manifest (`package.json`,
`pyproject.toml`, `go.mod`, `pom.xml`, `build.gradle`, `Gemfile`, `*.csproj`), the test
config, and any existing step definitions.

| Project | Framework | Steps usually live in |
| --- | --- | --- |
| JS / TS | `@cucumber/cucumber` (`playwright-bdd` when Playwright drives the browser) | `features/step_definitions/` |
| Python + pytest | `pytest-bdd` | `tests/step_defs/` |
| Python, no pytest | `behave` | `features/steps/` |
| Go | `godog` | a `*_test.go` in the package under test, with `.feature` files under `features/` |
| Java / Kotlin | `cucumber-jvm` with JUnit 5 | `src/test/java/**/steps/` |
| Ruby | `cucumber` | `features/step_definitions/` |
| C# / .NET | `Reqnroll` | `Steps/` |

An installed framework wins over the table every time. Where none is installed, name the
one that fits the stack and get the user's go-ahead before adding the dependency.

Every framework reads `.feature` files from a configured path, and most default to
`features/` at the root. Find where this project's files actually are — under a module
folder in a monorepo — and set the path to match. A runner pointed at an empty directory
reports zero scenarios and passes.

**Done when:** you know the framework, the file layout, the runner command, and — where
step definitions already exist — the conventions they follow: naming, async style, how
state passes between steps, where the support code sits.

## 3. Find the seams

For each undefined step, find the real code it should drive: the service function, the
HTTP client, the repository, the page object, the CLI entry point. The glue calls the
system through the same doors the application uses.

**Done when:** every undefined step names the function, endpoint, or object it will call,
or is marked as having no seam yet — a behaviour the product does not implement.

## 4. Write the glue

One step definition per distinct step. Rules:

- **Match the text.** The pattern matches the step in the `.feature` file exactly, and
  parameters use whatever syntax this framework parses — Cucumber expressions
  (`{string}`, `{int}`) in `@cucumber/cucumber`, `cucumber-jvm`, Ruby `cucumber` and
  Reqnroll; `parse` format (`{name}`, `{count:d}`) in `behave` and in `pytest-bdd` via
  `parsers.parse`; a regex in `godog`. Copy the syntax the project already uses. The
  feature file is the spec, so the glue bends to it.
- **Thin.** A step body sets up state, performs the action, or asserts an outcome, and
  nothing else. Anything longer than a few lines belongs in a support module the step
  calls.
- **`Then` asserts.** Every `Then` step ends on an assertion in the project's assertion
  library, comparing the real observed value.
- **Share state through the framework's own channel** — the World, a fixture, a scenario
  context object — matching what existing steps do.
- **Reuse before adding.** A step whose text an existing definition already matches needs
  no new definition.
- **Pending over pretend.** A step with no seam yet is marked pending with the framework's
  own mechanism, so the runner reports it as pending. An assertion written to pass without
  touching the system reports green and tests nothing.

Set up hooks and fixtures only where scenarios genuinely need them: a clean database per
scenario, a browser per scenario, a seeded account for a `Given`.

**Done when:** every step from step 1 has exactly one definition, or is marked pending with
the reason recorded.

## 5. Run it

Run the project's BDD command and read the output.

**Done when:** the runner reports zero undefined and zero ambiguous steps, and you can
state the pass / fail / pending counts from its actual output.

Failing scenarios are a real result — the glue works and the product disagrees with the
spec. Report those failures with the step, the expected value, and the observed one, and
leave both the feature file and the product code as they are unless the user asks for a
fix.

## 6. Report

Tell the user: the framework used, the files you created or changed, the step counts
(defined, reused, pending), and the runner's output counts. List each pending step with
what it is waiting on, and each failing scenario with its expected-vs-observed.
