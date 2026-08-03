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
