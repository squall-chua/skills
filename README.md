# Agent Skills 🧩

> My personal collection of customized **agent skills** — capabilities I've built and tailored for skill-aware AI coding agents to load on demand.

This repo is where I keep the agent skills I use in my own workflow. Each skill teaches an agent how to handle one kind of task end to end, and is self-contained and conditionally loaded — so an agent pulls in a capability only when the work calls for it.

---

## 🗂️ Available skills

A quick map — each category is a folder under [`skills/`](skills/).

| Category | Skills |
| --- | --- |
| [🏗️ Design](#-design) | `system-design-architect`, `architecture-review` |
| [💻 Language](#-language) | `golang` |
| [✍️ Writing](#-writing) | `oldman` |
| [🥒 BDD](#-bdd) 🧪 | `to-bdd`, `wire-bdd`, `run-bdd`, `sync-bdd` |
| [🧪 Quality](#-quality) 🧪 | Three front doors over the skills that measure — see [the hierarchy](#-how-these-fit-together) |
| &nbsp;&nbsp;└ [🔧 Development](#-development--kept-green-on-a-branch) 🧪 | **`code-quality`** reads `code-coverage`, `mutation-test`, `crap-test`, `static-analysis`, `dry-test`, `clean-code`, and the BDD four |
| &nbsp;&nbsp;└ [🚦 Release](#-release--run-at-the-gate) 🧪 | **`release-quality`** reads `contract-test`, `integration-test`, `fault-injection-test`, `stress-test`, `security-compliance` |
| &nbsp;&nbsp;└ [🎨 Visual](#-visual--run-against-a-rendered-page) 🧪 | **`visual-quality`** reads `visual-accessibility`, `visual-slop` |

🧪 marks a skill that is still experimental — read the note at the top of its category before you trust its output.

### 🏗️ Design

Skills that shape a system before and after it is built.

#### 🏗️ [`system-design-architect`](skills/design/system-design-architect/SKILL.md)

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

#### 🗺️ [`architecture-review`](skills/design/architecture-review/SKILL.md)

Reads the architecture behind a change and writes it up. Point it at a branch, a GitHub PR, a GitLab MR, a Gerrit CL, a commit range, a folder, or the whole repo. It maps the components, the arrows between them, the stores, and the outbound calls — for a change review, both before and after — then reports what changed, with Mermaid diagrams where they earn their place.

The core of it is two intentions. The **stated** one is what the author said the change is for, quoted from the PR body, the issue, and the commit messages. The **built** one is what the code now makes cheap and what it makes expensive. The gap between them is **drift**, and the report names each kind: promised but unbuilt, built but unstated, over-built, under-built, or put in the wrong component. Where the author stated nothing at all, that is recorded as a finding rather than filled in from the diff — reading intent off the diff makes drift impossible to see.

**Use it when you want to:**

- Understand the shape of a change before reviewing it line by line.
- Check that what a PR does matches what its description says it does.
- Get architecture documentation, with diagrams, for a codebase nobody has written up.
- Find the boundaries, cycles, and missing seams that a line-by-line review walks straight past.
- Know the blast radius of a changed shared interface before it ships.
- Get a concrete proposal per problem — the move, the cost, and when to do it — sized against the change rather than three times bigger.

Ten lenses do the flagging: boundaries, direction, cycles, blast radius, ownership of state, seams, failure, coupling in time, evolution, and consistency. Findings are bucketed P1, P2, P3, each with the cost of leaving it and who pays. The report also names what held up, so the next person knows which pattern to copy, and closes with what the review did not read.

**Trigger it with:** `/architecture-review`. It never fires on its own, and it changes no code — the report is the whole deliverable.

---

### 💻 Language

Skills for writing code in one language.

#### 🐹 [`golang`](skills/language/golang/SKILL.md)

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

### ✍️ Writing

Skills that change how the agent writes, not what it builds.

#### 🧓 [`oldman`](skills/writing/oldman/SKILL.md)

A plain-language, concise communication mode. Like a patient old man explaining to a friend: the agent keeps replies short by cutting filler and pleasantries, but uses full, simple, everyday words and correct grammar — no rare vocabulary, jargon, or slang unless truly needed. This makes answers easy to follow for an older reader or a non-native English speaker. The style also applies to what the agent writes: documents, READMEs, and commit messages.

**Use it when you want to:**

- Get short, clear answers without fancy or hard words.
- Make an agent's writing readable for a non-native or non-technical audience.
- Keep docs and commit messages plain and easy to scan.

**Trigger it with:** "oldman mode", "keep it simple", "plain English", or `/oldman`. Turn it off with "stop oldman" or "normal mode".

---

### 🥒 BDD

Skills that turn requirements into `.feature` files and keep them honest.

Between them they fill **specified behaviour**, one of the seven dimensions the [🔧 Development](#-development--kept-green-on-a-branch) front door [`code-quality`](skills/quality/code-quality/SKILL.md) reads — `run-bdd` writes the report it looks for. They sit in their own category because they are worth having on their own, whether or not you ever run a front door.

> ### 🧪 The BDD skills are experimental
>
> `to-bdd`, `wire-bdd`, `run-bdd`, and `sync-bdd` are new and still being shaped by real use. Their steps, wording, and hand-offs between each other will change. Try them, but read what they produce before you trust it, and keep your `.feature` files in version control so a bad run is one `git checkout` away from undone.

#### 🥒 [`to-bdd`](skills/bdd/to-bdd/SKILL.md) 🧪

Turns requirements into domain-driven Gherkin/Cucumber `.feature` files. The agent first hunts for the requirements — in the conversation, in repo docs and PRDs, or in whichever issue tracker the project uses — and asks you where they live if it finds nothing that states a real behaviour. It then reads the project to learn its own vocabulary, so the scenarios speak the team's language instead of inventing new terms. Every scenario must end on an outcome someone can actually check; anything that cannot be made testable is reported back to you rather than guessed at.

**Use it when you want to:**

- Convert a PRD, spec, or GitHub issue into acceptance criteria or `.feature` files.
- Write BDD scenarios that read at the business level, with no selectors, endpoints, or SQL in the steps.
- Keep scenarios to one behaviour each, with a single `When` and an observable `Then`.
- Get BDD started on an undocumented codebase, where the code is the only spec there is.

**Undocumented codebase?** When no requirements exist anywhere, the skill loads [`mining-from-code.md`](skills/bdd/to-bdd/mining-from-code.md) and recovers the rules from the code itself — existing tests, entry points, guards, domain types, and git history, one slice at a time. What comes back is tagged as *observed* behaviour, not spec: the code shows what the system does, and a bug nobody spots would otherwise become the official requirement. You confirm each rule as intended or wrong before the tag comes off. Rules you mark wrong stay written the way you want them, so they fail on the first run and the bug shows up as a finding.

**Trigger it with:** `/to-bdd`. The skill never fires on its own — you have to call it.

**Credit:** the Gherkin rules are distilled from [AutomationPanda/gherkin-guidelines-for-ai](https://github.com/AutomationPanda/gherkin-guidelines-for-ai) by [Andrew Knight](https://github.com/AutomationPanda), and the domain-driven framing from the [`bdd-gherkin`](https://github.com/angelo-v/opencode-playground/blob/main/.opencode/skills/bdd-gherkin/SKILL.md) skill by [Angelo Veltens](https://github.com/angelo-v).

#### 🔌 [`wire-bdd`](skills/bdd/wire-bdd/SKILL.md) 🧪

The middle piece between `to-bdd` and `run-bdd`: it writes the step definitions that make your `.feature` files actually runnable. The agent lists every undefined step, reads the project setup to pick the framework it already uses (`@cucumber/cucumber`, `pytest-bdd`, `behave`, `godog`, `cucumber-jvm`, `cucumber`, Reqnroll), finds the real code each step should drive, and writes thin glue that calls the system through its own doors. A step with nothing to call yet is marked pending, not faked green. It finishes by running the suite, so the report of what passes, fails, or is pending comes from real output.

**Use it when you want to:**

- Turn `.feature` files into executable tests using the framework already in the project.
- Fill in missing step definitions without duplicating the ones that exist.
- Find out which scenarios have no product code behind them yet.

**Trigger it with:** `/wire-bdd`. Like its siblings, it never fires on its own.

#### 📋 [`run-bdd`](skills/bdd/run-bdd/SKILL.md) 🧪

The end of the chain: it runs the `.feature` files and writes up what happened. The agent finds the command the project already uses (`cucumber-js`, `pytest-bdd`, `behave`, `godog`, `cucumber-jvm`, SpecFlow), runs it, and backs every verdict with the captured output — a scenario with no output counts as unrun, not passed. The feature files are the spec and are never edited to make a run go green; a scenario that looks wrong is raised as a spec question, and one with no step definitions is listed as unwired and handed back to `wire-bdd`. Each run writes its own timestamped report, so the agent can say what turned red or green since the last one.

**Use it when you want to:**

- Run the existing `.feature` files and get a readable report of what passed and what did not.
- See failures with the exact step, the expected value, the observed value, and a likely cause.
- Find out which scenarios have no step definitions yet, or are blocked on missing test data.

Each failure is sorted into a **product fix**, where the spec is right and the code is wrong, or a **spec question**, where the scenario may describe behaviour nobody intended — only you can settle the second, so it goes in the report as a question. Nothing is written until you say go. Ask it to fix the failures and it changes the product code, supplies the missing fixtures, re-runs the whole suite to prove nothing else turned red, and writes a *second* report beside the first. Spec questions, pending scenarios, and unwired scenarios are left standing, since each needs an answer, planned work, or `/wire-bdd`.

**Trigger it with:** `/run-bdd`. Like its siblings, it never fires on its own.

#### 🔄 [`sync-bdd`](skills/bdd/sync-bdd/SKILL.md) 🧪

Keeps the `.feature` files honest as requirements change. The agent reads both sides in full — the current requirements from docs, issues, or the conversation, and every scenario in the feature files — then pairs them by behaviour rather than by wording. What does not pair is sorted into **uncovered** (a requirement nothing specifies), **stale** (a scenario whose requirement moved on), and **orphaned** (a scenario with no requirement behind it). You get a drift report with counts and quoted evidence, then a proposed fix per item. Nothing is edited or deleted until you approve it.

**Use it when you want to:**

- Check whether the feature files still describe the product you actually ship.
- Catch requirements that changed after the scenarios were written.
- Find scenarios describing behaviour nobody wrote down, before deciding to drop them.

**Trigger it with:** `/sync-bdd`. Like its siblings, it never fires on its own.

---

### 🧪 Quality

Skills that measure code, tests, or a running system, and report what they find.

> ### 🧪 The test and quality skills are experimental
>
> Every skill from here down is marked 🧪: `mutation-test`, `code-coverage`, `crap-test`, `dry-test`, `static-analysis`, `clean-code`, `contract-test`, `integration-test`, `fault-injection-test`, `stress-test`, `visual-accessibility`, `visual-slop`, `security-compliance`, and the three front doors `code-quality`, `release-quality`, and `visual-quality`. They are new and still being shaped by real use, so their steps, thresholds, buckets, and report shapes will change.
>
> Three habits make them safe to try. Run them on a branch, so a bad run is one `git checkout` away from undone. Read the report before you trust the number — each says plainly what it did not measure, and that part matters more than the score. And check anything a fix run writes: a test written to kill a mutant can still be a poor test, and a fix that closes one finding can open another.
>
> `fault-injection-test` and `stress-test` put a running system in trouble on purpose. Never point either at production or shared staging without the authorization its third step asks for.

#### 🧭 How these fit together

There are **fourteen dimensions** — fourteen questions about the code, the suite, or the running system. Thirteen skills in this category answer one each, and the fourteenth, specified behaviour, takes the three BDD skills between them. Three **front doors** sit above the lot: each reads its group's reports together, cross-reads them, and gives one graded verdict. The grouping is by **phase**, because the fourteen do not all belong at the same moment.

| Phase | Front door | Reads these skills | Needs |
| --- | --- | --- | --- |
| 🔧 Development | [`code-quality`](skills/quality/code-quality/SKILL.md) | `code-coverage`, `mutation-test`, `crap-test`, `static-analysis`, `dry-test`, `clean-code`, and the four [🥒 BDD](#-bdd) skills | a laptop and a branch |
| 🚦 Release | [`release-quality`](skills/quality/release-quality/SKILL.md) | `contract-test`, `integration-test`, `fault-injection-test`, `stress-test`, `security-compliance` | a running system, containers, permission to break things |
| 🎨 Visual | [`visual-quality`](skills/quality/visual-quality/SKILL.md) | `visual-accessibility`, `visual-slop` | a page that renders in a browser |

Every skill below writes a timestamped report into `.reports/`. A front door reads whichever reports it finds there — it never runs a sibling for you, because these cost real time and a couple of them touch a live system. When a report is missing it hands you the command instead.

```
Quality
│
├── /code-quality ..................... development — the code and its suite
│   ├── code-coverage ................. how much of the code runs under test
│   ├── mutation-test ................. would the tests catch a bug, or run past it
│   ├── crap-test ..................... which functions are dangerous to edit
│   ├── static-analysis ............... what is wrong with the code as written
│   ├── dry-test ...................... is one piece of knowledge in several places
│   ├── clean-code .................... can the next person read it and change it
│   └── to-bdd → wire-bdd → run-bdd ... does the written spec hold
│
├── /release-quality ............ release — the running system
│   ├── contract-test ........... does the API keep the contract it publishes
│   ├── integration-test ........ does it work against a real database
│   ├── fault-injection-test .... does it survive that database failing
│   ├── stress-test ............. how much load before it stops keeping up
│   └── security-compliance ..... what can an attacker reach
│
└── /visual-quality ............. visual — the rendered interface
    ├── visual-accessibility .... can everyone operate it
    └── visual-slop ............. did anybody decide anything
```

Three rules hold in all three front doors. **The verdict is a floor, not an average** — sound on six dimensions and fragile on the seventh is fragile. **Absent evidence is never good news** — missing, skipped, and stale all read as *unproven*, never as a pass. And **relevance comes before measurement** — a JSON API is told it has no interface to grade, rather than graded ⚫ Unproven on accessibility.

The three are independent. Nothing merges them, and each names the other two at the end of its report so a green verdict in one phase is never mistaken for a whole-system pass.

#### 🔧 Development — kept green on a branch

Seven dimensions you can answer without deploying anything. Every one is measured against the code or the suite, so all seven run on a laptop, at module scope, in the middle of an afternoon. [`code-quality`](skills/quality/code-quality/SKILL.md) is the front door; the rest fill it.

##### 🧭 [`code-quality`](skills/quality/code-quality/SKILL.md) 🧪

The development front door: the seven dimensions you can answer without deploying anything. Each one alone is easy to misread — 90% coverage looks like health right up until the mutation score says the tests assert nothing, and a file can be perfectly unique and unreadable. All seven are measured against the code or the suite, so all seven run on a laptop, on a branch, at module scope, in the middle of an afternoon. That is what makes this the set to keep green during development rather than at a release gate.

Called on a repo with no reports at all, it works out which of the seven that project should cover and which are a practice the team may take or leave — then hands over **one** command, the cheapest thing you can run today, and keeps the rest of the list in the report. Finish that one, call it again, and it names the next. It asks only about dimensions whose precondition is already met, so a repo with no tests is never asked to weigh mutation testing. On a codebase with nothing measured it gives an eight-move ladder that runs the spec first, because every other dimension here measures the code against itself and only the scenarios say what the code was *for*.

**Use it when you want to:**

- A starting point when you have run none of these skills and want to know which ones your project needs.
- One verdict on the code's health instead of seven reports to reconcile.
- To know whether a coverage number means anything, judged against the other signals.
- An ordered list of what to fix first, drawn from every report at once.
- A starting plan for a codebase with no tests at all, ordered by risk rather than by file.

**Trigger it with:** `/code-quality`. It never fires on its own — and neither do the sibling skills it draws on, so when a signal is missing it hands you the command to fill it rather than running it for you.

##### 📊 [`code-coverage`](skills/quality/code-coverage/SKILL.md) 🧪

Runs the unit tests with coverage on and turns the number into a plan. The agent picks the tool your language uses, turns branch coverage on, and records every exclusion with a reason. Then it ranks the gaps instead of listing them — git churn crossed with what the code decides, so money, permissions, and data writes go to the top. Each gap near the top names the behaviour nobody tests and a concrete test to add. Nothing is written to your tests, your config, or CI until you say go.

**Use it when you want to:**

- Get a coverage report broken down by module, package, and file, not one number.
- Know which uncovered code to test first, ranked by risk instead of by size.
- Get a specific test suggested for each gap, with the case name and the input.
- Have those gaps closed for you, once you have read the report and said go.
- Set a coverage gate that holds, and compare this run against the last one.

**Trigger it with:** `/code-coverage`. It never fires on its own.

**Its sibling:** coverage says a line ran; [`mutation-test`](skills/quality/mutation-test/SKILL.md) says whether the line is checked. Run this one first — it is the cheaper half.

##### 🧬 [`mutation-test`](skills/quality/mutation-test/SKILL.md) 🧪

Checks the tests, not the code. The agent breaks your source on purpose, one small edit at a time — each edit is a *mutant* — and a good test suite goes red on every one. A mutant that survives marks a behaviour nobody is testing. You get a timestamped report listing every survivor, the behaviour it exposes, and the test that would kill it. Your tests are not touched until you say go.

**Use it when you want to:**

- Find out whether your tests would actually catch a bug, not just execute the line.
- Turn a high coverage number into a real measure of test quality.
- Have the missing tests written and proven, once you have read the report and said go.
- Set a mutation score gate in CI that runs over changed files.

**Trigger it with:** `/mutation-test`. It never fires on its own.

**Credit:** the process outline comes from the [`add-mutation-testing`](https://github.com/qdhenry/Claude-Command-Suite/blob/main/.claude/commands/test/add-mutation-testing.md) command in [qdhenry/Claude-Command-Suite](https://github.com/qdhenry/Claude-Command-Suite) by [Quinney Henry](https://github.com/qdhenry), MIT licensed.

##### 💩 [`crap-test`](skills/quality/crap-test/SKILL.md) 🧪

Scores every function with the CRAP metric — `complexity² × (1 − coverage)³ + complexity` — so complex code and untested code are read as one number instead of two. The run is a replay: the agent writes one stdlib-only script, proves it against twelve fixed vectors before it touches your repo, then joins a complexity file to a coverage file and prints a CSV. The script, both inputs, and the CSV are saved beside the report, so anyone can re-run it and get the same table. The order is the score and nothing else. Nothing is written to your tests or your source until you say go.

**Use it when you want to:**

- Find the functions that are both hard to follow and barely tested, ranked by one number.
- Get an exact coverage target per function — "34%, needs 50.0%" instead of "add more tests".
- Know which functions no test can save: complexity 31 or more fails even at 100% coverage.
- Have the tests written and the big functions split, once you have read the report and said go.
- Gate CI on the count of functions over 30, as a ceiling that can only fall.

**Trigger it with:** `/crap-test`. It never fires on its own.

**Its siblings:** it reuses what [`code-coverage`](skills/quality/code-coverage/SKILL.md) and [`static-analysis`](skills/quality/static-analysis/SKILL.md) measure separately, and crosses them. Coverage ranks gaps by risk, which is a judgement; this one ranks by arithmetic. Run both — they disagree usefully.

##### 🔬 [`static-analysis`](skills/quality/static-analysis/SKILL.md) 🧪

Reads the code without running it, over the paths you name — or over the files changed against the default branch if you name none. It runs three kinds of tool: a type checker, a linter, and a dead code finder. Then it cuts the noise. Findings are grouped by *rule*, because one rule firing 200 times is one decision and not 200 problems, then categorised and re-ranked by what the code decides. Each real finding gets one plain sentence on what goes wrong and a fix written as a diff. It works on untested code: a red suite or no suite does not stop the reading, only the fixing. Security sits outside this run — that is `security-compliance`. Nothing is changed until you say go.

**Use it when you want to:**

- Point a set of analyzers at specific folders or files and get one readable report.
- See the real bugs separated from the style noise.
- Get a fix diff per finding, and know how many fix themselves.
- Put a baseline in place so CI fails on new findings without failing on the past.
- Have the fixes applied and proven, once you have read the report and said go.

**Trigger it with:** `/static-analysis`. It never fires on its own.

##### 🧬 [`dry-test`](skills/quality/dry-test/SKILL.md) 🧪

Finds functions that share a *shape*, in fourteen languages, and then refuses to call that a DRY violation on its own. It ships its own engine: [`dry.py`](skills/quality/dry-test/scripts/dry.py) is a port of Robert C. Martin's [dry4go](https://github.com/unclebob/dry4go) onto tree-sitter grammars — each function's syntax tree becomes a set of subtree fingerprints with names and literal values stripped, and two functions are scored by Jaccard similarity over those sets. Clones are grouped into families, and each family is crossed with a second measurement: how often git says those files were edited *together*. Shape says they look alike; co-change says whether they have ever moved as one. The report ends with the one question a machine cannot answer — does the same sentence describe what every member knows?

**Use it when you want to:**

- Find copy-paste across a codebase in Python, Go, JavaScript, TypeScript, TSX, Java, Kotlin, Swift, C#, PHP, Ruby, Rust, C, or C++.
- See clone *families* rather than a list of pairs — three copies are one problem, not three.
- Tell real duplication from code that only rhymes, using history instead of taste.
- Get a proposal per family, and a recorded reason for the ones that should stay as they are.
- Gate CI on new duplication in changed files.

**Trigger it with:** `/dry-test`. It never fires on its own, and it changes no code until you name the families to merge.

**Why you can trust the number:** four self-checks run against your own code before any score prints — rename every identifier (must not move the score), flip an operator (must move it), add an escape inside a string (must not), and find any unit at all. Each was verified by breaking the script on purpose. The same four also run against a committed fixture in **each of the fourteen languages** ([`check_fixtures.py`](skills/quality/dry-test/scripts/check_fixtures.py)), alongside two more: one rewrites every literal value and requires the fingerprints not to move (dry4go's normaliser rule asserted directly), the other flips an operator *inside* a string interpolation and requires that it does move, because interpolated code is not spelling. All **29 `UNITS` entries across the 14 languages** are reached by a fixture, and the expected set is stated in the runner rather than read from `dry.py`, so deleting a table entry fails the suite instead of quietly satisfying it. That suite caught two real faults on its first run, in Swift and PHP. On Go's `net/http` the port returns **100% of dry4go's 150 findings**, and its exact prefilters were confirmed to give byte-identical results to brute force on two corpora, 9,061 units in 7 seconds.

**Credit:** the algorithm — normalised syntax trees, subtree fingerprints, Jaccard similarity, and the `--min-lines` / `--min-nodes` floors — is [Robert C. Martin's](https://github.com/unclebob), from [`dry4go`](https://github.com/unclebob/dry4go). `dry.py` is an independent implementation of it over tree-sitter; no dry4go source is bundled here.

##### 🧼 [`clean-code`](skills/quality/clean-code/SKILL.md) 🧪

Reads the code the way a person does, against the clean code rules — fifty-six of them in nine groups, from names and functions through comments, structure, objects and tests. This is the half no linter reaches: a tool can prove a function is 80 lines long, but only a reader can say it does two things, that a name lies about what it holds, or that a comment repeats the line beneath it. The risk is the mirror of a linter's, so the skill's spine is the cut: a rule broken that causes no **smell** — rigidity, fragility, immobility, needless complexity, needless repetition, opacity — is taste, and taste is counted and dropped rather than reported. The project's own conventions beat the rule list, and anything a formatter, a linter, or a sibling skill already owns is struck off before the reading starts. Every fix keeps the behaviour; a fix that needs the behaviour to change becomes a bug report instead.

**Use it when you want to:**

- Get the readability findings a linter cannot produce, over the folders you name.
- See each one ranked by the smell it causes, not by how much it offends a rule.
- Read one plain sentence on what the next person pays for it, with a fix diff.
- Know how many breaks were dropped as taste, so the silence is accounted for.
- Have the fixes applied and proven against the suite, once you have read the report and said go.

**Trigger it with:** `/clean-code`. It never fires on its own.

**Credit:** the rules are [Robert C. Martin's](https://github.com/unclebob), from *Clean Code*, by way of [Wojtek Lukaszuk's summary](https://gist.github.com/wojteklu/73c6914cc446146b8b533c0988cf8d29). What the skill adds is the reading procedure, the smell ranking, and the report.

##### 🥒 The BDD four fill the seventh dimension

`to-bdd`, `wire-bdd`, and `run-bdd` fill **specified behaviour** — does the written spec hold — and `run-bdd` writes the `bdd-report-` that `/code-quality` reads. They live in the [🥒 BDD](#-bdd) category above because they are useful on their own, but this is the phase they belong to. The three go end to end on a repo with no tests at all: `to-bdd` mines a draft from the code where no requirements are written, `wire-bdd` builds the harness rather than needing one, `run-bdd` runs the result. `sync-bdd` keeps the scenarios in step with the code afterwards.

#### 🚦 Release — run at the gate

Five dimensions that are properties of a deployed whole rather than of a file. None can be run at module scope or answered with the service stopped, and each is blocked on an **environment** rather than on effort. [`release-quality`](skills/quality/release-quality/SKILL.md) is the front door; the rest fill it.

##### 🚦 [`release-quality`](skills/quality/release-quality/SKILL.md) 🧪

The release front door: the five dimensions that are properties of a deployed whole rather than of a file. None can be run at module scope, none can be answered with the service stopped, and each is blocked on an **environment** rather than on effort — a URL, a Docker daemon, a load environment, permission to break things. So the skill names the precondition per dimension, because "we need a staging instance we are allowed to break" is a request a team can act on and "resilience is unproven" is not.

It checks one thing nothing else in the family checks: the **environment** each report ran against. A stress report from a staging database a twentieth the size of production measured a system nobody operates, so that report is graded ⚫ Unproven rather than believed — a number from the wrong environment is worse than no number, because it reads as evidence. And it closes with the line the whole skill exists for: **is this safe to release** — ready, ready with named limits, not ready, or unknown. It never softens *unknown* into *probably fine* on the strength of a year without incident.

**Use it when you want to:**

- A release readiness check that says plainly what it does not know.
- To know whether a clean contract run covered the whole API or a fifth of it.
- One verdict across security, contracts, seams, resilience, and load instead of five reports.
- An ordered plan for a system where none of this has ever been measured, cheapest favour asked first — security on a build, contracts on a URL, seams on Docker, then the two that need a platform conversation.

**Trigger it with:** `/release-quality`. It never fires on its own.

##### 🤝 [`contract-test`](skills/quality/contract-test/SKILL.md) 🧪

Tests a running API against its own contract, from the outside. The source is never opened: every finding comes from a request the agent sent and the response it got back, so the report says what a real consumer hits. A gap between the promise and the behaviour is a *drift*. The agent finds the contract — published in the repo, served by the running app, or derived from the route definitions — runs a conformance tool against a target you pin, then sends by hand the promises no tool checks on its own: guards, error bodies, media types, unknown ids, pagination. Two numbers come out side by side: how much of the contract was exercised, and how much of that had no drift. Your API source is never edited.

**Use it when you want to:**

- Check that a deployed API still matches the OpenAPI, GraphQL, gRPC, or AsyncAPI contract it publishes.
- Test an API that publishes no contract at all — the agent derives one and leaves the file behind as a first draft.
- Test an API you cannot or should not read the source of — a third party's, another team's, a legacy service.
- Find the breaking changes a deploy introduced, before the consumers find them.
- Know which part of your contract has never actually been tested.
- Keep the hand-sent probes as a checked-in suite that runs in seconds.
- Set up a CI gate that judges on new drift instead of a total count.

**Trigger it with:** `/contract-test`. It never fires on its own.

**Its siblings:** coverage and mutation testing look inward at the code; this one stands outside the box and asks whether the API keeps its word.

##### 🔗 [`integration-test`](skills/quality/integration-test/SKILL.md) 🧪

Writes the tests that run against your real database, broker, cache, and object store. A *seam* is where your code hands work to something it does not own. Unit tests stop at the seam and mock what is on the far side, so everything they prove is a statement about your own mock. This skill crosses it: one rule sorts the seams — run the collaborators you own in a container the suite starts itself, fake the ones you do not — and a seam left mocked in-process is reported as *unproven* rather than counted. Every test is *proven red* before it is trusted, and the suite is proven *hermetic* four ways: alone, shuffled, twice with no wipe, and in parallel. Your production code is left alone.

**Use it when you want to:**

- Get real integration tests written for the database, queue, cache, or storage your code actually talks to.
- Replace mocks that pass while production breaks.
- Find out which of your collaborators have never been tested for real.
- Fix a flaky integration suite, or prove a new one is not flaky before you trust it.
- Set up containers that start themselves, so a fresh clone and CI both just work.

**Trigger it with:** `/integration-test`. It never fires on its own.

##### 💥 [`fault-injection-test`](skills/quality/fault-injection-test/SKILL.md) 🧪

Breaks the environment under your running system and watches what happens. First it writes down the *steady state* — the few numbers that say the system is serving people, each with the command that reads it and a tolerance band. Then it takes the dependencies down, slows them past the timeout, makes them flap, fills the disk, kills a container mid-request, and partitions the network, one fault at a time, with a hypothesis written before each run. The blast radius, the abort condition, and the kill switch are all fixed first, and the kill switch is tested while nothing is wrong. Two things come out: how many experiments held their steady state, and whether it came back afterwards. Your production code is not touched until you say go.

Ask it to fix things and it adds one mechanism at a time — a timeout, backoff with jitter, a circuit breaker, a bulkhead, an idempotency key, a fallback — then re-runs the *identical* experiment to prove it. Same fault, same hold time, same load, before and after. Widening a tolerance band or softening a fault to turn a red into a green is called out as rewriting the exam.

**Use it when you want to:**

- Find out whether your system survives its database, cache, broker, or payment provider going down.
- Catch the failure that matters more than any of them: the system that never comes back after the fault stops.
- See which weakness is missing a timeout, a retry budget, a circuit breaker, or a fallback.
- Learn what a fault actually does to a customer, and whether anything alerted anybody.
- Discover the coupling nobody knew about, when breaking one thing moves something else.
- Have the resilience added and proven by re-running the same fault, once you have read the report and said go.

**Trigger it with:** `/fault-injection-test`. It never fires on its own.

**Needs:** a running system under a realistic load, and a container runtime for the injector. Production or shared staging needs recorded authorization first.

##### 📈 [`stress-test`](skills/quality/stress-test/SKILL.md) 🧪

Raises the load until your system stops keeping up, and finds the *knee* — the point where throughput stops rising and latency starts climbing. Below it, more load means more work done; above it, more load means only more waiting. Then it names what gave first: the connection pool, one pinned core, garbage collection, a query without an index. A knee with no cause named is a number nobody can act on. The figure it leads with is **headroom** — the knee divided by the peak you actually have to serve, which is the one number someone outside the team can use.

It is strict about one thing above all. A load generator that waits for each response before sending the next stops sending when the system stalls, so the slowest requests are never made and never recorded — that is *coordinated omission*, and it is why so many load tests report a p99 that the real peak walks straight through. This skill runs an open model at a constant arrival rate, records latency against the time each request was *due* to be sent, and states the arrival model in the report header so you can tell whether the percentiles mean anything. Five shapes run, not one: smoke, load, stress, soak, and spike. Your code is not touched until you say go.

**Use it when you want to:**

- Find out how much traffic your system takes before it stops keeping up, and how much room that leaves.
- Know which resource is the actual limit, so the performance work goes where it will move something.
- Catch the leak a short run cannot see — connections, memory, or file handles climbing over hours.
- Find out whether overload settles at a limit or collapses, because retries can make a busy system worse.
- Get a load test whose percentiles are not quietly flattering.
- Have the knee raised and proven by re-running the same profile, once you have read the report and said go.

**Trigger it with:** `/stress-test`. It never fires on its own.

**Needs:** a running instance and a load generator. Shared staging or production needs recorded authorization first, and third parties are stubbed by default.

##### 🛡️ [`security-compliance`](skills/quality/security-compliance/SKILL.md) 🧪

Scans the code, its dependencies, its full git history, and the running app, then sorts the findings by the only fact that decides which one matters: *reach*. A CVSS 9.8 in a build-time dependency reaches nobody; a 5.3 on an unauthenticated route reaches everybody, and it is the one that gets used. So every finding carries a path — entry point, route through the code, sink — or a written argument for why no path exists. What scanners are useless at, the agent reads by hand: IDOR, missing route authorization, tenant isolation, SSRF, business logic, crypto misuse, and what leaks into logs. DAST runs only with authorization recorded first — approver, staging target, hosts, window, and rate limit. Secret values and captured PII stay out of the report.

**Use it when you want to:**

- Get one security review across code, dependencies, history, containers, and the live app.
- Find out which of your hundreds of CVEs an attacker can actually reach.
- See your findings mapped to OWASP Top 10 and CWE, with the categories no tool checked named as gaps.
- Run an authorized DAST pass against staging with the scope and window recorded.
- Get a fix per finding, and know which need a design change rather than a patch.
- Set the four CI gates, including the scheduled dependency scan — a repo clean on Friday is vulnerable on Monday and no commit announces it.

**Trigger it with:** `/security-compliance`. It never fires on its own.

#### 🎨 Visual — run against a rendered page

Two dimensions that need pixels. Both drive a real browser, and neither can be read out of source. They answer the two halves of one question: can a person use this interface, and would they remember it. [`visual-quality`](skills/quality/visual-quality/SKILL.md) is the front door; the rest fill it.

##### 🎨 [`visual-quality`](skills/quality/visual-quality/SKILL.md) 🧪

The visual front door: the two dimensions that need pixels. Both drive a real browser, and neither can be read out of source — a focus ring nobody can see and a row of tag chips above a tinted icon tile do not exist until the page renders. They answer the two halves of one question. **Access** asks whether a person can use the interface. **Signature** asks whether they would remember it. The common shape is a page that fails both while looking fine to whoever built it.

The most likely correct answer here is *not applicable*, and the skill says so in a line rather than grading a JSON API ⚫ Unproven on access. Where an interface does exist, it widens each report's scope to the shared components and the style layer — a commit to a `Button` invalidates every report that rendered one — and records which routes, widths, themes, and states were walked, because a page checked at 1440 in light mode was checked once, not four ways. Its sharpest finding is a pair: a P1 barrier sitting on the element that also carries the worst tell stack, which is one rebuild rather than two fixes.

**Use it when you want to:**

- To know, in plain words, whether everyone can use the interface and whether anyone would remember it.
- One verdict across accessibility and design instead of two reports about the same screen.
- To find the element that is both unusable and undesigned, and rebuild it once.
- A fix list that says which findings belong in a shared component and how many pages that reaches.

**Trigger it with:** `/visual-quality`. It never fires on its own.

##### ♿ [`visual-accessibility`](skills/quality/visual-accessibility/SKILL.md) 🧪

Drives your running UI in a real browser and checks it against WCAG. A rules engine sees about a third of WCAG, and it is not the third that stops people — so the agent runs whichever engine your project already has (axe, Pa11y, Lighthouse, jest-axe), then drives the rest by hand with the [`vibium`](https://github.com/vibium/vibium) browser CLI: tab order, focus visibility, keyboard traps, reflow at 320px, reduced motion, forced colours, live regions. Findings are ranked by *barrier* — what a person cannot do because of it — so a keyboard trap in checkout outranks a contrast miss on a footer link. Every finding carries the command that reproduces it and a screenshot. Your UI source is left alone.

**Use it when you want to:**

- Get a WCAG report on the running app, not on the markup as written.
- Find the barriers a scanner cannot see — focus order, focus rings, keyboard traps, live regions.
- Know which of your accessibility findings actually stop somebody finishing a task.
- See which success criteria nothing checked, named as gaps rather than passes.
- Check the app at 320px, at 200% zoom, in dark mode, and under forced colours.
- Set gates that catch a palette change before it moves every screen at once.

**Trigger it with:** `/visual-accessibility`. It never fires on its own.

**Needs:** a running instance and the `vibium` CLI. No test suite required.

##### 🫠 [`visual-slop`](skills/quality/visual-slop/SKILL.md) 🧪

Checks your running UI against the [pols.dev anti-slop design law](https://pols.dev/slop.md) — about 150 named *tells* of a generated interface, fetched fresh each run and walked heading by heading, so the review is against the law rather than against the agent's taste. Findings are ranked by what they *stack* with: one pill is a choice, but an icon tile plus a category pill plus tag chips plus a hairline border plus a glowy button in one card is the clearest slop signature there is. Because the law's own deepest point is that dodging the list is still slop, every finding carries the replacement rather than just the removal, and the page gets one verdict on whether it has a signature at all. Nothing is changed until you say go.

Ask it to fix things and it builds the *signature first*, before removing a single tell — strip the tells from a page with nothing decided and you get a cleaner page that still reads as generated. Then it works P1 defects, the stacked elements, and the single tells, checking each change three ways: the style sweep again, fresh screenshots, and a re-walk of the headings that change could touch, since swapping a glow for a hairline border trades one tell for another. It writes a *second* report beside the first, with the before and after pictures of each rebuilt element side by side.

**Use it when you want to:**

- Find out whether your interface reads as AI-made, and exactly which parts give it away.
- Get the design tells separated from the real defects — dead controls, clipped text, sections that render empty.
- See which single element is carrying the most tells at once.
- Get a proposed replacement per finding, with the reason, instead of a list of things to delete.
- Find out whether the page has a signature, or is merely clean.
- Have the rebuild done and proven, once you have read the report and said go.

**Trigger it with:** `/visual-slop`. It never fires on its own.

**Needs:** a running instance, the `vibium` CLI, and network access to fetch the law.

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

# one skill, user-level — name the skill, not its folder path
npx skills add squall-chua/skills -g -s golang

# everything, no prompts
npx skills add squall-chua/skills --all
```

Skills are harness-agnostic, so a plain copy works too:

```bash
# Claude Code (user-level)
cp -r skills/design/system-design-architect ~/.claude/skills/

# or project-level
cp -r skills/design/system-design-architect .claude/skills/
```

The category folders are for reading the repo, not for the agent. Copy the skill folder itself — the one holding `SKILL.md` — straight into your skills directory. The `skills` CLI does this for you.

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
- The `mutation-test` skill's process outline comes from the [`add-mutation-testing`](https://github.com/qdhenry/Claude-Command-Suite/blob/main/.claude/commands/test/add-mutation-testing.md) command in [qdhenry/Claude-Command-Suite](https://github.com/qdhenry/Claude-Command-Suite) by [Quinney Henry](https://github.com/qdhenry), which is MIT licensed. The mutation-testing loop is theirs; this repo added the triage buckets, the score formula, and the report.
- The `dry-test` skill's engine implements the algorithm of [`dry4go`](https://github.com/unclebob/dry4go) by [Robert C. Martin](https://github.com/unclebob) — normalised syntax trees, one fingerprint per subtree, Jaccard similarity, and the `--min-lines` / `--min-nodes` floors. The algorithm is his; [`dry.py`](skills/quality/dry-test/scripts/dry.py) is an independent implementation of it over tree-sitter grammars so it runs on fourteen languages, and no dry4go source is bundled here.
- The `code-coverage`, `static-analysis`, `code-quality`, `release-quality`, `visual-quality`, `crap-test`, and `dry-test` skills were designed with, and `mutation-test` and `run-bdd` reshaped by, the [`writing-great-skills`](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-great-skills/SKILL.md) skill by [Matt Pocock](https://github.com/mattpocock), from the MIT-licensed [mattpocock/skills](https://github.com/mattpocock/skills). None of its text is bundled here — what it contributed is the method: completion criteria on every step, the information hierarchy that decides what stays in `SKILL.md`, leading words, and the pruning discipline. The shape of these skills owes it a great deal.

---

## 📄 License

Licensed under the MIT License — see [LICENSE](LICENSE) for details. Bundled third-party content keeps its own license: the `golang` skill guides are MIT licensed from [samber/cc-skills-golang](https://github.com/samber/cc-skills-golang), the `to-bdd` skill derives from [AutomationPanda/gherkin-guidelines-for-ai](https://github.com/AutomationPanda/gherkin-guidelines-for-ai) and the MIT-licensed [`bdd-gherkin`](https://github.com/angelo-v/opencode-playground/blob/main/.opencode/skills/bdd-gherkin/SKILL.md) skill, and `mutation-test` derives from the MIT-licensed [qdhenry/Claude-Command-Suite](https://github.com/qdhenry/Claude-Command-Suite) — keep the attribution in [🙏 Credits](#-credits) if you redistribute it. The `writing-great-skills` influence noted there is method rather than bundled text, so it carries no license obligation, but the credit stands.
