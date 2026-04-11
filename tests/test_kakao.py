from kakao import make_response, make_error_response


def test_make_response_basic():
    result = make_response("hello")
    assert result["version"] == "2.0"
    assert result["template"]["outputs"][0]["simpleText"]["text"] == "hello"
    assert len(result["template"]["quickReplies"]) == 3


def test_make_response_quick_replies_labels():
    result = make_response("test")
    labels = [qr["label"] for qr in result["template"]["quickReplies"]]
    assert labels == ["오늘의 말씀", "한 구절 묵상", "오늘의 기도"]


def test_make_response_quick_replies_action():
    result = make_response("test")
    for qr in result["template"]["quickReplies"]:
        assert qr["action"] == "message"
        assert qr["messageText"] == qr["label"]


def test_make_response_truncate_long_text():
    long_text = "가" * 1500
    result = make_response(long_text)
    text = result["template"]["outputs"][0]["simpleText"]["text"]
    assert len(text) == 1000
    assert text.endswith("...")


def test_make_response_exact_1000_no_truncate():
    text = "가" * 1000
    result = make_response(text)
    output = result["template"]["outputs"][0]["simpleText"]["text"]
    assert output == text
    assert not output.endswith("...")


def test_make_error_response():
    result = make_error_response()
    text = result["template"]["outputs"][0]["simpleText"]["text"]
    assert "준비 중" in text
    assert len(result["template"]["quickReplies"]) == 3
