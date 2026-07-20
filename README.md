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

Skills are harness-agnostic. To use one, copy its directory into wherever your agent loads skills from — for example:

```bash
# Claude Code (user-level)
cp -r skills/system-design-architect ~/.claude/skills/

# or project-level
cp -r skills/system-design-architect .claude/skills/
```

Agents are single files. Copy the ones you want the same way:

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

---

## 📄 License

Licensed under the MIT License — see [LICENSE](LICENSE) for details. Bundled third-party content keeps its own license: the `golang` skill guides are MIT licensed from [samber/cc-skills-golang](https://github.com/samber/cc-skills-golang).
