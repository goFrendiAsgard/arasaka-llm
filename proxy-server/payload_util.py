import hashlib
import json
from copy import deepcopy
from typing import Any

from cache.factory import get_cache
from config import (
    LLM_ALIGNMENT,
    LLM_API_KEY,
    LLM_API_URL,
    SUMMARIZATION_MODEL,
    SUMMARIZATION_SYSTEM_PROMPT,
    SUMMARIZATION_THRESHOLD,
)
from log_util import logger
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.usage import Usage


async def alter_payload(original_payload: Any) -> Any:
    if not isinstance(original_payload, dict):
        return original_payload
    payload = deepcopy(original_payload)
    payload = maybe_inject_alignment(payload)
    payload = await maybe_inject_summarization(payload)
    return payload


def maybe_inject_alignment(payload: dict[str, Any]) -> dict[str, Any]:
    return maybe_inject_system_prompt(payload, LLM_ALIGNMENT)


async def maybe_inject_summarization(payload: dict[str, Any]):
    if "contents" not in payload:
        return payload
    previous_summary, retained_conversation = extract_previous_summary(
        payload["contents"]
    )
    new_summary, retained_conversation = await maybe_summarize(
        previous_summary, retained_conversation
    )
    payload = maybe_inject_system_prompt(
        payload, f"\n#Previous conversation: {new_summary}"
    )
    payload["contents"] = retained_conversation
    return payload


async def maybe_summarize(
    previous_summary: str, recent_conversation: list[str]
) -> tuple[str, list[str]]:
    to_be_summarized_conversation, retained_conversation = split_conversation(
        recent_conversation
    )
    if len(to_be_summarized_conversation) == 0:
        return previous_summary, recent_conversation
    if len(json.dumps(recent_conversation)) < SUMMARIZATION_THRESHOLD:
        return previous_summary, recent_conversation
    to_be_summarized_conversation_str = json.dumps(to_be_summarized_conversation)
    if LLM_API_URL.startswith("https://generativelanguage.googleapis.com"):
        agent = Agent(
            model=GeminiModel(
                model_name=SUMMARIZATION_MODEL,
                provider=GoogleGLAProvider(api_key=LLM_API_KEY),
            ),
            system_prompt=SUMMARIZATION_SYSTEM_PROMPT,
        )
        agent_run_result = await agent.run(
            user_prompt=(
                f"Previous conversation: {previous_summary}",
                f"Recent conversation: {to_be_summarized_conversation_str}",
                "Summarize the conversation into a single paragraph, retain important contexts so that the main assistant can continue the conversation",  # noqa
            )
        )
        logger.info(
            json.dumps(
                {
                    "event": "finish_summarization",
                    "data": {
                        "usage": usage_to_dict(agent_run_result.usage()),
                        "new_summary": agent_run_result.output,
                        "retained_conversation": retained_conversation,
                    },
                }
            )
        )
        return agent_run_result.output, retained_conversation
    return previous_summary, recent_conversation


def usage_to_dict(usage: Usage) -> dict[str, Any]:
    return {
        "request_tokens": usage.request_tokens,
        "response_tokens": usage.response_tokens,
        "total_tokens": usage.total_tokens,
        "details": usage.details,
    }


def split_conversation(conversation: list[str]) -> tuple[list[str], list[str]]:
    """
    Split conversation into two parts:
    - conversation to be summarized
    - conversation should be retained
    We need to retain last part of conversation
    """
    if len(conversation) < 2:
        return [], conversation
    # Pivot example: {'role': 'user', 'parts': [{'text': '...'}]}
    pivot = len(conversation) - 2
    while pivot > 0:
        has_role = "role" in conversation[pivot]
        is_user_role = has_role and conversation[pivot]["role"] == "user"
        has_parts = is_user_role and "parts" in conversation[pivot]
        has_part_list = has_parts and len(conversation[pivot]["parts"]) > 0
        has_text = has_part_list and "text" in conversation[pivot]["parts"][0]
        if has_text:
            return conversation[:pivot], conversation[pivot:]
        pivot -= 1
    return [], conversation


def maybe_inject_system_prompt(payload: dict[str, Any], data: str) -> str:
    has_system_instruction = "systemInstruction" in payload
    has_parts = has_system_instruction and "parts" in payload["systemInstruction"]
    has_parts_list = has_parts and len(payload["systemInstruction"]["parts"]) > 0
    has_text = has_parts_list and "text" in payload["systemInstruction"]["parts"][0]
    if has_text:
        payload["systemInstruction"]["parts"][0]["text"] += data
    return payload


def extract_previous_summary(contents: list[Any]) -> tuple[str, list[Any]]:
    pivot = get_summarization_pivot(contents)
    recent_conversation = contents[pivot:]
    previous_summarization_key = get_summarization_key(contents[:pivot])
    cache = get_cache()
    if cache.key_exists(previous_summarization_key):
        return cache.get(previous_summarization_key), recent_conversation
    return "<Empty>", recent_conversation


def get_summarization_pivot(contents: list[Any]):
    pivot = len(contents)
    cache = get_cache()
    while pivot > 0:
        if cache.key_exists(get_summarization_key(contents[:pivot])):
            return pivot
        pivot -= 1
    return pivot


def get_summarization_key(contents: list[Any]):
    content_str = json.dumps(contents)
    hash_object = hashlib.md5(content_str.encode("utf-8"))
    md5_hash = hash_object.hexdigest()
    return md5_hash
