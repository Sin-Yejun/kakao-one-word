import json
import logging
from datetime import datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

KST = ZoneInfo("Asia/Seoul")
DATA_PATH = Path("data/meditation.json")
CRAWL_URL = "https://www.woorichurch.org/modu/ov/ov_meditation.asp?ov_date={date}&Page=1"


def load_json() -> dict:
    if not DATA_PATH.exists():
        return {}
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def save_to_json(date_str: str, data: dict) -> None:
    contents = load_json()
    contents[date_str] = data

    # 최신 3일치만 유지
    sorted_keys = sorted(contents.keys(), reverse=True)
    contents = {k: contents[k] for k in sorted_keys[:3]}

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(contents, ensure_ascii=False, indent=2), encoding="utf-8")
