from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from question_loader import load_questions


@dataclass
class PipelineResult:
    pipeline: str
    question_id: str
    answer: str | None
    retrieved_context: list[str]
    token_usage: dict[str, int]
    notes: str


def _gemini_client() -> Any:
    """Return a Gemini client if the dependency and environment variable are available.

    This is intentionally lightweight so the repo can be run in a staged manner.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY in the environment before running the Gemini-backed pipeline.")

    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as exc:
        raise RuntimeError(
            f"Gemini client dependency is missing or misconfigured: {exc}. "
            "Install google-genai and configure GEMINI_API_KEY."
        ) from exc


def run_llm_only(question: dict[str, Any]) -> PipelineResult:
    # Placeholder implementation for the challenge’s baseline.
    question_id = str(question.get("question_id", "unknown"))
    return PipelineResult(
        pipeline="llm_only",
        question_id=question_id,
        answer=None,
        retrieved_context=[],
        token_usage={"input": 0, "output": 0, "total": 0},
        notes="Placeholder baseline; wire in Gemini client when the model runtime is ready.",
    )


def run_traditional_rag(question: dict[str, Any]) -> PipelineResult:
    question_id = str(question.get("question_id", "unknown"))
    return PipelineResult(
        pipeline="traditional_rag",
        question_id=question_id,
        answer=None,
        retrieved_context=[],
        token_usage={"input": 0, "output": 0, "total": 0},
        notes="Placeholder retrieval baseline; replace with chunker + vector store retrieval.",
    )


def run_graph_rag(question: dict[str, Any]) -> PipelineResult:
    question_id = str(question.get("question_id", "unknown"))
    return PipelineResult(
        pipeline="graph_rag",
        question_id=question_id,
        answer=None,
        retrieved_context=[],
        token_usage={"input": 0, "output": 0, "total": 0},
        notes="Placeholder graph pipeline; wire in TigerGraph + graph neighborhood selection.",
    )


def run_all(question_file: str | Path, output_file: str | Path) -> list[dict[str, Any]]:
    questions = load_questions(question_file)
    results: list[dict[str, Any]] = []

    for question in questions:
        qid = str(question.get("question_id", "unknown"))
        print(f"Processing {qid}...")

        llm_only = run_llm_only(question)
        rag = run_traditional_rag(question)
        graph = run_graph_rag(question)

        results.extend([
            asdict(llm_only),
            asdict(rag),
            asdict(graph),
        ])

    out = Path(output_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the three Round 3 pipeline skeletons.")
    parser.add_argument("--questions", required=True, help="Path to a CSV, JSON, or DOCX questions file.")
    parser.add_argument("--output", required=True, help="Path to write the per-question JSON results.")
    args = parser.parse_args()

    run_all(args.questions, args.output)
