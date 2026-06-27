# ARIA

> **Autonomous Reasoning & Interaction Agent**
>
> An engineering-first autonomous AI runtime designed to build real AI agents that can **reason, interact, remember, and execute**.

---

## Vision

Most AI agent projects focus on prompting large language models.

ARIA focuses on **building the runtime around the model**.

The language model is only the **brain**.

Everything else—planning, browser automation, memory, tools, execution, and orchestration—is implemented as independent engineering modules.

Our goal is to build an extensible AI operating runtime rather than another chatbot.

---

# Why ARIA?

Modern agent frameworks are powerful, but many tightly couple:

* reasoning
* tool execution
* memory
* browser automation
* provider APIs

This makes replacing components difficult.

ARIA separates these responsibilities into independent modules.

```
            User
              │
              ▼
          ARIA CLI
              │
              ▼
         ARIA Harness
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
 Planner   ToolRouter  Memory
              │
     ┌────────┼─────────┐
     ▼        ▼         ▼
 Browser   Vision    Research
              │
              ▼
            Brain
        (GPT / Claude / Local)
```

The AI model is **replaceable**.

The runtime is **the product**.

---

# Philosophy

ARIA follows four engineering principles.

## 1. Brain is replaceable

Today's AI may be GPT-5.5.

Tomorrow it may be Claude.

Next year it may be a local model.

Nothing else should change.

---

## 2. Everything is a module

Planner

Browser

Memory

Vision

Research

Tool Router

Harness

are independent modules.

---

## 3. Local-first

ARIA should continue to function even when cloud models are unavailable.

Cloud providers enhance reasoning.

They should never define the architecture.

---

## 4. Autonomous engineering

ARIA is designed to:

* inspect repositories
* browse the web
* generate reports
* remember previous work
* assist software engineering workflows

---

# Features

* GPT-5.5 Brain (OpenAI Responses API)
* Browser automation using Playwright
* Vision abstraction
* Long-term memory
* Research report generation
* CLI-first workflow
* Rich terminal interface
* Modular Harness architecture
* Mock providers for offline development
* uv-native packaging
* Fully tested

---

# Installation

Using uv:

```bash
uv tool install aria-agent
aria config set openai-api-key
aria demo
```

or locally

```bash
git clone https://github.com/<your-name>/ARIA.git

cd ARIA

uv sync

uv tool install . --reinstall
aria config set openai-api-key
uv run aria demo
```

After publication, ARIA can also run through:

```bash
uvx aria-agent
pipx install aria-agent
aria --help
```

---

# Configuration

Set the OpenAI key used by ARIA's brain:

```bash
aria config set openai-api-key
```

For local/offline verification without a key, allow the mock brain:

```bash
export ARIA_ALLOW_MOCK_BRAIN=1
```

Verify configuration:

```bash
aria config show
aria config check
```

Verify the brain:

```bash
aria brain check
```

---

# Run

Run a research task:

```bash
aria run "Research browser-use and produce a short report for ARIA"
```

Learn from a YouTube transcript:

```bash
aria youtube https://www.youtube.com/watch?v=t5F3RkDRzqA
aria learn https://www.youtube.com/watch?v=t5F3RkDRzqA
```

Learn from a web or GitHub URL:

```bash
aria learn https://github.com/browser-use/browser-use
```

Search memory:

```bash
aria memory search "browser screenshots"
```

List generated reports:

```bash
aria report list
```

Generated reports are written under:

```
reports/
```

---

# Demo

```bash
aria demo
aria run "youtube https://www.youtube.com/watch?v=t5F3RkDRzqA"
aria memory search "Spider-Man"
aria report list
```

---

# Project Structure

```
src/aria/

brain/

planner/

browser/

vision/

memory/

research/

tools/

cli/

config/

harness.py
```

---

# Why is ARIA different?

ARIA is **not** trying to become another AutoGPT.

ARIA is **not** trying to become another LangGraph.

ARIA is **not** trying to become another CrewAI.

Instead,

ARIA provides a lightweight autonomous runtime where every subsystem can evolve independently.

The emphasis is software engineering.

Not prompt engineering.

---

# Roadmap

* Reflection loop
* Multi-agent collaboration
* ChromaDB long-term memory
* Local LLM providers
* MCP ecosystem
* Plugin system
* Voice interaction
* Computer-use improvements
* Distributed agents

---

# Contributing

Contributions are welcome.

Please open an issue before submitting large architectural changes.

---

# License

MIT

---

## Long-term Goal

ARIA aims to become an open-source autonomous AI runtime for engineers.

The objective is not simply to generate text.

The objective is to build software capable of reasoning, interacting with the real world, remembering previous experience, and continuously improving over time.
