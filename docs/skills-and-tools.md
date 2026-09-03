# Skills and Tools Configuration

This document outlines the Claude Code skills and tools selected to ensure the production-grade quality of the Enterprise Agentic RAG + Research + SQL platform.

## Selected Skills

| Skill/Tool | Purpose | Where it will be used | Why it is necessary | Alternatives Considered |
| :--- | :--- | :--- | :--- | :--- |
| `mistral-api` | LLM Integration Reference | Core RAG & Agentic Logic | Ensures precise use of the Mistral SDK, optimal prompt caching, and correct tool-use implementation to minimize latency and cost. | Internal model knowledge (too risky for production API specs) |
| `code-review` | Quality Assurance | FastAPI Endpoints, LangGraph Nodes, SQL Queries | Maintains "production-grade" standards by identifying bugs, efficiency bottlenecks, and non-idiomatic Python before merge. | Manual review (slower, less consistent) |
| `security-review` | Enterprise Hardening | SQL Layers, API Authentication, RAG Prompting | Critical for preventing SQL injection, prompt injection, and ensuring tenant data isolation in an enterprise context. | General code review (too broad; security needs a dedicated lens) |
| `artifact-diagramming` | Architectural Mapping | LangGraph State Machine, RAG Pipeline | Agentic workflows in LangGraph are complex state machines; visual diagrams are necessary to prevent logic drift and align stakeholders. | Text-based docs (insufficient for complex cycles) |
| `artifact-design` | Documentation Quality | Project Specifications, API Docs | Ensures that all shared documentation and architectural decisions are presented professionally and are easy to navigate. | Standard Markdown (lacks design polish for enterprise stakeholders) |

## Implementation Strategy

These skills will be invoked at the following lifecycle stages:

1. **Design Phase**: `artifact-diagramming` $\rightarrow$ `artifact-design` (Define flows and specs).
2. **Development Phase**: `mistral-api` $\rightarrow$ `code-review` (Implement and refine).
3. **Hardening Phase**: `security-review` (Audit for enterprise vulnerabilities).
4. **Verification Phase**: `code-review` (Final quality check).
