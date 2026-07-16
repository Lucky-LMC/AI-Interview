"""Evaluation report serialization."""

import json
from pathlib import Path
from typing import Any


def write_reports(output_dir: Path, results: list[dict[str, Any]]) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "total": len(results),
        "passed": sum(1 for item in results if item["passed"]),
        "failed": sum(1 for item in results if not item["passed"]),
    }
    payload = {"summary": summary, "results": results}
    (output_dir / "evaluation.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Offline Evaluation Report",
        "",
        f"- Total: {summary['total']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        "",
        "## Cases",
        "",
    ]
    for item in results:
        marker = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- [{marker}] `{item['id']}` ({item['category']})")
    (output_dir / "evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary
