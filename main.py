import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request

from kakao import make_response, make_error_response
from crawler import load_json

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
    entry_date = today
    today_data = data.get(today)

    if not today_data:
        # 카카오는 5초 안에 응답을 받아야 해서 이 자리에서 크롤링할 수 없다.
        # 대신 보관 중인 가장 최근 날짜를 그 날짜 그대로 보여준다.
        past = [d for d in data if d <= today]
        if not past:
            logger.error("서빙할 데이터가 전혀 없음 (오늘=%s)", today)
            return make_error_response()
        entry_date = max(past)
        today_data = data[entry_date]
        logger.warning("오늘(%s) 데이터 없음 — %s 데이터로 대체", today, entry_date)

    title = today_data['title']
    date_label = f"[{entry_date.replace('-', '.')}]"

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
