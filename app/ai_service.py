"""
AI Service Module - OpenRouter Integration
"""

import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# List of free models to try in order (fastest first)
FREE_MODELS = [
    "meta-llama/llama-3.2-3b-instruct:free",    # Fastest - small model
    "google/gemma-3-4b-it:free",                 # Fast - small model
    "qwen/qwen3-4b:free",                        # Fast - small model
    "mistralai/mistral-small-3.1-24b-instruct:free",  # Medium
    "meta-llama/llama-3.3-70b-instruct:free",    # Slowest but most powerful
]


def call_ai(prompt: str, max_tokens: int = 1024) -> str:
    """Call OpenRouter API, trying each free model until one works."""
    load_dotenv(override=True)
    api_key = os.environ.get('OPENROUTER_API_KEY', '')

    if not api_key or api_key == 'your_openrouter_api_key_here':
        return "❌ API key not set. Please add OPENROUTER_API_KEY to your .env file."

    for model in FREE_MODELS:
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }).encode("utf-8")

        req = urllib.request.Request(
            OPENROUTER_API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "StudyHub"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                if content and len(content) > 5:
                    return content
        except Exception:
            continue  # Try next model

    return "❌ All AI models are currently unavailable. Please try again in a moment."


def summarize_note(title: str, content: str) -> str:
    return call_ai(f"""You are a helpful study assistant. Summarize this study note in 3-5 bullet points focusing on key concepts.

Note Title: {title}
Note Content: {content}

Bullet-point summary:""")


def generate_quiz(title: str, content: str) -> str:
    return call_ai(f"""You are a study assistant. Generate 5 quiz questions with answers based on this note. Mix multiple choice, short answer, and true/false.

Note Title: {title}
Note Content: {content}

Format:
Q1: [Question]
Answer: [Answer]""", max_tokens=1500)


def explain_topic(title: str, content: str) -> str:
    return call_ai(f"""You are a friendly tutor. Explain this study note simply for a new student. Use analogies where helpful.

Note Title: {title}
Note Content: {content}

Simple explanation:""")


def improve_note(title: str, content: str) -> str:
    return call_ai(f"""You are an expert study coach. Review this note and suggest:
1. Missing important points
2. Better organization
3. Key terms to define
4. Related topics to explore

Note Title: {title}
Note Content: {content}

Suggestions:""")


def chat_with_note(title: str, content: str, user_question: str) -> str:
    return call_ai(f"""You are a study assistant. Answer the student's question based on their note.

Note Title: {title}
Note Content: {content}

Question: {user_question}
Answer:""")


def generate_study_plan(subjects_data: list) -> str:
    subjects_summary = "\n".join([
        f"- {s['name']}: {s['note_count']} notes"
        for s in subjects_data
    ])
    return call_ai(f"""You are a study coach. Create a practical 7-day study plan for a student with these subjects:

{subjects_summary}

Include daily time slots, subject tips, and encouragement:""", max_tokens=1500)
