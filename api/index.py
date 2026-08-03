"""Vercel 서버리스 진입점.

Vercel 은 api/ 아래 파일을 함수로 잡고, 모듈의 `app` 을 ASGI 앱으로 인식한다.
프로젝트 루트의 main.py 를 불러오기 위해 경로를 먼저 추가한다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app  # noqa: E402

__all__ = ["app"]
