import logging
import os

from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL_STR = os.getenv("PROXY_LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)

HTTP_PORT = int(os.getenv("PROXY_HTTP_PORT", "8000"))
ALLOW_CUSTOM_LLM = int(os.getenv("PROXY_ALLOW_CUSTOM_LLM", "0")) == 1

EMBEDDING_API_URL = os.getenv(
    "PROXY_EMBEDDING_API_URL", "http://localhost:11434/v1"
).rstrip("/")


LLM_API_KEY = os.getenv("PROXY_LLM_API_KEY")
LLM_API_URL = os.getenv(
    "PROXY_LLM_API_URL", "https://generativelanguage.googleapis.com/v1beta"
).rstrip("/")
LLM_MODEL = os.getenv("PROXY_LLM_MODEL", "gemini-2.5-flash-preview-04-17")
_DEFAULT_LLM_ALIGNMENT = """
Nilai luhur Bank Arasaka:
Integritas, Sikap Positif, Komitmen, Penyempurnaan Berkelanjutan, Inovatif, dan Loyal
""".strip()
LLM_ALIGNMENT = os.getenv("PROXY_LLM_ALIGNMENT", _DEFAULT_LLM_ALIGNMENT)

SUMMARIZATION_API_URL = os.getenv("PROXY_SUMMARIZATION_API_URL", LLM_API_URL).rstrip(
    "/"
)
SUMMARIZATION_API_KEY = os.getenv("PROXY_SUMMARIZATION_API_KEY", LLM_API_KEY)
SUMMARIZATION_MODEL = os.getenv("PROXY_SUMMARIZATION_API_MODEL", LLM_MODEL)
SUMMARIZATION_THRESHOLD = int(os.getenv("PROXY_SUMMARIZATION_THRESHOLD", "1000"))

_DEFAULT_SUMMARIZATION_PROMPT = """
You are a summarization assistant.
Your goal is to help main assistant to continue the conversation by creating an updated,
concise summary integrating the previous summary (if any) with the new conversation
history.
Preserve ALL critical context needed for the main assistant
to continue the task effectively. This includes key facts, decisions, tool usage
results, and essential background. Do not omit details that would force the main
assistant to re-gather information.
Output *only* the updated summary text.
""".strip()
SUMMARIZATION_SYSTEM_PROMPT = os.getenv(
    "PROXY_SUMMARIZATION_SYSTEM_PROMPT", _DEFAULT_SUMMARIZATION_PROMPT
)
