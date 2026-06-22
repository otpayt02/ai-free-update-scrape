"""Convenience entry point — run from project root: python run.py"""
import sys
from pathlib import Path

# Make sure src/ is on the path when running without uv install
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_free_update_scrape.schedule import run

if __name__ == "__main__":
    run()
