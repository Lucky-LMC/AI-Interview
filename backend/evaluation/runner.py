"""CLI entrypoint for key-free deterministic regression evaluation."""

import argparse
import json
from pathlib import Path
from typing import Any

from backend.evaluation.evaluators import evaluate_exact_route, evaluate_retrieval
from backend.evaluation.report import write_reports
from backend.graph.quality.question_quality import score_question_rules
from backend.graph.rag.service import RagResult, RetrievedChunk
from backend.graph.runtime.contracts import SourceRef
from backend.graph.runtime.policies import AgentPolicy


CASES_DIR = Path(__file__).parent / "cases"


def _load(name: str) -> list[dict[str, Any]]:
    return json.loads((CASES_DIR / name).read_text(encoding="utf-8"))


def _workflow_results() -> list[dict[str, Any]]:
    results = []
    for case in _load("workflow_cases.json"):
        actual = "valid" if case["resume_valid"] else "invalid"
        score = evaluate_exact_route(expected=case["expected_route"], actual=actual)
        results.append({"id": case["id"], "category": "workflow", **score.model_dump()})
    return results


def _agent_results() -> list[dict[str, Any]]:
    factories = {
        "interviewer": AgentPolicy.interviewer,
        "feedback": AgentPolicy.feedback,
        "consultant": AgentPolicy.consultant,
    }
    results = []
    for case in _load("agent_cases.json"):
        policy = factories[case["agent"]]()
        actual = {
            "model_run_limit": policy.model_run_limit,
            "global_tool_run_limit": policy.global_tool_run_limit,
            "tool_limits": policy.tool_limits,
        }
        passed = actual == case["expected_policy"]
        results.append({
            "id": case["id"],
            "category": "agent_policy",
            "passed": passed,
            "details": {"expected": case["expected_policy"], "actual": actual},
        })
    return results


def _question_results() -> list[dict[str, Any]]:
    results = []
    for case in _load("question_cases.json"):
        state = {
            "round": case["round"],
            "resume_text": case["resume_text"],
            "history": case.get("history", []),
        }
        actual = score_question_rules(case["question"], state).route
        score = evaluate_exact_route(expected=case["expected_route"], actual=actual)
        results.append({"id": case["id"], "category": "question", **score.model_dump()})
    return results


def _rag_results() -> list[dict[str, Any]]:
    results = []
    for case in _load("rag_cases.json"):
        rag_result = RagResult(
            query=case["query"],
            confidence=case["confidence"],
            fallback_required=case["fallback_required"],
            documents=[
                RetrievedChunk(
                    content="fixture",
                    content_hash=f"hash-{document_id}",
                    source=SourceRef(title=document_id, document_id=document_id),
                )
                for document_id in case["actual_document_ids"]
            ],
        )
        score = evaluate_retrieval(
            expected_document_ids=case["expected_document_ids"],
            actual=rag_result,
            expected_fallback=case["fallback_required"],
        )
        results.append({"id": case["id"], "category": "rag", **score.model_dump()})
    return results


def run_offline(output: Path) -> dict[str, int]:
    results = [
        *_workflow_results(),
        *_agent_results(),
        *_question_results(),
        *_rag_results(),
    ]
    return write_reports(output, results)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Run deterministic key-free cases")
    parser.add_argument("--output", type=Path, default=Path(".artifacts/evaluation"))
    args = parser.parse_args()
    if not args.offline:
        parser.error("Only --offline evaluation is enabled by default")
    summary = run_offline(args.output)
    print(json.dumps(summary, ensure_ascii=False))
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
