import getpass
import os

from dotenv import load_dotenv
from httpx import AsyncClient
from pydantic_ai.mcp import MCPServerHTTP
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

# for automation
from zrb import CmdTask, Group, HttpCheck, LLMTask, Task, cli, llm_config

load_dotenv()
LLM_API_KEY = os.getenv("BANKAI_LLM_API_KEY", f"{getpass.getuser()}-key")
# Gemini Base URL: https://generativelanguage.googleapis.com/v1beta/models/
LLM_BASE_URL = os.getenv("BANKAI_LLM_BASE_URL", "http://localhost:8000/v1beta/models/")
LLM_MODEL = os.getenv("BANKAI_LLM_MODEL", "gemini-2.0-flash")
LLM_PERSONA = """
You are Bankai, an AI Assistant in Private Banking.
You know about best practice and security in software engineering.
""".strip()


# Automation Tasks Definition
arasaka_group = cli.add_group(Group("arasaka", description="Arasaka Bank Automation"))

prepare_proxy_server = CmdTask(
    name="prepare-proxy",
    cwd=os.path.join(os.path.dirname(__file__), "proxy-server"),
    cmd="pip install -r requirements.txt",
)

prepare_mcp_server = CmdTask(
    name="prepare-mcp",
    cwd=os.path.join(os.path.dirname(__file__), "mcp-server"),
    cmd="pip install -r requirements.txt",
)

arasaka_group.add_task(
    Task(
        name="prepare-all",
        description="🍳 Prepare MCP and LLM Proxy Server",
        action=lambda ctx: ctx.print("🍳 Wokeh..."),
        upstream=[prepare_proxy_server, prepare_mcp_server],
    )
)

start_proxy_server = CmdTask(
    name="start-proxy",
    cwd=os.path.join(os.path.dirname(__file__), "proxy-server"),
    cmd="python main.py",
    readiness_check=HttpCheck(
        name="check-proxy", url="http://localhost:8000/health", interval=1
    ),
    readiness_check_delay=1,
)

start_mcp_server = CmdTask(
    name="start-mcp",
    cwd=os.path.join(os.path.dirname(__file__), "mcp-server"),
    cmd="python main.py",
    readiness_check=HttpCheck(
        name="check-mcp", url="http://localhost:8001/health", interval=1
    ),
    readiness_check_delay=1,
)

arasaka_group.add_task(
    Task(
        name="start-all",
        description="🚀 Start MCP and LLM Proxy Server",
        action=lambda ctx: ctx.print("🚀 Gacor..."),
        upstream=[start_proxy_server, start_mcp_server],
    )
)

# Bankai


class CustomGoogleGLAProvider(GoogleGLAProvider):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        http_client: AsyncClient | None = None,
    ) -> None:
        self._base_url = None
        if base_url is not None:
            self._base_url = base_url
        super().__init__(api_key, http_client=http_client)

    @property
    def base_url(self) -> str:
        if self._base_url is not None:
            return self._base_url
        return super().base_url


default_provider = CustomGoogleGLAProvider(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
    http_client=AsyncClient(timeout=30),
)
llm_config.set_default_persona(LLM_PERSONA)
llm_config.set_default_provider(default_provider)
llm_config.set_default_model(
    GeminiModel(model_name=LLM_MODEL, provider=default_provider)
)
llm_config.set_default_summarize_history(False)
llm_config.set_default_enrich_context(False)


server = MCPServerHTTP(url="http://localhost:8001/sse")
cli.add_task(
    LLMTask(
        name="test-mcp",
        mcp_servers=[server],
        message="Use the days_between tool to calculate the number of days between 2000-01-01 and 2025-03-18, then say hello to user",  # noqa
        retries=0,
    )
)
