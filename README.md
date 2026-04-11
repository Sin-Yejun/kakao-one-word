# 한 구절 묵상 카카오톡 챗봇

분당우리교회의 매일 묵상 콘텐츠를 카카오톡 채널 챗봇으로 제공하는 서비스입니다.

## 미리보기

사용자는 3개 버튼 중 하나를 선택해 오늘의 콘텐츠를 받아볼 수 있습니다.

| 버튼 | 응답 내용 |
|------|----------|
| 오늘의 말씀 | 본문 말씀 (개역개정 + 새번역) |
| 오늘의 묵상 | 묵상 해설 + 묵상질문 |
| 오늘의 기도 | 기도문 + 함께 기도 |

## 아키텍처

```
[분당우리교회 웹사이트]
        │
        ▼  GitHub Actions (05:00, 06:00 KST)
   ┌──────────┐
   │ crawler  │  httpx + BeautifulSoup4
   └────┬─────┘
        ▼
   ┌──────────┐
   │ JSON     │  3일치 롤링 저장
   └────┬─────┘
        ▼
   ┌──────────┐      ┌──────────┐
   │ FastAPI  │◄─────│ 카카오    │
   │ /webhook │      │ 오픈빌더  │
   └──────────┘      └──────────┘
```

- GitHub Actions가 매일 오전 5시, 6시(KST)에 `/crawl` 엔드포인트를 호출하여 크롤링
- 카카오 오픈빌더 웹훅으로 요청이 오면 JSON에서 오늘 데이터를 읽어 응답
- 데이터가 없으면 웹훅에서 fallback으로 즉시 크롤링 시도

## 기술 스택

| 항목 | 선택 |
|------|------|
| 언어 | Python 3.11 |
| 웹 프레임워크 | FastAPI |
| 크롤링 | httpx + BeautifulSoup4 |
| 스케줄러 | GitHub Actions Cron |
| 데이터 저장 | JSON 파일 (DB 없음) |
| 배포 | Railway |
| 테스트 | pytest + pytest-asyncio |

## 프로젝트 구조

```
├── main.py          # FastAPI 앱, 웹훅/크롤링 엔드포인트
├── crawler.py       # 크롤링, HTML 파싱, JSON 저장/로드
├── kakao.py         # 카카오 응답 포맷 헬퍼
├── tests/
│   ├── test_main.py
│   ├── test_crawler.py
│   └── test_kakao.py
├── data/
│   └── meditation.json   # 크롤링 데이터 (런타임 생성)
├── requirements.txt
└── Procfile              # Railway 배포용
```

## 로컬 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 테스트

```bash
python -m pytest tests/ -v
```

24개 테스트 — 크롤러 파싱, JSON 저장/로드, 웹훅 응답, 카카오 포맷을 검증합니다.
