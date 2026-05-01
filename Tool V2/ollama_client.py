"""
LLM client for the Predictive Measles Risk Dashboard (orchestrator + tab helpers).

**Backends (first match wins after loading .env):**

1. **OpenAI** — set ``OPENAI_API_KEY`` (optional ``OPENAI_MODEL``, default ``gpt-4o-mini``).
2. **Ollama Cloud** — set ``OLLAMA_API_KEY`` if OpenAI is not configured.

No secrets in logs.
"""
from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, Optional

import requests

from utils.logging_config import get_logger

logger = get_logger("ollama_client")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OLLAMA_URL = "https://ollama.com/api/chat"
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
# Prefer cloud model tag; some setups use short name
OLLAMA_MODELS = ("gemma4:31b-cloud", "gpt-oss:20b-cloud", "gpt-oss:20b", "llama3.2:3b")
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
# Orchestrator user prompts include metrics + CDC tool summary + state ranking blocks; 8k truncated the tail
# and hid TOP STATES from the national reporter (ranking "unavailable" in prose).
MAX_PROMPT_CHARS = 28000


def _post_openai_chat_messages(messages: list[dict[str, Any]], *, timeout: int = 90) -> Optional[str]:
    """OpenAI Chat Completions API. Returns assistant text or None."""
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key:
        return None
    model = (os.environ.get("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    body: dict[str, Any] = {"model": model, "messages": messages}
    try:
        response = requests.post(OPENAI_CHAT_URL, headers=headers, json=body, timeout=timeout)
    except requests.RequestException as e:
        logger.error("OpenAI request failed reason=%s", e)
        return None
    if response.status_code != 200:
        logger.error("OpenAI request failed status=%s body=%s", response.status_code, response.text[:500])
        return None
    try:
        out = response.json()
        content = out["choices"][0]["message"]["content"]
        return (content or "").strip() or None
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
        logger.error("OpenAI parse failed reason=%s", e)
        return None


def _openai_chat_completions_raw(
    messages: list[dict[str, Any]],
    *,
    tools: Optional[list[dict[str, Any]]] = None,
    timeout: int = 90,
) -> Optional[dict[str, Any]]:
    """POST /v1/chat/completions; return parsed JSON or None."""
    _load_env()
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key:
        return None
    model = (os.environ.get("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    body: dict[str, Any] = {"model": model, "messages": messages}
    if tools is not None:
        body["tools"] = tools
    try:
        response = requests.post(OPENAI_CHAT_URL, headers=headers, json=body, timeout=timeout)
    except requests.RequestException as e:
        logger.error("OpenAI request failed reason=%s", e)
        return None
    if response.status_code != 200:
        logger.error("OpenAI request failed status=%s body=%s", response.status_code, response.text[:500])
        return None
    try:
        return response.json()
    except json.JSONDecodeError as e:
        logger.error("OpenAI JSON parse failed reason=%s", e)
        return None


def chat_completion_with_tools_openai(
    system: str,
    user: str,
    *,
    tools: list[dict[str, Any]],
    on_tool_call: Callable[[str, dict[str, Any]], str],
    timeout_s: int = 90,
    max_tool_rounds: int = 4,
) -> Optional[str]:
    """
    OpenAI Chat Completions with function tools: run tool handlers when the model requests them,
    then continue until the model returns text (no tool_calls). Returns None if not using OpenAI or on error.

    **Requires OPENAI_API_KEY.** Ollama does not use this path — callers should fall back to ``chat_completion``.
    """
    _load_env()
    if not (os.environ.get("OPENAI_API_KEY") or "").strip():
        logger.warning("chat_completion_with_tools_openai: OPENAI_API_KEY not set")
        return None
    system = system or ""
    user = user or ""
    if len(system) + len(user) > MAX_PROMPT_CHARS:
        budget = max(0, MAX_PROMPT_CHARS - len(system) - len("\n... (truncated)"))
        user = user[:budget] + "\n... (truncated)"
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    for _ in range(max_tool_rounds):
        data = _openai_chat_completions_raw(messages, tools=tools, timeout=timeout_s)
        if data is None:
            return None
        try:
            choice = data["choices"][0]
            msg = choice["message"]
        except (KeyError, IndexError, TypeError) as e:
            logger.error("OpenAI tool response shape error reason=%s", e)
            return None
        tool_calls = msg.get("tool_calls")
        content = msg.get("content")
        if tool_calls:
            assistant_msg: dict[str, Any] = {"role": "assistant", "tool_calls": tool_calls}
            assistant_msg["content"] = content if content else None
            messages.append(assistant_msg)
            for tc in tool_calls:
                try:
                    tid = tc["id"]
                    fn = tc.get("function") or {}
                    name = fn.get("name", "")
                    raw_args = fn.get("arguments") or "{}"
                    args = json.loads(raw_args) if isinstance(raw_args, str) else {}
                except (KeyError, TypeError, json.JSONDecodeError) as e:
                    logger.warning("Bad tool_call payload reason=%s", e)
                    tid = tc.get("id", "")
                    name = ""
                    args = {}
                    tool_content = f"Invalid tool request: {e}"
                else:
                    tool_content = on_tool_call(name, args)
                messages.append({"role": "tool", "tool_call_id": tid, "content": tool_content})
            continue
        if content and str(content).strip():
            return str(content).strip()
        return None
    logger.warning("chat_completion_with_tools_openai: max_tool_rounds exceeded")
    return None


def _post_ollama_chat_messages(messages: list[dict[str, Any]], *, timeout: int = 90) -> Optional[str]:
    """Ollama Cloud POST /api/chat with model fallback."""
    key = (os.environ.get("OLLAMA_API_KEY") or "").strip()
    if not key:
        logger.warning("Ollama skipped: OLLAMA_API_KEY not set")
        return None
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    response = None
    for model in OLLAMA_MODELS:
        body = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        try:
            response = requests.post(OLLAMA_URL, headers=headers, json=body, timeout=timeout)
        except requests.RequestException as e:
            logger.error("Ollama request failed reason=%s", e)
            return None
        if response.status_code == 200:
            break
        if response.status_code in (404, 422):
            logger.warning("Ollama model %s not available status=%s", model, response.status_code)
            continue
        logger.error("Ollama request failed status=%s body=%s", response.status_code, response.text[:300])
        return None
    else:
        logger.error("Ollama: no model succeeded")
        return None
    try:
        out = response.json()
        report = out.get("message", {}).get("content", "")
        return (report or "").strip() or None
    except (KeyError, json.JSONDecodeError) as e:
        logger.error("Ollama parse failed reason=%s", e)
        return None


def _post_chat_messages(messages: list[dict[str, Any]], *, timeout: int = 90) -> Optional[str]:
    """
    Route to OpenAI or Ollama. Shared by dashboard helpers and orchestrator agents.

    If ``OPENAI_API_KEY`` is set, OpenAI is used. Otherwise ``OLLAMA_API_KEY`` / Ollama Cloud.
    Returns assistant text or None (missing key, HTTP error, parse error).
    """
    _load_env()
    if (os.environ.get("OPENAI_API_KEY") or "").strip():
        return _post_openai_chat_messages(messages, timeout=timeout)
    if (os.environ.get("OLLAMA_API_KEY") or "").strip():
        return _post_ollama_chat_messages(messages, timeout=timeout)
    logger.warning("LLM skipped: set OPENAI_API_KEY or OLLAMA_API_KEY")
    return None


def chat_completion(system: str, user: str, *, timeout_s: int = 90) -> Optional[str]:
    """
    System + user chat for multi-agent orchestration. Truncates user text if the combined
    payload exceeds MAX_PROMPT_CHARS (system kept intact).
    """
    system = system or ""
    user = user or ""
    if len(system) + len(user) > MAX_PROMPT_CHARS:
        budget = max(0, MAX_PROMPT_CHARS - len(system) - len("\n... (truncated)"))
        user = user[:budget] + "\n... (truncated)"
    return _post_chat_messages(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        timeout=timeout_s,
    )


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
        load_dotenv(Path(__file__).resolve().parent / ".env")
    except ImportError:
        pass


def get_ollama_summary(
    alarm_probability: float,
    baseline_tier: str,
    forecast_summary: str,
    top_drivers: Optional[list] = None,
    data_as_of: str = "",
    extra_context: str = "",
) -> Optional[str]:
    """
    Send current risk summary to the configured LLM (OpenAI or Ollama Cloud); return AI-generated interpretation.
    On failure (missing key, timeout, 4xx/5xx) returns None and logs (no key).
    """
    drivers_str = ""
    if top_drivers:
        drivers_str = "Top drivers of outbreak alarm: " + "; ".join(str(d) for d in top_drivers[:5])
    payload_text = (
        f"Measles risk dashboard summary (data as of {data_as_of or 'N/A'}):\n"
        f"- Probability of outbreak in next 4 weeks (alarm): {alarm_probability:.1%}\n"
        f"- Baseline risk tier: {baseline_tier}\n"
        f"- {forecast_summary}\n"
        f"{drivers_str}\n"
        f"{extra_context}"
    )
    if len(payload_text) > MAX_PROMPT_CHARS:
        payload_text = payload_text[:MAX_PROMPT_CHARS] + "\n... (truncated)"
    prompt = (
        "Below is a short summary of measles surveillance data and a predictive risk model (outbreak alarm and case forecast). "
        "Write 2-3 short paragraphs in plain language: (1) what the current alarm and baseline risk suggest, "
        "(2) what the forecast implies for the next few weeks, and (3) one cautious recommendation. "
        "Do not make up numbers; only use the provided data. Use clear, non-technical language.\n\n"
        f"{payload_text}"
    )
    return _post_chat_messages([{"role": "user", "content": prompt}], timeout=90)


def get_ollama_follow_up(question: str, context_summary: str) -> Optional[str]:
    """
    Send a user follow-up question with current context. Returns answer or None.
    """
    prompt = f"Context from the measles risk dashboard:\n{context_summary[:4000]}\n\nUser question: {question}\n\nAnswer in 1-2 short paragraphs using only the context and data provided."
    return _post_chat_messages([{"role": "user", "content": prompt}], timeout=90)


def get_ollama_forecast_interpretation(
    forecast_table_summary: str,
    national_forecast_line: str = "",
    data_as_of: str = "",
) -> Optional[str]:
    """
    Generate a short AI interpretation of the forecast-by-state table and national outlook.
    Output must include: Hotspots (top states), Universal precautions, CDC reference link, and key CDC facts.
    """
    cdc_facts = (
        "Key CDC facts (paraphrase in your response where relevant): measles is highly contagious (airborne; virus can remain in a room up to about 2 hours). "
        "Symptoms typically appear 7–14 days after exposure: fever, cough, runny nose, conjunctivitis, rash. "
        "MMR vaccine: 2 doses about 97%% effective; 1 dose about 93%%."
    )
    prompt = (
        f"Measles risk dashboard — forecast (data as of {data_as_of or 'N/A'}):\n"
        f"{forecast_table_summary}\n"
        f"{national_forecast_line}\n\n"
        f"{cdc_facts}\n\n"
        "Your response MUST include these sections:\n"
        "(1) **Hotspots** — List the current hotspot states (from the summary above) with their risk scores.\n"
        "(2) **Outlook** — What the state-level outlooks (High / Watch / Low) and drivers suggest overall; one practical takeaway.\n"
        "(3) **Universal precautions** — Vaccination/MMR, hand hygiene, staying home when sick, masking in high-risk settings, seeking care for concerning symptoms. Keep practical and non-alarmist.\n"
        "(4) **CDC reference** — Include this line: CDC measles information: https://www.cdc.gov/measles/about/index.html\n"
        "Use clear, non-technical language. Do not make up numbers."
    )
    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = prompt[:MAX_PROMPT_CHARS] + "\n... (truncated)"
    return _post_chat_messages([{"role": "user", "content": prompt}], timeout=90)


def get_ollama_ww_nndss_report(summary_text: str, data_as_of: str = "") -> Optional[str]:
    """
    Generate an AI report comparing wastewater detection to NNDSS cases: trends, lead time, divergence, and cautions.
    """
    prompt = (
        "Measles risk dashboard — Wastewater vs NNDSS (data as of %s):\n\n%s\n\n"
        "Write a short comparative report in plain language. Include: (1) Current NNDSS weekly cases trend over the last 4–8 weeks (up/down/flat). "
        "(2) Current wastewater detection_frequency trend (this is the share of reporting sites that detected measles RNA; explain what that means in one sentence). "
        "(3) Whether wastewater appears to lead reported cases and by how many weeks, based on the best lag. "
        "(4) Any divergence (e.g. wastewater rising while cases flat). "
        "(5) A brief caution: correlation does not prove causation; reporting delays and sparse case counts can make correlation noisy. "
        "Use clear, non-technical language. Do not make up numbers."
        % (data_as_of or "N/A", summary_text[:5000])
    )
    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = prompt[:MAX_PROMPT_CHARS] + "\n... (truncated)"
    return _post_chat_messages([{"role": "user", "content": prompt}], timeout=90)


def get_ollama_state_report(
    state_name: str,
    risk_tier: str,
    risk_score: float,
    coverage_pct: Optional[float] = None,
    data_as_of: str = "",
) -> Optional[str]:
    """
    Generate a short AI narrative report for a single state. Returns plain-language summary or None.
    """
    cov_str = f"Kindergarten MMR coverage: {coverage_pct:.1f}%." if coverage_pct is not None else "Coverage data not shown."
    prompt = (
        f"Measles risk dashboard — state report for **{state_name}** (data as of {data_as_of or 'N/A'}):\n"
        f"- Risk tier: {risk_tier}\n"
        f"- Risk score (0–100): {risk_score}\n"
        f"- {cov_str}\n\n"
        "Write 2 short paragraphs in plain language: (1) what this state's risk tier and score mean for measles outbreak risk, "
        "and (2) one practical takeaway (e.g. for public health awareness or vaccination). Use clear, non-technical language. Do not make up numbers."
    )
    return _post_chat_messages([{"role": "user", "content": prompt}], timeout=90)
