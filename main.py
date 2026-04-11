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

    today = get_today()
    data = load_json()
    today_data = data.get(today)

    if not today_data:
        return make_error_response()

    if utterance == "오늘의 말씀":
        text = f"📖 {today_data['bible_book']}\n\n{today_data['bible_verse']}"
    elif utterance == "한 구절 묵상":
        text = f"✍️ 한 구절 묵상\n\n{today_data['meditation']}\n\n💬 묵상질문\n\n{today_data['question']}"
    elif utterance == "오늘의 기도":
        text = f"🙏 오늘의 기도\n\n{today_data['prayer']}"
    else:
        text = "아래 버튼을 눌러 오늘의 묵상을 확인해 보세요 😊"

    return make_response(text)
