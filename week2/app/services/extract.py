from __future__ import annotations

import os
import re
from typing import List
import json
from typing import Any
import requests
from dotenv import load_dotenv

load_dotenv()

# RunPod API configuration (synchronous endpoint)
RUNPOD_API_URL = "https://api.runpod.ai/v2/sb0nltoldikmr4/runsync"
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")

BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False


def extract_action_items(text: str) -> List[str]:
    lines = text.splitlines()
    extracted: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            # Trim common checkbox markers
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            extracted.append(cleaned)
    # Fallback: if nothing matched, heuristically split into sentences and pick imperative-like ones
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters


def _call_runpod_api(prompt: str) -> str:
    """
    Call the RunPod API endpoint with the given prompt.
    
    Args:
        prompt: The prompt to send to the LLM
        
    Returns:
        The response text from the LLM (model-generated text only)
        
    Raises:
        ValueError: If RUNPOD_API_KEY is not set
    """
    if not RUNPOD_API_KEY:
        raise ValueError("RUNPOD_API_KEY environment variable is not set")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
    }
    
    payload = {
        "input": {
            "prompt": prompt
        }
    }
    
    response = requests.post(RUNPOD_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()

    # RunPod synchronous endpoint typically returns the model output under "output"
    if "output" in result:
        output = result["output"]

        # Case 1: plain string
        if isinstance(output, str):
            return output

        # Case 2: dict with direct text
        if isinstance(output, dict):
            if "text" in output and isinstance(output["text"], str):
                return output["text"]

            # Case 3: OpenAI-style completion object
            if "choices" in output and isinstance(output["choices"], list) and output["choices"]:
                choice = output["choices"][0]
                if isinstance(choice, dict):
                    if "text" in choice and isinstance(choice["text"], str):
                        return choice["text"]
                    # Chat-style response
                    if (
                        "message" in choice
                        and isinstance(choice["message"], dict)
                        and "content" in choice["message"]
                        and isinstance(choice["message"]["content"], str)
                    ):
                        return choice["message"]["content"]

        # Case 4: list where first element may be a string or completion object
        if isinstance(output, list) and output:
            first = output[0]
            if isinstance(first, str):
                return first
            if isinstance(first, dict):
                if "text" in first and isinstance(first["text"], str):
                    return first["text"]
                if "choices" in first and isinstance(first["choices"], list) and first["choices"]:
                    choice = first["choices"][0]
                    if isinstance(choice, dict):
                        if "text" in choice and isinstance(choice["text"], str):
                            return choice["text"]
                        if (
                            "message" in choice
                            and isinstance(choice["message"], dict)
                            and "content" in choice["message"]
                            and isinstance(choice["message"]["content"], str)
                        ):
                            return choice["message"]["content"]

    # Fallback: return the entire output as JSON string
    return json.dumps(result.get("output", result))


def extract_action_items_llm(text: str) -> List[str]:
    """
    Extract action items from text using an LLM via RunPod API.
    
    This function uses a large language model to intelligently identify
    action items from free-form text, which can handle more complex
    patterns than the heuristic-based extract_action_items function.
    
    Args:
        text: The input text to extract action items from
        
    Returns:
        A list of extracted action items as strings
        
    Raises:
        ValueError: If RUNPOD_API_KEY is not set
        httpx.HTTPError: If the API request fails
    """
    if not text.strip():
        return []
    
    # Construct a prompt that asks for structured JSON output
    prompt = f"""Extract all action items from the following notes. Return ONLY a JSON array of strings, where each string is a clear, actionable item. Do not include any explanatory text, just the JSON array.

Notes:
{text}

Return format: ["action item 1", "action item 2", ...]"""

    try:
        response_text = _call_runpod_api(prompt)
        
        # Try to extract JSON from the response
        # The LLM might return JSON wrapped in markdown code blocks or with extra text
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            # Extract content between code blocks
            parts = response_text.split("```")
            if len(parts) >= 2:
                response_text = parts[1]
                # Remove language identifier if present (e.g., ```json)
                if "\n" in response_text:
                    response_text = response_text.split("\n", 1)[1]
        
        # Try to find JSON array in the response
        # Look for array pattern
        json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        # Parse JSON
        try:
            items = json.loads(response_text)
            if isinstance(items, list):
                # Filter out empty strings and ensure all items are strings
                result = [str(item).strip() for item in items if str(item).strip()]
                return result
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract items from the text
            # Look for list-like patterns
            lines = response_text.split("\n")
            extracted = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Remove common list markers
                line = re.sub(r'^[-*•]\s*', '', line)
                line = re.sub(r'^\d+\.\s*', '', line)
                line = line.strip('"\'')
                if line:
                    extracted.append(line)
            return extracted if extracted else []
        
        return []
        
    except Exception as e:
        # Log error and fallback to heuristic extraction
        # In production, you might want to use proper logging
        print(f"Error calling RunPod API: {e}")
        # Fallback to heuristic method
        return extract_action_items(text)
