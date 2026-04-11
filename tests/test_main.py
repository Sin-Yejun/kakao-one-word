import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture
def sample_data():
    return {
        "2026-04-11": {
            "title": "하나님을 인정하는 삶",
            "bible_book": "창세기 14장",
            "bible_ref": "창세기 14장 20절",
            "bible_verse": "[개역개정]\n20 너희 대적을 네 손에 붙이신 지극히 높으신 하나님을 찬송할지로다\n\n[새번역]\n20 아브람은 들으시오.",
            "meditation": "아브람은 롯을 구하기 위한 전쟁에서 승리했습니다.",
            "question": "1. 말씀을 통해 하나님이 오늘 나에게 주신 교훈은 무엇인가요?",
            "prayer": "지극히 높으신 하나님, 제 삶의 모든 승리가 주님께로부터 왔음을 인정합니다.\n\n함께 기도 - 일대일\n12주 과정으로 진행되는 양육과정입니다.",
        }
    }


def make_kakao_request(utterance: str) -> dict:
    return {"userRequest": {"utterance": utterance}}


@pytest.mark.asyncio
async def test_webhook_today_bible(sample_data):
    with patch("main.load_json", return_value=sample_data), \
         patch("main.get_today", return_value="2026-04-11"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/webhook", json=make_kakao_request("오늘의 말씀"))
        assert resp.status_code == 200
        body = resp.json()
        text = body["template"]["outputs"][0]["simpleText"]["text"]
        assert "하나님을 인정하는 삶" in text
        assert "창세기 14장" in text
        assert "지극히 높으신" in text
        assert len(body["template"]["quickReplies"]) == 3


@pytest.mark.asyncio
async def test_webhook_meditation(sample_data):
    with patch("main.load_json", return_value=sample_data), \
         patch("main.get_today", return_value="2026-04-11"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/webhook", json=make_kakao_request("오늘의 묵상"))
        text = resp.json()["template"]["outputs"][0]["simpleText"]["text"]
        assert "하나님을 인정하는 삶" in text
        assert "아브람" in text
        assert "교훈" in text


@pytest.mark.asyncio
async def test_webhook_prayer(sample_data):
    with patch("main.load_json", return_value=sample_data), \
         patch("main.get_today", return_value="2026-04-11"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/webhook", json=make_kakao_request("오늘의 기도"))
        text = resp.json()["template"]["outputs"][0]["simpleText"]["text"]
        assert "하나님을 인정하는 삶" in text
        assert "함께 기도" in text


@pytest.mark.asyncio
async def test_webhook_unknown_utterance(sample_data):
    with patch("main.load_json", return_value=sample_data), \
         patch("main.get_today", return_value="2026-04-11"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/webhook", json=make_kakao_request("아무말"))
        text = resp.json()["template"]["outputs"][0]["simpleText"]["text"]
        assert "버튼을 눌러" in text


@pytest.mark.asyncio
async def test_webhook_no_data_today():
    with patch("main.load_json", return_value={}), \
         patch("main.get_today", return_value="2026-04-11"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/webhook", json=make_kakao_request("오늘의 말씀"))
        text = resp.json()["template"]["outputs"][0]["simpleText"]["text"]
        assert "준비 중" in text


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
