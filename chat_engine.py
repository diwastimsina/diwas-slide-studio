"""
Chat engine — interprets user modification requests and updates the slide deck JSON.
"""

import json
from llm_router import call_llm_json, call_llm

INITIAL_ANALYSIS_PROMPT = """You are a world-class presentation strategist. Analyze the document below and return a JSON object describing a compelling, visually rich presentation.

DOCUMENT:
{text}

Return ONLY valid JSON (no markdown, no explanation):
{{
  "title": "Presentation title",
  "subtitle": "One-line subtitle",
  "theme": "professional",
  "slides": [
    {{
      "type": "title",
      "title": "...",
      "subtitle": "..."
    }},
    {{
      "type": "bullets",
      "title": "Slide title",
      "bullets": ["Point 1", "Point 2", "Point 3"],
      "speaker_notes": "What to say here"
    }},
    {{
      "type": "chart_bar",
      "title": "Chart title",
      "description": "One sentence about this data",
      "data": {{
        "labels": ["Category A", "Category B", "Category C"],
        "values": [42, 78, 35],
        "xlabel": "Categories",
        "ylabel": "Values"
      }}
    }},
    {{
      "type": "chart_pie",
      "title": "Distribution title",
      "description": "One sentence",
      "data": {{
        "labels": ["Segment 1", "Segment 2", "Segment 3"],
        "values": [45, 30, 25]
      }}
    }},
    {{
      "type": "two_column",
      "title": "Comparison title",
      "left_header": "Left side",
      "left_points": ["Point A", "Point B"],
      "right_header": "Right side",
      "right_points": ["Point C", "Point D"]
    }},
    {{
      "type": "quote",
      "quote": "An impactful quote or key insight from the document",
      "attribution": "Source or context"
    }},
    {{
      "type": "closing",
      "title": "Conclusion title",
      "bullets": ["Key takeaway 1", "Key takeaway 2", "Key takeaway 3"],
      "call_to_action": "What the audience should do next"
    }}
  ]
}}

Rules:
- Generate 8-12 slides total
- Include at least 2 charts (bar and pie) with realistic data from the document
- Mix slide types for visual variety
- Make bullet points punchy (max 10 words each)
- First slide must be type "title", last must be type "closing"
"""

MODIFY_PROMPT = """You are a presentation editor. The user wants to modify their slide deck.

CURRENT SLIDE DECK JSON:
{current_json}

USER REQUEST:
"{user_request}"

DOCUMENT CONTEXT (for reference when adding new content):
{doc_context}

Apply the user's request and return the COMPLETE updated slide deck JSON.
Keep all slides that were not mentioned. Only change what the user asked for.

Valid slide types: title, bullets, chart_bar, chart_pie, two_column, quote, closing
Valid themes: professional, modern, minimal, bold

Return ONLY valid JSON with the same structure as the input. No explanation, no markdown fences."""

INTENT_PROMPT = """Classify this user message into one of these categories:
- "modify" — wants to change, update, add, remove, or adjust the presentation
- "question" — asking a question about the content or presentation
- "chat" — general conversation not about the presentation

User message: "{message}"

Reply with just one word: modify, question, or chat"""

ANSWER_PROMPT = """The user has a question about their presentation or document.

SLIDE DECK:
{current_json}

DOCUMENT CONTEXT:
{doc_context}

USER QUESTION: "{question}"

Answer helpfully and concisely in 2-4 sentences."""


def analyze_document(text: str, keys: dict, ollama_model: str) -> dict:
    prompt = INITIAL_ANALYSIS_PROMPT.format(text=text)
    return call_llm_json(prompt, keys, ollama_model)


def detect_intent(message: str, keys: dict, ollama_model: str) -> str:
    prompt = INTENT_PROMPT.format(message=message)
    result = call_llm(prompt, keys, ollama_model).strip().lower()
    for intent in ("modify", "question", "chat"):
        if intent in result:
            return intent
    return "modify"  # default — assume modification


def modify_presentation(current_analysis: dict, user_request: str,
                        doc_context: str, keys: dict, ollama_model: str) -> dict:
    prompt = MODIFY_PROMPT.format(
        current_json=json.dumps(current_analysis, indent=2),
        user_request=user_request,
        doc_context=doc_context[:3000],
    )
    return call_llm_json(prompt, keys, ollama_model)


def answer_question(current_analysis: dict, question: str,
                    doc_context: str, keys: dict, ollama_model: str) -> str:
    prompt = ANSWER_PROMPT.format(
        current_json=json.dumps(current_analysis, indent=2),
        doc_context=doc_context[:3000],
        question=question,
    )
    return call_llm(prompt, keys, ollama_model)
