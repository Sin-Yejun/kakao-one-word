import json
import os
from pathlib import Path

import pytest

from crawler import save_to_json, load_json, DATA_PATH


@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    """crawler.DATA_PATH를 임시 디렉토리로 변경"""
    test_path = tmp_path / "meditation.json"
    monkeypatch.setattr("crawler.DATA_PATH", test_path)
    return test_path


def test_save_to_json_creates_file(tmp_data_dir):
    data = {"title": "테스트", "bible_book": "창세기 1장"}
    save_to_json("2026-04-11", data)
    assert tmp_data_dir.exists()
    contents = json.loads(tmp_data_dir.read_text(encoding="utf-8"))
    assert "2026-04-11" in contents
    assert contents["2026-04-11"]["title"] == "테스트"


def test_save_to_json_keeps_max_3_days(tmp_data_dir):
    for i in range(5):
        save_to_json(f"2026-04-{10 + i:02d}", {"title": f"day{i}"})
    contents = json.loads(tmp_data_dir.read_text(encoding="utf-8"))
    assert len(contents) == 3
    # 가장 최근 3일만 유지
    assert "2026-04-12" in contents
    assert "2026-04-13" in contents
    assert "2026-04-14" in contents
    assert "2026-04-10" not in contents
    assert "2026-04-11" not in contents


def test_save_to_json_overwrites_same_date(tmp_data_dir):
    save_to_json("2026-04-11", {"title": "old"})
    save_to_json("2026-04-11", {"title": "new"})
    contents = json.loads(tmp_data_dir.read_text(encoding="utf-8"))
    assert contents["2026-04-11"]["title"] == "new"


def test_load_json_returns_empty_when_no_file(tmp_data_dir):
    result = load_json()
    assert result == {}


def test_load_json_returns_data(tmp_data_dir):
    save_to_json("2026-04-11", {"title": "test"})
    result = load_json()
    assert "2026-04-11" in result
