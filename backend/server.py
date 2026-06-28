"""Server entry point for PortalOnline GMap Scraper API."""

import asyncio
import logging
import os
import signal

import uvicorn

from config import API_HOST, API_PORT

logger = logging.getLogger(__name__)


async def main():
    """Entry point: create FastAPI app, configure Uvicorn."""
    from api.app import create_app

    app = create_app()

    config = uvicorn.Config(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        loop="asyncio",
    )
    server = uvicorn.Server(config)

    loop = asyncio.get_event_loop()

    def _shutdown():
        logger.info("Received shutdown signal")
        server.should_exit = True

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _shutdown)
        except NotImplementedError:
            signal.signal(sig, lambda s, f: _shutdown())

    logger.info("Starting server on %s:%d", API_HOST, API_PORT)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
