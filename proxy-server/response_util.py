from typing import Any

import httpx
import json
from fastapi import Request
from fastapi.responses import Response, StreamingResponse
from log_util import logger


async def create_streamed_response(
    request: Request, original_response: Response
) -> Response:
    async def content_stream():
        full_content = ""
        try:
            logger.info({"event": "stream_started"})
            async for chunk in original_response.aiter_text(chunk_size=10):
                yield chunk
                logger.debug(
                    json.dumps(
                        {
                            "event": "stream_chunk",
                            "chunk": chunk,
                        }
                    )
                )
                full_content += chunk
                if await request.is_disconnected():
                    logger.info({"event": "client_disconnected"})
                    break
        except (
            httpx.ReadError,
            httpx.RemoteProtocolError,
            httpx.StreamClosed,
        ) as e:
            logger.error({"event": "stream_error", "error": str(e)})
        finally:
            await original_response.aclose()
            logger.info(
                json.dumps(
                    {
                        "event": "stream_closed",
                        "content": full_content,
                        "headers": _get_streaming_header(original_response),
                    }
                )
            )

    return StreamingResponse(
        content_stream(),
        status_code=original_response.status_code,
        headers=_get_streaming_header(original_response),
    )


def _get_streaming_header(original_response: Response) -> dict[str, Any]:
    return {
        "Content-Type": original_response.headers.get(
            "Content-Type", "text/event-stream"
        ),
        "Cache-Control": "no-cache",
        **{
            k: v
            for k, v in original_response.headers.items()
            if k.lower() not in ["connection", "content-encoding"]
        },
    }


async def create_unstreamed_response(original_response: Response) -> Response:
    content = await original_response.aread()
    logger.info(
        ijson.dumps(
            {
                "event": "full_response_body",
                "status_code": original_response.status_code,
                "headers": dict(original_response.headers),
                "content": content,
            }
        )
    )
    await original_response.aclose()
    return Response(
        content=content,
        status_code=original_response.status_code,
        headers=dict(original_response.headers),
    )
