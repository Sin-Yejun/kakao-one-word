import logging
from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Request

from kakao import make_response, make_error_response
from crawler import load_json, crawl_and_save

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

KST = ZoneInfo("Asia/Seoul")

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작: 오늘 데이터 없으면 즉시 크롤링
    today = get_today()
    data = load_json()
    if today not in data:
        logger.info("오늘(%s) 데이터 없음 — 즉시 크롤링 시작", today)
        await crawl_and_save()

    # 스케줄러 등록: 05:00, 06:00, 07:00 KST
    for hour in [5, 6, 7]:
        scheduler.add_job(crawl_and_save, CronTrigger(hour=hour, minute=0))
    scheduler.start()
    logger.info("스케줄러 시작됨 (05:00, 06:00, 07:00 KST)")

    yield

    # 종료
    scheduler.shutdown()
    logger.info("스케줄러 종료됨")


app = FastAPI(lifespan=lifespan)


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
        return make_error_response()

    title = today_data['title']
    date_label = today.replace("-", ".")

    bible_ref = today_data.get('bible_ref', today_data['bible_book'])

    if block_name == "오늘의 말씀" or utterance == "오늘의 말씀":
        text = f"📖 {date_label} {title} — {bible_ref}\n\n{today_data['bible_verse']}"
    elif block_name == "오늘의 묵상" or utterance == "오늘의 묵상":
        text = f"✍️ {date_label} {title}\n\n{today_data['meditation']}\n\n💬 묵상질문\n\n{today_data['question']}"
    elif block_name == "오늘의 기도" or utterance == "오늘의 기도":
        text = f"🙏 {date_label} {title}\n\n{today_data['prayer']}"
    else:
        text = "아래 버튼을 눌러 오늘의 묵상을 확인해 보세요 😊"

    return make_response(text)
