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


def _extract_text_with_br(tag) -> str:
    """Replace <br> tags with newlines and return the resulting text."""
    for br in tag.find_all("br"):
        br.replace_with("\n")
    return tag.get_text(separator="")


def _find_section_by_h4(soup, title: str):
    """Find a qt_cont_sec section whose h4.tit text matches title."""
    for section in soup.find_all("section", class_="qt_cont_sec"):
        h4 = section.find("h4", class_="tit")
        if h4 and h4.get_text(strip=True) == title:
            return section
    return None


def parse_meditation(html: str) -> dict:
    """Parse meditation HTML and return a dict with 6 keys."""
    soup = BeautifulSoup(html, "html.parser")

    # title
    meditation_section = soup.find("section", class_="qt_meditation")
    if not meditation_section:
        raise ValueError("Missing qt_meditation section")
    sbj = meditation_section.find("p", class_="sbj")
    if not sbj:
        raise ValueError("Missing title (p.sbj)")
    title = sbj.get_text(strip=True)

    # bible_book: first p.word, text after ":"
    word = meditation_section.find("p", class_="word")
    if not word:
        raise ValueError("Missing bible_book (p.word)")
    word_text = word.get_text(strip=True)
    if ":" not in word_text:
        raise ValueError("Unexpected bible_book format")
    bible_book = word_text.split(":", 1)[1].strip()

    # bible_verse: section with h4="오늘의 한 구절", [개역개정] portion only
    verse_section = _find_section_by_h4(soup, "오늘의 한 구절")
    if not verse_section:
        raise ValueError("Missing section '오늘의 한 구절'")
    verse_div = verse_section.find("div", class_="cont")
    if not verse_div:
        raise ValueError("Missing div.cont in '오늘의 한 구절'")
    verse_raw = _extract_text_with_br(verse_div)
    # 개역개정과 새번역 모두 포함, 레이블을 깔끔하게 포맷팅
    lines = [line.strip() for line in verse_raw.strip().split("\n") if line.strip()]
    formatted = []
    for line in lines:
        if line == "[개역개정]":
            formatted.append("[개역개정]")
        elif line == "[새번역]":
            formatted.append("\n[새번역]")
        else:
            formatted.append(line)
    bible_verse = "\n".join(formatted).strip()

    # meditation: section with h4="한 구절 묵상"
    med_section = _find_section_by_h4(soup, "한 구절 묵상")
    if not med_section:
        raise ValueError("Missing section '한 구절 묵상'")
    med_div = med_section.find("div", class_="cont")
    if not med_div:
        raise ValueError("Missing div.cont in '한 구절 묵상'")
    meditation = _extract_text_with_br(med_div).strip()

    # question: section with h4="묵상질문"
    q_section = _find_section_by_h4(soup, "묵상질문")
    if not q_section:
        raise ValueError("Missing section '묵상질문'")
    q_div = q_section.find("div", class_="cont")
    if not q_div:
        raise ValueError("Missing div.cont in '묵상질문'")
    question = _extract_text_with_br(q_div).strip()

    # prayer: section with h4="심정이 통하는 기도", exclude "함께 기도" and after
    prayer_section = _find_section_by_h4(soup, "심정이 통하는 기도")
    if not prayer_section:
        raise ValueError("Missing section '심정이 통하는 기도'")
    prayer_div = prayer_section.find("div", class_="cont")
    if not prayer_div:
        raise ValueError("Missing div.cont in '심정이 통하는 기도'")
    prayer_raw = _extract_text_with_br(prayer_div)
    # "함께 기도" 부분도 포함, 줄바꿈 정리
    lines = [line.strip() for line in prayer_raw.strip().split("\n") if line.strip()]
    formatted = []
    for line in lines:
        if line.startswith("함께 기도"):
            formatted.append("\n" + line)
        else:
            formatted.append(line)
    prayer = "\n".join(formatted).strip()

    return {
        "title": title,
        "bible_book": bible_book,
        "bible_verse": bible_verse,
        "meditation": meditation,
        "question": question,
        "prayer": prayer,
    }


async def crawl_today(date_str: str) -> dict:
    """Fetch and parse meditation for the given date string (YYYY-MM-DD)."""
    url = CRAWL_URL.format(date=date_str)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
    return parse_meditation(response.text)


async def crawl_and_save() -> bool:
    """Crawl today's meditation (KST) and save it. Skip if already saved."""
    try:
        date_str = datetime.now(KST).strftime("%Y-%m-%d")
        contents = load_json()
        if date_str in contents:
            logger.info("Data for %s already exists, skipping crawl.", date_str)
            return True
        data = await crawl_today(date_str)
        save_to_json(date_str, data)
        logger.info("Saved meditation for %s.", date_str)
        return True
    except Exception:
        logger.exception("Failed to crawl and save meditation.")
        return False
