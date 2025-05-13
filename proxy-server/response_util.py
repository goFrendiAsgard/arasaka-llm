import logging

import httpx
from fastapi import Request
from fastapi.responses import Response, StreamingResponse


async def create_streamed_response(
    request: Request, original_response: Response
) -> Response:
    async def content_stream():
        try:
            async for chunk in original_response.aiter_text(chunk_size=10):
                yield chunk
                if await request.is_disconnected():
                    break
        except (
            httpx.ReadError,
            httpx.RemoteProtocolError,
            httpx.StreamClosed,
        ) as e:
            logging.error(f"Stream interrupted: {str(e)}")
        finally:
            await original_response.aclose()

    return StreamingResponse(
        content_stream(),
        status_code=original_response.status_code,
        headers={
            "Content-Type": original_response.headers.get(
                "Content-Type", "text/event-stream"
            ),
            "Cache-Control": "no-cache",
            **{
                k: v
                for k, v in original_response.headers.items()
                if k.lower() not in ["connection", "content-encoding"]
            },
        },
    )


async def create_unstreamed_response(original_response: Response) -> Response:
    content = await original_response.aread()
    await original_response.aclose()
    return Response(
        content=content,
        status_code=original_response.status_code,
        headers=dict(original_response.headers),
    )
