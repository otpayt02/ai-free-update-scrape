"""Launch the local scrape dashboard in a browser."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_free_update_scrape.web.app import run


if __name__ == "__main__":
    run(port=5052)
