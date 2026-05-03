"""
LLM Router — tries Groq → Gemini → Ollama in order.
Each provider is skipped if its API key is missing or the call fails.
"""

import os
import json
import re
import requests


def _strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _extract_json(text: str) -> dict:
    text = _strip_think(text)
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    start, end = text.find("{"), text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]
    return json.loads(text)


# ── Groq ───────────────────────────────────────────────────────────────────
def _call_groq(prompt: str, api_key: str, model: str = "llama-3.3-70b-versatile") -> str:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


# ── Gemini ─────────────────────────────────────────────────────────────────
def _call_gemini(prompt: str, api_key: str, model: str = "gemini-1.5-flash") -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096},
    }
    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


# ── Ollama ─────────────────────────────────────────────────────────────────
def _call_ollama(prompt: str, model: str = "deepseek-r1:latest") -> str:
    import ollama as ol
    response = ol.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.3, "num_predict": 4096},
    )
    return response["message"]["content"]


# ── Public interface ───────────────────────────────────────────────────────
def call_llm(prompt: str, keys: dict, ollama_model: str = "deepseek-r1:latest",
             need_json: bool = False) -> str:
    """
    keys = {"groq": "...", "gemini": "..."}  — missing/empty keys are skipped.
    Returns raw text. Caller parses JSON if needed.
    """
    errors = []

    if keys.get("groq"):
        try:
            return _call_groq(prompt, keys["groq"])
        except Exception as e:
            errors.append(f"Groq: {e}")

    if keys.get("gemini"):
        try:
            return _call_gemini(prompt, keys["gemini"])
        except Exception as e:
            errors.append(f"Gemini: {e}")

    try:
        return _call_ollama(prompt, ollama_model)
    except Exception as e:
        errors.append(f"Ollama: {e}")

    raise RuntimeError("All LLM providers failed:\n" + "\n".join(errors))


def call_llm_json(prompt: str, keys: dict, ollama_model: str = "deepseek-r1:latest") -> dict:
    raw = call_llm(prompt, keys, ollama_model, need_json=True)
    return _extract_json(raw)
