"""Cover-letter generation for a shortlisted job.

Inputs: job record + resume markdown + optional voice samples.
Output: markdown cover letter tailored to the job.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import anthropic

SYSTEM_PROMPT = """You are a professional cover-letter writer. You adapt the
candidate's authentic voice and qualifications to the specific job posting. You
avoid AI-writing clichés (no 'I am writing to express my interest,' no 'In
today's fast-paced world,' no 'I am passionate about'). You write like a
thoughtful human professional who read the job posting carefully."""


def generate_cover_letter(
    *,
    job_title: str,
    job_company: str,
    job_description: str,
    resume_markdown: str,
    voice_sample: str = "",
    additional_context: str = "",
    model: str = "claude-opus-4-7",
    client: Optional[anthropic.Anthropic] = None,
) -> str:
    if client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        client = anthropic.Anthropic(api_key=api_key)

    user_prompt = f"""Job:
Title: {job_title}
Company: {job_company}
Description:
{job_description}

My resume (markdown):
{resume_markdown}

{f'Voice sample from me (match this tone):{chr(10)}{voice_sample}' if voice_sample else ''}

{f'Additional context:{chr(10)}{additional_context}' if additional_context else ''}

Write a cover letter for this job. Requirements:
- Under 400 words.
- Opens with a specific reference to something in the posting (not a greeting).
- Three middle paragraphs: one on the match, one on a specific prior experience,
  one on the value I'd bring to this specific company.
- Closes without clichés. No 'I look forward to hearing from you.'
- No em-dashes at the start of sentences.
- Return only the letter text. No preamble, no 'Here is the letter:' wrapper."""

    msg = client.messages.create(
        model=model,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return msg.content[0].text.strip()
