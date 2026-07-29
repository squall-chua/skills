# Agent Skills 🧩

> My personal collection of customized **agent skills** — capabilities I've built and tailored for skill-aware AI coding agents to load on demand.

This repo is where I keep the agent skills I use in my own workflow. Each skill teaches an agent how to handle one kind of task end to end, and is self-contained and conditionally loaded — so an agent pulls in a capability only when the work calls for it.

---

## 🗂️ Available skills

### 🏗️ [`system-design-architect`](skills/system-design-architect/SKILL.md)

Guides you through producing a comprehensive system design document using an interactive, Socratic 7-step roadmap. Instead of making blind architectural assumptions, the agent proposes 2–3 viable options with trade-offs at each decision point and waits for you to choose — then compiles the final Markdown document (with Mermaid.js diagrams) once every step is settled.

**Use it when you want to:**

- Design a scalable, resilient system from scratch (e.g. a URL shortener, real-time chat, video streaming).
- Produce architecture documentation with capacity estimates, API design, data model, and failover strategy.
- Prepare for or practice a system design interview with a structured, decision-driven walkthrough.

**What it covers — the 7-step roadmap:**

1. **Requirements Clarification** — functional and non-functional requirements (scale, latency, consistency).
2. **Capacity Estimation** — users, traffic (RPS), storage, memory, and bandwidth.
3. **Interface Design** — API protocols (REST, gRPC) and public/internal endpoints.
4. **High-Level Design** — architecture mapped with Mermaid.js diagrams (load balancers, CDNs, app servers).
5. **Database Design** — SQL vs. NoSQL choice and the data schema.
6. **Scalability & Performance** — caching, sharding, and optimization layers.
7. **Reliability & Resiliency** — single points of failure and failover/redundancy design.

### 🧓 [`oldman`](skills/oldman/SKILL.md)

A plain-language, concise communication mode. Like a patient old man explaining to a friend: the agent keeps replies short by cutting filler and pleasantries, but uses full, simple, everyday words and correct grammar — no rare vocabulary, jargon, or slang unless truly needed. This makes answers easy to follow for an older reader or a non-native English speaker. The style also applies to what the agent writes: documents, READMEs, and commit messages.

**Use it when you want to:**

- Get short, clear answers without fancy or hard words.
- Make an agent's writing readable for a non-native or non-technical audience.
- Keep docs and commit messages plain and easy to scan.

**Trigger it with:** "oldman mode", "keep it simple", "plain English", or `/oldman`. Turn it off with "stop oldman" or "normal mode".

### 🐹 [`golang`](skills/golang/SKILL.md)

One Go (Golang) skill that covers the whole language and its ecosystem, from code style and concurrency to testing, gRPC, databases, and CI. The main `SKILL.md` is only an index of about 100 lines, so it stays cheap to load. Each row points to a topic guide under `references/`, and the agent reads a guide only when the task calls for it. Guides can point to deeper files of their own, so detail loads one level at a time.

**Use it when you want to:**

- Write, review, or debug Go code with idiomatic guidance on hand.
- Set up a Go project: layout, linting, CI, dependency management, observability.
- Work with a specific library — cobra, viper, testify, gqlgen, swaggo, wire, dig, fx, or the samber packages.

**What it covers — 45 topic guides, grouped by:**

1. **Writing everyday Go** — style, naming, docs, structs and interfaces, patterns, data structures, errors, context, concurrency, safety, modernizing, refactoring.
2. **Testing and measuring** — testing, testify, benchmarks, performance, troubleshooting, gopls.
3. **Building services and tools** — project layout, CLI, cobra, viper, databases, gRPC, GraphQL, Swagger, observability, security.
4. **Dependency injection** — the general guide plus google/wire, uber-go/dig, uber-go/fx, and samber/do.
5. **Toolchain and upkeep** — lint, CI, dependency management, library choices, pkg.go.dev lookups, staying updated.
6. **samber libraries** — lo, mo, oops, hot, ro, and slog.

**Credit:** the topic guides come from [samber/cc-skills-golang](https://github.com/samber/cc-skills-golang) by [Samuel Berthe](https://github.com/samber), MIT licensed. This version merges those 46 separate skills into one skill with an index, so only the relevant parts load. All credit for the Go content belongs to the original authors.

---

> ### 🧪 The BDD skills are experimental
>
> `to-bdd`, `wire-bdd`, `run-bdd`, and `sync-bdd` are new and still being shaped by real use. Their steps, wording, and hand-offs between each other will change. Try them, but read what they produce before you trust it, and keep your `.feature` files in version control so a bad run is one `git checkout` away from undone.

### 🥒 [`to-bdd`](skills/to-bdd/SKILL.md) 🧪

Turns requirements into domain-driven Gherkin/Cucumber `.feature` files. The agent first hunts for the requirements — in the conversation, in repo docs and PRDs, or in whichever issue tracker the project uses — and asks you where they live if it finds nothing that states a real behaviour. It then reads the project to learn its own vocabulary, so the scenarios speak the team's language instead of inventing new terms. Every scenario must end on an outcome someone can actually check; anything that cannot be made testable is reported back to you rather than guessed at.

**Use it when you want to:**

- Convert a PRD, spec, or GitHub issue into acceptance criteria or `.feature` files.
- Write BDD scenarios that read at the business level, with no selectors, endpoints, or SQL in the steps.
- Keep scenarios to one behaviour each, with a single `When` and an observable `Then`.
- Get BDD started on an undocumented codebase, where the code is the only spec there is.

**Undocumented codebase?** When no requirements exist anywhere, the skill loads [`mining-from-code.md`](skills/to-bdd/mining-from-code.md) and recovers the rules from the code itself — existing tests, entry points, guards, domain types, and git history, one slice at a time. What comes back is tagged as *observed* behaviour, not spec: the code shows what the system does, and a bug nobody spots would otherwise become the official requirement. You confirm each rule as intended or wrong before the tag comes off. Rules you mark wrong stay written the way you want them, so they fail on the first run and the bug shows up as a finding.

**Trigger it with:** `/to-bdd`. The skill never fires on its own — you have to call it.

**Credit:** the Gherkin rules are distilled from [AutomationPanda/gherkin-guidelines-for-ai](https://github.com/AutomationPanda/gherkin-guidelines-for-ai) by [Andrew Knight](https://github.com/AutomationPanda), and the domain-driven framing from the [`bdd-gherkin`](https://github.com/angelo-v/opencode-playground/blob/main/.opencode/skills/bdd-gherkin/SKILL.md) skill by [Angelo Veltens](https://github.com/angelo-v).

### 🔌 [`wire-bdd`](skills/wire-bdd/SKILL.md) 🧪

The middle piece between `to-bdd` and `run-bdd`: it writes the step definitions that make your `.feature` files actually runnable. The agent lists every undefined step, reads the project setup to pick the framework it already uses (`@cucumber/cucumber`, `pytest-bdd`, `behave`, `godog`, `cucumber-jvm`, `cucumber`, Reqnroll), finds the real code each step should drive, and writes thin glue that calls the system through its own doors. A step with nothing to call yet is marked pending, not faked green. It finishes by running the suite, so the report of what passes, fails, or is pending comes from real output.

**Use it when you want to:**

- Turn `.feature` files into executable tests using the framework already in the project.
- Fill in missing step definitions without duplicating the ones that exist.
- Find out which scenarios have no product code behind them yet.

**Trigger it with:** `/wire-bdd`. Like its siblings, it never fires on its own.

### 📋 [`run-bdd`](skills/run-bdd/SKILL.md) 🧪

The end of the chain: it runs the `.feature` files and writes up what happened. The agent collects every scenario in scope, finds the command the project already uses (`cucumber-js`, `pytest-bdd`, `behave`, `godog`, `cucumber-jvm`, SpecFlow), runs it, and captures the real output. Every verdict must be backed by that captured output — a scenario with no output counts as unrun, not passed. Failures are reported with the broken step, expected against observed, and a cause. The feature files are treated as the spec and are never edited to make a run go green; a scenario that looks wrong is raised as a spec question instead. Scenarios with no step definitions are listed as unwired and handed back to `wire-bdd`. The result is a Markdown report with a summary table, per-feature counts, and evidence under each failure. Each run writes its own timestamped file, so history is kept and the agent can tell you what turned red or green since the last run.

**Use it when you want to:**

- Run the existing `.feature` files and get a readable report of what passed and what did not.
- See failures with the exact step, the expected value, the observed value, and a likely cause.
- Find out which scenarios have no step definitions yet, or are blocked on missing test data.

**Trigger it with:** `/run-bdd`. Like `to-bdd`, it never fires on its own.

### 🔄 [`sync-bdd`](skills/sync-bdd/SKILL.md) 🧪

Keeps the `.feature` files honest as requirements change. The agent reads both sides in full — the current requirements from docs, issues, or the conversation, and every scenario in the feature files — then pairs them by behaviour rather than by wording. What does not pair is sorted into **uncovered** (a requirement nothing specifies), **stale** (a scenario whose requirement moved on), and **orphaned** (a scenario with no requirement behind it). You get a drift report with counts and quoted evidence, then a proposed fix per item. Nothing is edited or deleted until you approve it.

**Use it when you want to:**

- Check whether the feature files still describe the product you actually ship.
- Catch requirements that changed after the scenarios were written.
- Find scenarios describing behaviour nobody wrote down, before deciding to drop them.

**Trigger it with:** `/sync-bdd`. Like its siblings, it never fires on its own.

> ### 🧬 `mutation-test` is experimental
>
> It is new and still being shaped by real use. Its steps, thresholds, and report shape will change. Try it on a branch, read what it writes before you trust the score, and check the tests it adds — a test written to kill a mutant can still be a poor test.

### 🧬 [`mutation-test`](skills/mutation-test/SKILL.md) 🧪

Checks the tests, not the code. The agent breaks your source on purpose, one small edit at a time — each edit is a *mutant* — and a good test suite goes red on every one. A mutant that slips through is a *survivor*, and it marks a behaviour nobody is testing. The skill runs the whole loop: confirm the suite is green first, scope which files to mutate, pick and configure the tool your language uses (Stryker, PIT, mutmut, gremlins, cargo-mutants, Infection, and others), run it, then sort every mutant into killed, survived, no coverage, timeout, build error, or equivalent. Each survivor gets one plain sentence naming the behaviour that goes unchecked. Then it kills them: write the test, apply the mutant by hand, watch the new test fail, revert, and confirm the suite is green. A test that does not fail against the mutant has not killed it. The score goes up by killing mutants, never by widening the exclude list. It finishes with a re-run that proves the kills, a threshold committed to the config, and a timestamped Markdown report.

**Use it when you want to:**

- Find out whether your tests would actually catch a bug, not just execute the line.
- Turn a high coverage number into a real measure of test quality.
- Get a list of surviving mutants with the missing behaviour spelled out, and tests written to kill them.
- Set a mutation score gate in CI that runs over changed files instead of the whole repo.

**Trigger it with:** `/mutation-test`. It never fires on its own.

**Credit:** the process outline comes from the [`add-mutation-testing`](https://github.com/qdhenry/Claude-Command-Suite/blob/main/.claude/commands/test/add-mutation-testing.md) command in [qdhenry/Claude-Command-Suite](https://github.com/qdhenry/Claude-Command-Suite).

*More skills will be added over time.*

---

## 🤖 Available agents

Skills teach one agent how to do a task. **Agents** are separate helpers you hand a whole task to. Each one runs in its own context and reports back. They live in [`agents/`](agents/).

### 🔍 [`auditor`](agents/auditor.md)

Checks that work claimed done is really done. It runs the code instead of just reading it, then compares what it finds against the spec. Use it when a task is marked complete but unproven, when the app should work end to end but doesn't, or when a summary looks too clean.

### 🚚 CLI delegates

Five agents that hand a task to another command-line coding tool and bring the answer back:

| Agent | Runs | Notes |
| --- | --- | --- |
| [`agy`](agents/agy.md) | `agy` | Reads its model list live with `agy models`. |
| [`claude-cli`](agents/claude-cli.md) | `claude` | A fresh Claude session with its own context. |
| [`copilot`](agents/copilot.md) | `copilot` | GitHub Copilot CLI. |
| [`codex`](agents/codex.md) | `codex` | OpenAI Codex CLI. |
| [`opencode`](agents/opencode.md) | `opencode` | Model names use `provider/model` form. |

All five follow the same three rules:

1. **You pick the model.** If you don't name one, the agent asks first. Your configured default is offered as the first choice.
2. **Only when you ask.** These agents are never started on their own initiative — you have to name them.
3. **Login stays with you.** Signing in opens a browser, so the agent never tries. It stops and tells you the command to run yourself.

---

## 🛠️ Installation & usage

The easiest way is the [Vercel `skills` CLI](https://github.com/vercel-labs/skills). It clones this repo and puts the skills where your agent looks for them:

```bash
# pick skills and target agents interactively
npx skills add squall-chua/skills

# one skill, user-level
npx skills add squall-chua/skills -g -s golang

# everything, no prompts
npx skills add squall-chua/skills --all
```

Skills are harness-agnostic, so a plain copy works too:

```bash
# Claude Code (user-level)
cp -r skills/system-design-architect ~/.claude/skills/

# or project-level
cp -r skills/system-design-architect .claude/skills/
```

The `skills` CLI does not handle agents — it only looks for `SKILL.md` files. Agents are single files, so copy the ones you want:

```bash
cp agents/auditor.md ~/.claude/agents/
```

Once installed, trigger a skill with natural language that matches its purpose — e.g.:

- *"I want to design a high-scale URL shortener."*
- *"Help me create a system design for a real-time chat application."*

---

## 📊 Example output

[docs/design/url-shortener.md](docs/design/url-shortener.md) is a real document produced by the `system-design-architect` skill, including capacity calculations, sharded database justifications, Mermaid.js architecture diagrams, and a global edge redirection strategy.

---

## 🙏 Credits

- The `golang` skill repackages [samber/cc-skills-golang](https://github.com/samber/cc-skills-golang) by [Samuel Berthe](https://github.com/samber) and its contributors. The Go guidance is their work; this repo only merged it into one skill with an on-demand index.
- The `to-bdd` skill's Gherkin rules are distilled from [AutomationPanda/gherkin-guidelines-for-ai](https://github.com/AutomationPanda/gherkin-guidelines-for-ai) by [Andrew Knight](https://github.com/AutomationPanda), and its domain-driven framing from the [`bdd-gherkin`](https://github.com/angelo-v/opencode-playground/blob/main/.opencode/skills/bdd-gherkin/SKILL.md) skill by [Angelo Veltens](https://github.com/angelo-v), which is MIT licensed. The rules are theirs; this repo restated them as a step-by-step skill.

---

## 📄 License

Licensed under the MIT License — see [LICENSE](LICENSE) for details. Bundled third-party content keeps its own license: the `golang` skill guides are MIT licensed from [samber/cc-skills-golang](https://github.com/samber/cc-skills-golang), and the `to-bdd` skill derives from [AutomationPanda/gherkin-guidelines-for-ai](https://github.com/AutomationPanda/gherkin-guidelines-for-ai) and the MIT-licensed [`bdd-gherkin`](https://github.com/angelo-v/opencode-playground/blob/main/.opencode/skills/bdd-gherkin/SKILL.md) skill — keep the attribution in [🙏 Credits](#-credits) if you redistribute it.
