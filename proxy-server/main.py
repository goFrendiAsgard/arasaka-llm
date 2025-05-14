import json
from contextlib import asynccontextmanager

import httpx
import uvicorn
from config import HTTP_PORT
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from log_util import logger
from payload_util import alter_payload
from request_util import (
    get_incoming_payload,
    get_outgoing_query_params,
    get_outgoing_request_header,
    get_outgoing_url,
    should_stream,
)
from response_util import create_streamed_response, create_unstreamed_response

app = FastAPI()
client = httpx.AsyncClient(timeout=30)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await client.alclose()


@app.get("/health")
async def get_health():
    return JSONResponse({"status": "ok"})


@app.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
)
async def proxy(path: str, request: Request):
    outgoing_url = get_outgoing_url(path)
    outgoing_headers = get_outgoing_request_header(path, request)
    incoming_payload = await get_incoming_payload(request)
    outgoing_payload = await alter_payload(path, incoming_payload)
    stream_enabled = should_stream(outgoing_url, incoming_payload)
    outgoing_query_params = get_outgoing_query_params(request, path)
    logger.debug(
        json.dumps(
            {
                "event": "start_redirection",
                "data": {
                    "incoming_path": path,
                    "outgoing_url": outgoing_url,
                    "incoming_headers": dict(request.headers),
                    "outgoing_headers": outgoing_headers,
                    "incoming_payload": incoming_payload,
                    "outgoing_payload": outgoing_payload,
                    "incoming_query_params": dict(request.query_params),
                    "outgoing_query_params": outgoing_query_params,
                },
            }
        )
    )
    try:
        req = client.build_request(
            method=request.method,
            url=outgoing_url,
            headers=outgoing_headers,
            content=json.dumps(outgoing_payload),
            params=outgoing_query_params,
        )
        response = await client.send(req, stream=stream_enabled)
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Service unavailable")
    if stream_enabled:
        return await create_streamed_response(request, response)
    else:
        return await create_unstreamed_response(response)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=HTTP_PORT)
