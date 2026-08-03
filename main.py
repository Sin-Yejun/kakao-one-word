import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request

from kakao import make_response, make_error_response
from crawler import load_json, crawl_today

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

KST = ZoneInfo("Asia/Seoul")

app = FastAPI()


def get_today() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d")


@app.get("/")
async def health_check():
    return {"status": "ok"}


@app.post("/p1")
async def probe_no_body():
    """POST 자체가 되는지."""
    return {"ok": "p1"}


@app.post("/p2")
async def probe_raw_body(request: Request):
    """원시 본문을 읽을 수 있는지."""
    raw = await request.body()
    return {"ok": "p2", "len": len(raw)}


@app.post("/p3")
async def probe_json_body(request: Request):
    """JSON 파싱이 되는지."""
    body = await request.json()
    return {"ok": "p3", "keys": sorted(body.keys())}


@app.get("/debug")
async def debug():
    """배포 환경 점검용 임시 엔드포인트. 원인 확인 후 제거한다."""
    import os
    import sys
    import traceback

    from crawler import DATA_PATH

    info = {
        "cwd": os.getcwd(),
        "data_path": str(DATA_PATH),
        "data_exists": DATA_PATH.exists(),
        "today": None,
        "load_json": None,
        "webhook_trace": None,
    }
    try:
        info["today"] = get_today()
    except Exception:
        info["today"] = traceback.format_exc(limit=3)
    try:
        info["load_json"] = sorted(load_json().keys())
    except Exception:
        info["load_json"] = traceback.format_exc(limit=3)

    # 웹훅이 하는 일을 그대로 재현해서 터지는 지점을 잡는다
    try:
        data = load_json()
        entry = data.get(info["today"])
        if not entry:
            entry = await crawl_today(info["today"])
        info["webhook_trace"] = f"ok, title={entry['title']}"
    except Exception:
        info["webhook_trace"] = traceback.format_exc(limit=6)

    info["python"] = sys.version
    return info


@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    utterance = body.get("userRequest", {}).get("utterance", "")
    block_name = body.get("intent", {}).get("name", "")

    today = get_today()
    data = load_json()
    today_data = data.get(today)

    if not today_data:
        # 배포에 포함된 데이터가 오래됐을 때를 위한 보험. 서버 디스크는 읽기 전용이라
        # 저장하지 않고 이번 응답에만 쓴다.
        logger.info("오늘(%s) 데이터 없음 — 즉석 크롤링 시도", today)
        try:
            today_data = await crawl_today(today)
        except Exception:
            logger.exception("즉석 크롤링 실패")
            return make_error_response()

    title = today_data['title']
    date_label = f"[{today.replace('-', '.')}]"

    bible_ref = today_data.get('bible_ref', today_data['bible_book'])

    if block_name == "오늘의 말씀" or utterance == "오늘의 말씀":
        summary = today_data.get('summary', '')
        summary_block = f"📝 {summary}\n\n" if summary else ""
        text = f"📖 {date_label} {title} — {bible_ref}\n\n{summary_block}{today_data['bible_verse']}"
    elif block_name == "오늘의 묵상" or utterance == "오늘의 묵상":
        text = f"✍️ {date_label} {title}\n\n{today_data['meditation']}\n\n💬 묵상질문\n\n{today_data['question']}"
    elif block_name == "오늘의 기도" or utterance == "오늘의 기도":
        text = f"🙏 {date_label} {title}\n\n{today_data['prayer']}"
    else:
        text = "아래 버튼을 눌러 오늘의 묵상을 확인해 보세요 😊"

    return make_response(text)
