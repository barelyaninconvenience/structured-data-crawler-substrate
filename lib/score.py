"""LLM scoring against the 6-dimension rubric."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import anthropic

RUBRIC_PATH = Path(__file__).resolve().parent.parent / "rubric.md"


SYSTEM_PROMPT = """You are scoring a job posting for the overemployment endeavor.
A user wants to stack multiple remote jobs that can be largely automated via AI
tools. You score against a 6-dimension rubric (each 0-2, total /12). You return
strict JSON with no markdown fences."""


def _build_user_prompt(job_title: str, job_company: str, job_pay: str,
                        job_remote: str, job_description: str) -> str:
    rubric = RUBRIC_PATH.read_text(encoding="utf-8")
    return f"""Here is the rubric:

{rubric}

Here is the job:

Title: {job_title}
Company: {job_company}
Pay: {job_pay}
Remote status: {job_remote}
Description:
{job_description}

Score this job on the 6 dimensions. Return ONLY a JSON object with this exact structure:

{{
  "score_automatability": <0-2>,
  "score_oversight": <0-2>,
  "score_pay": <0-2>,
  "score_remote": <0-2>,
  "score_stakes": <0-2>,
  "score_flexibility": <0-2>,
  "red_flags": ["short string", "..."],
  "green_flags": ["short string", "..."],
  "verdict": "one sentence, under 150 chars",
  "recommend": "apply" | "maybe" | "skip"
}}

Follow the rubric's red-flag / green-flag keyword guidance strictly. If information
is missing, default to the middle score (1). If the job is clearly not remote,
score_remote must be 0."""


def score_job(
    *,
    title: str,
    company: str,
    pay: str,
    remote: str,
    description: str,
    model: str = "claude-sonnet-4-6",
    client: Optional[anthropic.Anthropic] = None,
) -> dict:
    if client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        client = anthropic.Anthropic(api_key=api_key)

    msg = client.messages.create(
        model=model,
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_prompt(
            title, company, pay, remote, description)}],
    )
    text = msg.content[0].text.strip()
    # Strip markdown fences if the model ignored the instruction
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        if text.startswith("json"):
            text = text[4:].lstrip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Model returned non-JSON: {text[:500]}") from e
