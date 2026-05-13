# System Design Architect Skill 🏗️

> A powerful, interactive agent skill designed to guide you through a comprehensive 7-step system design roadmap.

This repository contains the `system-design-architect` skill, an automated framework that helps engineers and architects build robust, scalable, and resilient system design documentation. Unlike generic AI generation, this skill prioritizes **Socratic dialogue** and **collaborative decision-making**.

---

## 🚀 Core Philosophy

### 1. Zero Blind Assumptions
The agent will **never** unilaterally decide on an architecture. At every critical juncture, it proposes 2-3 viable options with their respective trade-offs (Pros/Cons) and waits for your selection.

### 2. Interactive Step-by-Step Workflow
The process is broken down into 7 distinct phases. The agent completes one phase, presents the findings/options, and halts for your input before moving to the next.

### 3. Progressive Documentation
Throughout the session, the agent maintains the state of the design. Only when all 7 steps are finalized is the complete, polished Markdown document generated and saved to your desired location.

---

## 🗺️ The 7-Step Roadmap

Following the "Ace System Design Interviews Like a Boss" framework:

1.  **Requirements Clarification**: Define Functional and Non-Functional requirements (Scale, Latency, Consistency).
2.  **Capacity Estimation**: Calculate expected Users, Traffic (RPS), Storage, Memory, and Bandwidth needs.
3.  **Interface Design**: Define API protocols (REST, gRPC) and public/internal endpoints.
4.  **High-Level Design (HLD)**: Map out the architecture using **Mermaid.js** diagrams (Load Balancers, CDNs, App Servers, etc.).
5.  **Database Design**: Choose the right storage engine (SQL vs. NoSQL) and define the data schema.
6.  **Scalability & Performance**: Implement caching strategies, sharding, and optimization layers.
7.  **Reliability & Resiliency**: Identify Single Points of Failure (SPOF) and design failover/redundancy mechanisms.

---

## 🛠️ Usage

To activate the skill within an Antigravity session, simply mention system design or request an architecture document:

- *"I want to design a high-scale URL shortener."*
- *"Help me create a system design for a real-time chat application."*
- *"Let's build an architecture document for a video streaming service."*

### Trigger Keywords
The skill is automatically loaded when it detects:
`design system`, `architecture document`, `system design`

---

## 📊 Example Output

Check out [docs/design/url-shortener.md](docs/design/url-shortener.md) for a real-world example of a document generated using this skill. It includes:
- Precise capacity calculations.
- Sharded database justifications.
- Mermaid.js architecture diagrams.
- Global edge redirection strategies.

---

## 📦 Installation

To use this skill in your project, copy the `skills/system-design-architect` directory into your `.agent/skills/` folder.

```bash
cp -r skills/system-design-architect .agent/skills/
```

Ensure your `ARCHITECTURE.md` or `GEMINI.md` reflects the availability of this new skill.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
