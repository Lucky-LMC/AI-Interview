# Workflow Upgrade Checklist

Use this checklist when upgrading the main interview workflow to support the resume-aligned architecture.

## Phase 1: Baseline Fixes

- Fix `ask_question_node.py` so it uses the imported global `interviewer_agent` or imports `create_interviewer_agent` explicitly.
- Fix the exception fallback so it writes `fallback_question`, not an uninitialized `question`.
- Change the SQLite checkpoint path to be project-root based instead of cwd-relative.
- Compile the backend after each slice.

## Phase 2: State And Schemas

- Add state fields for resume validation:
  - `resume_validation`
  - `resume_valid`
- Add state fields for question review:
  - `question_review`
  - `question_retry_count`
- Add Pydantic models for structured outputs:
  - `ResumeValidationResult`
  - `QuestionReviewResult`

Keep schemas small. Prefer fields that drive routing:

- `passed: bool`
- `score: float`
- `issues: list[str]`
- `rewrite_instruction: str`

## Phase 3: Resume Validation Node

- Create `backend/graph/nodes/validate_resume_node.py`.
- Check that resume summary has a target role, skills, project highlights, and interview focus points.
- Use deterministic checks first.
- Use LLM structured validation only if deterministic checks are insufficient.
- Route invalid resumes to a safe user-facing error or repair path.

## Phase 4: Question Review Node

- Create `backend/graph/nodes/review_question_node.py`.
- Review the latest question against:
  - resume relevance
  - round-appropriate difficulty
  - duplicate risk
  - clarity
- Store the result in state.
- If failed and retry count is 0, route back to `interviewer_agent` with rewrite guidance.
- If failed again, use a deterministic fallback template.

## Phase 5: Workflow Wiring

Target graph:

```text
START
  -> parse_resume
  -> validate_resume
  -> interviewer_agent
  -> review_question
  -> answer
  -> check_finish
  -> interviewer_agent | feedback_agent
  -> generate_report
  -> END
```

Be careful with LangGraph interrupts. The interrupt should remain before `answer`, after question review has produced an acceptable question.

## Phase 6: Docs And Verification

- Update README workflow diagram text and project structure.
- Do not update resume metrics unless an evaluation artifact exists.
- Run `.venv\Scripts\python.exe -m compileall backend -q`.
- If possible, add unit tests or dry-run tests for validation/review helpers without real LLM calls.
- Summarize what is now supported and what remains packaging language.
