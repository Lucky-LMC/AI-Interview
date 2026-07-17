import os
from pathlib import Path

import pytest


_TEST_ENV = {
    "OPENAI_API_KEY": "test-key",
    "OPENAI_API_BASE": "http://test.invalid/v1",
    "MODEL_NAME": "test-model",
    "TEMPERATURE": "0",
    "EMBEDDING_MODEL": "test-embedding",
    "DB_HOST": "localhost",
    "DB_PORT": "3306",
    "DB_USER": "test",
    "DB_PASSWORD": "test",
    "DB_NAME": "test",
    "DATABASE_URL": "sqlite+pysqlite:///:memory:",
    "TAVILY_API_KEY": "",
}

for _key, _value in _TEST_ENV.items():
    os.environ[_key] = _value


@pytest.fixture
def invalid_interview_state() -> dict:
    from backend.graph.runtime.contracts import WorkflowRuntime

    return {
        "round": 0,
        "max_rounds": 3,
        "resume_path": "",
        "resume_text": "",
        "target_position": "",
        "resume_validation": {},
        "resume_valid": False,
        "history": [],
        "question_review": {},
        "question_retry_count": 0,
        "question_rewrite_instruction": "",
        "learning_resources": "",
        "report": "",
        "is_finished": False,
        "runtime": WorkflowRuntime.new(run_id="invalid-test", workflow_version="2.0"),
    }


@pytest.fixture
def compiled_graph():
    from langgraph.checkpoint.memory import InMemorySaver
    from backend.graph.workflow import interview_workflow

    return interview_workflow.create_interview_graph(checkpointer=InMemorySaver())
