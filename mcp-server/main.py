import os

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

MCP_HTTP_PORT = int(os.getenv("MCP_HTTP_PORT", "8001"))
mcp = FastMCP("Demo 🚀")


@mcp.tool()
def hello(name: str) -> str:
    return f"Hello, {name}!"


@mcp.tool()
def days_between(start_date: str, end_date: str) -> int:
    from datetime import date

    y1, m1, d1 = map(int, start_date.split("-"))
    y2, m2, d2 = map(int, end_date.split("-"))
    date1 = date(y1, m1, d1)
    date2 = date(y2, m2, d2)
    return abs((date2 - date1).days)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=MCP_HTTP_PORT)
