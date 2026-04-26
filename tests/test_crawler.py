import json
import pytest
from crawler import load_json, save_to_json, parse_meditation, crawl_today, crawl_and_save

SAMPLE_HTML = '''
<html><body>
<section class="qt_area qt_meditation sol_qt_area">
  <p class="sbj">하나님을 인정하는 삶</p>
  <p class="word">오늘의 본문 : 창세기 14장</p>
  <p class="word">오늘의 한 구절 : 창세기 14장 20절</p>
</section>

<section class="qt_cont_sec">
  <h4 class="tit">본문 개요</h4>
  <div class="cont">아브람은 롯을 구하기 위한 전쟁에서 승리한 후 하나님을 찬양합니다.</div>
</section>

<section class="qt_cont_sec">
  <h4 class="tit">오늘의 한 구절</h4>
  <div class="cont">
    [개역개정]<br/>
    20 너희 대적을 네 손에 붙이신 지극히 높으신 하나님을 찬송할지로다 하매 아브람이 그 얻은 것에서 십분의 일을 멜기세덱에게 주었더라<br/>
    <br/>
    [새번역]<br/>
    20 아브람은 들으시오. 그대는, 원수들을 그대의 손에 넘겨 주신 가장 높으신 하나님을 찬양하시오.
  </div>
</section>

<section class="qt_cont_sec">
  <h4 class="tit">한 구절 묵상</h4>
  <div class="cont">아브람은 롯을 구하기 위한 전쟁에서 승리했습니다.<br/>이 승리를 통해 아브람이 깨달은 것은 분명했습니다.</div>
</section>

<section class="qt_cont_sec">
  <h4 class="tit">묵상질문</h4>
  <div class="cont">1. 말씀을 통해 하나님이 오늘 나에게 주신 교훈은 무엇인가요?<br/><br/>2. 최근 내 삶에 얻은 승리가 하나님이 이루신 것을 믿나요?</div>
</section>

<section class="qt_cont_sec">
  <h4 class="tit">심정이 통하는 기도</h4>
  <div class="cont">지극히 높으신 하나님, 제 삶의 모든 승리가 주님께로부터 왔음을 인정합니다.<br/><br/>함께 기도 - 일대일<br/>12주 과정으로 진행되는 양육과정입니다.</div>
</section>
</body></html>
'''


@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    import crawler
    data_file = tmp_path / "data" / "meditation.json"
    monkeypatch.setattr(crawler, "DATA_PATH", data_file)
    return tmp_path


def test_load_json_empty(tmp_data_dir):
    result = load_json()
    assert result == {}


def test_save_and_load(tmp_data_dir):
    save_to_json("2026-04-11", {"title": "test"})
    result = load_json()
    assert result["2026-04-11"]["title"] == "test"


def test_save_keeps_only_3(tmp_data_dir):
    save_to_json("2026-04-09", {"title": "a"})
    save_to_json("2026-04-10", {"title": "b"})
    save_to_json("2026-04-11", {"title": "c"})
    save_to_json("2026-04-12", {"title": "d"})
    result = load_json()
    assert len(result) == 3
    assert "2026-04-09" not in result


# --- parse_meditation tests ---

def test_parse_meditation_title():
    result = parse_meditation(SAMPLE_HTML)
    assert result["title"] == "하나님을 인정하는 삶"


def test_parse_meditation_bible_book():
    result = parse_meditation(SAMPLE_HTML)
    assert result["bible_book"] == "창세기 14장"


def test_parse_meditation_bible_verse_both_versions():
    result = parse_meditation(SAMPLE_HTML)
    assert "지극히 높으신" in result["bible_verse"]
    assert "[개역개정]" in result["bible_verse"]
    assert "[새번역]" in result["bible_verse"]
    assert "가장 높으신 하나님을 찬양하시오" in result["bible_verse"]


def test_parse_meditation_summary():
    result = parse_meditation(SAMPLE_HTML)
    assert result["summary"] == "아브람은 롯을 구하기 위한 전쟁에서 승리한 후 하나님을 찬양합니다."


def test_parse_meditation_meditation():
    result = parse_meditation(SAMPLE_HTML)
    assert "아브람" in result["meditation"]
    assert "깨달은" in result["meditation"]


def test_parse_meditation_question_has_linebreaks():
    result = parse_meditation(SAMPLE_HTML)
    assert "1." in result["question"]
    assert "2." in result["question"]
    assert "\n" in result["question"]


def test_parse_meditation_prayer_includes_together():
    result = parse_meditation(SAMPLE_HTML)
    assert "하나님" in result["prayer"]
    assert "함께 기도" in result["prayer"]
    assert "양육과정" in result["prayer"]


def test_parse_meditation_missing_section():
    incomplete = "<html><body><section class='qt_area qt_meditation'><p class='sbj'>제목</p></section></body></html>"
    with pytest.raises(ValueError):
        parse_meditation(incomplete)


@pytest.mark.asyncio
async def test_crawl_today_success():
    from unittest.mock import AsyncMock, MagicMock, patch
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = SAMPLE_HTML
    mock_response.charset_encoding = "utf-8"

    with patch("crawler.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client
        result = await crawl_today("2026-04-11")
        assert result["title"] == "하나님을 인정하는 삶"


@pytest.mark.asyncio
async def test_crawl_and_save_skips_existing(tmp_data_dir):
    from unittest.mock import patch
    save_to_json("2026-04-11", {"title": "existing"})
    with patch("crawler.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-11"
        result = await crawl_and_save()
        assert result is True
