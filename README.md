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

*More skills will be added over time.*

---

## 🛠️ Installation & usage

Skills are harness-agnostic. To use one, copy its directory into wherever your agent loads skills from — for example:

```bash
# Claude Code (user-level)
cp -r skills/system-design-architect ~/.claude/skills/

# or project-level
cp -r skills/system-design-architect .claude/skills/
```

Once installed, trigger a skill with natural language that matches its purpose — e.g.:

- *"I want to design a high-scale URL shortener."*
- *"Help me create a system design for a real-time chat application."*

---

## 📊 Example output

[docs/design/url-shortener.md](docs/design/url-shortener.md) is a real document produced by the `system-design-architect` skill, including capacity calculations, sharded database justifications, Mermaid.js architecture diagrams, and a global edge redirection strategy.

---

## 📄 License

Licensed under the MIT License — see [LICENSE](LICENSE) for details.
