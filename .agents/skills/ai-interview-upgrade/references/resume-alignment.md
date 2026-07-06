# Resume Alignment Reference

Use this reference when checking whether the AI interview project supports resume claims.

## Current Safe Claims

These claims are supported by the current project shape:

- FastAPI backend with native HTML/CSS/JavaScript frontend.
- LangGraph main interview workflow with checkpoint-backed state.
- PDF resume parsing through PyPDF2.
- LLM-based resume summarization and target-role extraction.
- Interviewer Agent using LangGraph `create_react_agent` and Tavily-backed question search.
- Feedback Agent using Tavily-backed learning-resource search.
- Consultant Agent using Chroma RAG first and Tavily fallback.
- MySQL business records plus SQLite LangGraph checkpoints.
- SSE streaming for the consultant chat endpoint.
- History list, resume file preview, record recovery, and delete flows in the frontend.

## Claims That Need Code Before Use

Do not present these as implemented unless the code exists:

- 8-node main interview workflow.
- Independent question-quality review Agent.
- Resume-structure quality gate.
- Pydantic structured output for question type, assessment point, reference answer, or review scores.
- Low-quality question rewrite route.
- Fallback to preset question templates after rewrite failure.
- Quantified question-role matching score such as 92%.

## Resume-Safe Upgrade Language

After the planned upgrade, the resume can safely say:

```text
Built an 8-node LangGraph interview workflow covering resume parsing, resume validation, question generation, question review, user answer interruption, round routing, learning-resource retrieval, and report generation.
```

Only add quantified metrics if an `evaluation/` script and sample set are committed.

## Review Checklist

Before updating README or resume text, verify:

- The named node exists in `backend/graph/workflow/interview_workflow.py`.
- The node function exists in `backend/graph/nodes/`.
- State fields are defined in `backend/graph/state/interview_state.py`.
- Pydantic schemas exist for structured LLM outputs.
- Retry/fallback behavior is implemented in code, not only in prompts.
- A verification command has been run in the current turn.
