"""Entry point: starts the web server on the local network."""

import logging
import socket

import uvicorn

from app.config import load_settings
from app.exceptions import InvalidBoardProfileError, InvalidSettingError
from app.main import create_app

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
# Any private address works: connecting a UDP socket sends no packets, it only picks a route.
ROUTE_PROBE_ADDRESS = ("10.254.254.254", 1)
LOOPBACK_ADDRESS = "127.0.0.1"

logger = logging.getLogger(__name__)


def find_local_ip() -> str:
    """Return this machine's address on the local network, or loopback if there is no route."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        try:
            probe.connect(ROUTE_PROBE_ADDRESS)
            return probe.getsockname()[0]
        except OSError:
            return LOOPBACK_ADDRESS


def main() -> None:
    """Load the settings, log how to reach the platform and start the server."""
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    settings = load_settings()

    try:
        app = create_app(settings)
    except (InvalidBoardProfileError, InvalidSettingError) as error:
        logger.error("Server not started. %s", error)
        raise SystemExit(1) from None

    address = f"http://{find_local_ip()}:{settings.port}"
    logger.info("Open %s on any device in the local network", address)

    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
