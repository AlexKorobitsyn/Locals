import json
import logging
import os
import time
from urllib.error import URLError
from urllib.request import urlopen

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT_SECONDS = 60
RETRY_SECONDS = 1


def main():
    logging.basicConfig(level=logging.INFO)
    base = os.environ.get("SMOKE_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    expected = os.environ["EXPECTED_RELEASE_ID"]
    deadline = time.monotonic() + DEFAULT_TIMEOUT_SECONDS
    while True:
        try:
            with urlopen(base + "/api/v1/health/ready", timeout=3) as response:
                assert json.load(response) == {"status": "ok", "database": "ok"}
            break
        except (OSError, URLError):
            if time.monotonic() > deadline:
                raise RuntimeError("Image readiness check timed out") from None
            time.sleep(RETRY_SECONDS)
    with urlopen(base + "/api/v1/health/version", timeout=3) as response:
        assert json.load(response)["release_id"] == expected
    with urlopen(base + "/api/v1/openapi.json", timeout=3) as response:
        paths = json.load(response)["paths"]
        assert "/api/v1/recommendations/tracks" in paths
        assert "/api/v1/me/favorite-genres" in paths
    with urlopen(base + "/api/v1/recommendations/tracks", timeout=10) as response:
        result = json.load(response)
        assert result["algorithm_version"] == "rules_v1"
        assert result["mode"] == "popular"
    logger.info("Release image smoke checks passed")


if __name__ == "__main__":
    main()
