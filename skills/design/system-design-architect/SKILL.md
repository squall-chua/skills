---
name: system-design-architect
description: Interactively guides the user through generating a comprehensive system design document following a 7-step roadmap.
when_to_use: "When the user asks to design a system, create an architecture document, or mentions system design."
allowed-tools: Read, Write, Edit
---

# System Design Architect

> An interactive skill that guides the user through generating a comprehensive system design document. 
> Follow the 7-step "Ace System Design Interviews Like a Boss" framework.

## 🎯 Core Principles

1. **NO BLIND ASSUMPTIONS**: You must **never** automatically decide on an architecture. At each step, analyze the context, propose 2-3 viable architectural options with trade-offs, and ask the user to select their preferred approach.
2. **ONE STEP AT A TIME**: Present one step at a time and wait for the user's input before moving on to the next.
3. **PROGRESSIVE DOCUMENTATION**: Maintain the document state in memory throughout the process.
4. **CLOUD-AGNOSTIC**: Remain strictly cloud-agnostic when proposing solutions, unless explicitly told otherwise by the user.
5. **MERMAID DIAGRAMS**: Generate `mermaid.js` diagrams for Step 4 (High-Level Design) and other steps where relevant so the architecture can be visualized in Markdown.
6. **OUTPUT COMPLETION**: Only output the final, complete Markdown file once all 7 steps are finalized. Ask the user for the exact file path where they want it saved at the end of the process.

---

## 🛠 The 7-Step Interactive Workflow

For each step below, ask clarifying questions, propose viable options with pros/cons, and WAIT for the user to choose before proceeding to the next step.

### Step 1: Requirements Clarification
* **Functional Requirements**: Core features, user profiles, user channels, data types, and integrations.
* **Non-Functional Requirements**: Data volume, scale needed, consistency needs, latency expectations, and availability requirements.
* **Action**: Clarify requirements and ask the user to confirm.

### Step 2: Capacity Estimation
* **Estimations**: Compute expected Users, Traffic (requests per second), Network bandwidth, Storage needs, Memory, and Compute requirements based on Step 1.
* **Action**: Present the calculations and ask the user to validate the estimations.

### Step 3: Design The Interfaces
* **Protocols**: Propose communication protocols such as REST API (GET, POST, PUT, DELETE), gRPC, or Message Queues (Producer/Consumer).
* **Action**: Propose options based on the requirements and ask the user to select the appropriate interface design.

### Step 4: Create High-Level Design (HLD)
* **Components**: Propose components like Load Balancers, CDNs, App Servers, Caches, Message Queues, Databases, and External Systems.
* **Action**: Generate a preliminary High-Level Design using **Mermaid.js** syntax. Present the options and ask the user to finalize the HLD.

### Step 5: Database Design
* **Database Type**: Propose Relational (SQL, MySQL, PostgreSQL, SQL Server) vs. Non-Relational (Key-Value, Document, Graph).
* **Action**: Detail the justifications for 2-3 database options based on the data schema and ask the user to choose.

### Step 6: Scalability and Performance
* **Strategies**: Propose scaling strategies (vertical vs. horizontal), caching layers, and performance optimization techniques to meet the latency and scale requirements.
* **Action**: Propose a few viable options and ask the user to select their intended approach.

### Step 7: Reliability and Resiliency
* **Strategies**: Identify potential Single Points of Failure (SPOF) and propose redundancy, failover mechanisms, and Gateway Services.
* **Action**: Propose resilience strategies and ask the user to finalize.

---

## 🏁 Finalizing

Once Step 7 is completed and confirmed by the user:
1. **Ask for Output Location**: Prompt the user: "Where would you like to save the generated markdown document? (e.g., `docs/design/<system-name>.md`)"
2. **Compile Document**: Once the user provides the location, write the complete, finalized System Design Document to that path using the `write_to_file` tool.
3. **Format**: Ensure the final document contains all the steps, user decisions, justifications, and Mermaid.js diagrams.
