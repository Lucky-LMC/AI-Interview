---
name: ai-interview-upgrade
description: Upgrade this AI interview project so implementation, README, and resume claims stay aligned. Use when modifying the LangGraph interview workflow, adding resume validation or question-review gates, implementing Pydantic structured outputs, improving RAG/Tavily/SSE behavior, hardening FastAPI/MySQL/SQLite persistence, or checking whether the project can honestly support resume claims about an 8-node multi-agent workflow, quality gates, retry/fallback, and session recovery.
---

# AI Interview Upgrade

## Purpose

Use this skill for project-specific upgrades to the AI interview system in this repository. The goal is not to add impressive labels; the goal is to make the source code, README, and resume language mutually defensible.

This skill is repo-scoped. Prefer it over generic LangGraph or RAG advice when working inside this project.

## Required Context Pass

Before editing behavior, read the current source of truth:

1. `README.md`
2. `backend/graph/workflow/interview_workflow.py`
3. `backend/graph/state/interview_state.py`
4. `backend/graph/nodes/`
5. `backend/graph/agents/`
6. `backend/graph/tools/`
7. `backend/routes/interview_routes.py`
8. `backend/routes/consultant_routes.py`
9. `backend/models/schemas.py`

If comparing against the resume, read `references/resume-alignment.md`.
If planning the 8-node upgrade, read `references/workflow-upgrade-checklist.md`.

## Upgrade Rules

- Preserve the existing FastAPI + LangGraph + LangChain + Chroma + Tavily + MySQL + SQLite architecture unless there is a concrete reason to change it.
- Keep workflow nodes small and named after real responsibilities.
- Do not claim a capability in README or resume support notes unless the code has a corresponding implementation and verification path.
- Prefer Pydantic models for LLM outputs that need reliability, especially resume validation and question review.
- Prefer deterministic control flow for quality gates: review result -> route/retry/fallback. Do not rely only on prompt wording for critical guarantees.
- Keep the main interview flow and consultant RAG flow separate. The consultant uses SSE streaming; the main interview flow currently uses normal request/response unless explicitly upgraded.
- Do not expose secrets. Never open `.env` just to inspect keys.

## Recommended Target Architecture

When aligning the project to the resume, aim for an explainable 8-node main interview workflow:

1. `parse_resume`: extract PDF text and produce a structured resume summary.
2. `validate_resume`: check resume summary quality and required fields.
3. `interviewer_agent`: generate a candidate-specific interview question.
4. `review_question`: score the question for relevance, difficulty, duplicate risk, and clarity.
5. `answer`: interrupt point where the user submits an answer.
6. `check_finish`: decide whether to continue or finish.
7. `feedback_agent`: identify weaknesses and search learning resources.
8. `generate_report`: create the final Markdown report.

If adding retry behavior, keep it bounded. One rewrite attempt plus a template fallback is usually enough.

## Quality Gate Pattern

Use this pattern for gates that must be defensible in interviews:

1. Define a Pydantic schema in `backend/models/schemas.py` or a focused graph schema module.
2. Make the LLM return structured data that can be parsed into that schema.
3. Store the review result in `InterviewState` so it is visible for debugging and recovery.
4. Route based on explicit fields such as `passed`, `score`, or `needs_rewrite`.
5. Add fallback behavior for parse failures and low-quality outputs.

For question review, the expected dimensions are:

- `relevance`: tied to resume, role, and previous answers.
- `difficulty`: suitable for the current round.
- `duplicate_risk`: avoids repeating earlier questions.
- `clarity`: answerable and specific.

## Verification Expectations

Before claiming the upgrade is complete:

- Run syntax or import checks with the project virtual environment when available: `.venv\Scripts\python.exe`.
- Run `python -m compileall backend -q` or the `.venv` equivalent.
- Exercise or unit-check the new gate logic without requiring real paid API calls when possible.
- Re-read README and any resume-support notes to ensure they do not overstate the code.
- Include any known limits in the final summary.

## What Not To Do

- Do not copy large third-party skill packs into this repository.
- Do not add unverified metrics such as "92%" unless there is an evaluation script, dataset, and reproducible command.
- Do not turn the consultant Agent into part of the main interview workflow just to inflate node count.
- Do not silently change authentication, storage, or file deletion behavior while working on graph quality gates unless the user explicitly includes hardening in scope.
