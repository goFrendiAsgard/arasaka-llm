from typing import Any

from config import (
    ALLOW_CUSTOM_LLM,
    EMBEDDING_API_URL,
    LLM_API_KEY,
    LLM_API_URL,
    LLM_MODEL,
)
from fastapi import Request
from starlette.datastructures import QueryParams


async def get_incoming_payload(request: Request) -> dict[str, Any]:
    try:
        return await request.json()
    except Exception:
        return {}


def get_outgoing_request_header(path: str, request: Request):
    # Note: Force no compression by setting Accept-Encoding to identity.
    if LLM_API_URL.startswith(
        "https://generativelanguage.googleapis.com"
    ) and path.startswith("v1beta/models"):
        return {
            "X-Goog-Api-Key": LLM_API_KEY,
            "Accept-Encoding": "identity",
        }
    elif path.startswith("v1/chat/completions"):
        return {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Accept-Encoding": "identity",
        }
    elif path.startswith("v1/embeddings"):
        return {
            "Accept-Encoding": "identity",
        }
    return dict(request.headers)


def get_outgoing_url(path: str) -> str:
    if LLM_API_URL.startswith(
        "https://generativelanguage.googleapis.com"
    ) and path.startswith("v1beta/models"):
        # v1beta/models/<model-name>:streamGenerateContent
        if not ALLOW_CUSTOM_LLM:
            path_parts = path.split("/")
            if len(path_parts) > 2:
                # <model-name>:streamGenerateContent
                segment = path_parts[2]
                segment_parts = segment.split(":")
                segment_parts[0] = LLM_MODEL
                segment = ":".join(segment_parts)
                path_parts[2] = segment
                path = "/".join(path_parts)
        return f"https://generativelanguage.googleapis.com/{path}"
    elif path.startswith("v1/chat/completions"):
        return f"{LLM_API_URL}/chat/completions"
    elif path.startswith("v1/embeddings"):
        return f"{EMBEDDING_API_URL}/embeddings"
    return f"{LLM_API_URL}/{path}"


def get_outgoing_query_params(
    request: Request, path: str
) -> QueryParams | dict[str, str] | None:
    query_params = request.query_params
    if LLM_API_URL.startswith(
        "https://generativelanguage.googleapis.com"
    ) and path.startswith("v1beta/models"):
        query_params = dict(query_params)
        if "key" in query_params:
            query_params["key"] = LLM_API_KEY
    return query_params


def should_stream(target_url: str, payload: dict[str, Any]) -> bool:
    if ":streamGenerateContent" in target_url:
        return True
    return bool(payload.get("stream", False))
