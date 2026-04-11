QUICK_REPLIES = [
    {"label": "오늘의 말씀", "action": "message", "messageText": "오늘의 말씀"},
    {"label": "한 구절 묵상", "action": "message", "messageText": "한 구절 묵상"},
    {"label": "오늘의 기도", "action": "message", "messageText": "오늘의 기도"},
]

MAX_TEXT_LENGTH = 1000


def make_response(text: str) -> dict:
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:997] + "..."
    return {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": text}}],
            "quickReplies": QUICK_REPLIES,
        },
    }


def make_error_response() -> dict:
    return make_response("오늘의 말씀은 아직 준비 중입니다 🙏\n잠시 후 다시 시도해 주세요.")
