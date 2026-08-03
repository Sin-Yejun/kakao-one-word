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
        ▼  data/meditation.json 커밋 (3일치 롤링)
   ┌──────────┐
   │ 레포     │
   └────┬─────┘
        ▼  자동 재배포
   ┌──────────┐      ┌──────────┐
   │ Vercel   │◄─────│ 카카오    │
   │ /webhook │      │ 오픈빌더  │
   └──────────┘      └──────────┘
```

- **크롤링은 GitHub Actions가 직접 수행**하고 결과 JSON을 레포에 커밋한다.
  커밋이 올라가면 Vercel이 자동으로 재배포하므로 데이터가 배포본에 포함된다.
- 카카오 오픈빌더 웹훅 요청이 오면 배포본의 JSON에서 오늘 데이터를 읽어 응답한다.
- 데이터가 없으면 그 자리에서 크롤링해 응답한다. 서버 디스크는 읽기 전용이라
  저장하지 않고 해당 응답에만 쓴다.

### 왜 이 구조인가

데이터는 하루 한 번만 바뀌는데 서버를 24시간 띄워 둘 이유가 없다. 크롤링을 Actions로
빼면 서버는 파일을 읽기만 하는 얇은 함수가 되어 서버리스 무료 티어에 들어맞는다.
`/crawl` 엔드포인트와 `CRON_SECRET`도 함께 없앨 수 있다.

**카카오 오픈빌더는 응답을 5초 안에 받아야 한다.** 잠들었다 깨는 무료 호스팅
(Render 무료 등)은 콜드 스타트가 수십 초라 이 제한을 넘긴다. 서버 상태에 의존하지
않는 구조로 만든 이유다.

## 기술 스택

| 항목 | 선택 |
|------|------|
| 언어 | Python 3.11 |
| 웹 프레임워크 | FastAPI |
| 크롤링 | httpx + BeautifulSoup4 |
| 스케줄러 | GitHub Actions Cron |
| 데이터 저장 | JSON 파일, 레포에 커밋 (DB 없음) |
| 배포 | Vercel (서버리스) |
| 테스트 | pytest + pytest-asyncio |

## 프로젝트 구조

```
├── api/
│   └── index.py     # Vercel 진입점 (main:app 을 노출)
├── main.py          # FastAPI 앱, 카카오 웹훅
├── crawler.py       # 크롤링, HTML 파싱, JSON 저장/로드
├── kakao.py         # 카카오 응답 포맷 헬퍼
├── tests/
│   ├── test_main.py
│   ├── test_crawler.py
│   └── test_kakao.py
├── data/
│   └── meditation.json   # Actions 가 갱신해 커밋하는 데이터
├── vercel.json
├── requirements.txt      # 런타임 의존성 (Vercel 이 설치)
└── requirements-dev.txt  # 개발/테스트용
```

## 로컬 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

크롤링만 따로 돌리려면:

```bash
python crawler.py
```

## 테스트

```bash
python -m pytest tests/ -v
```

크롤러 파싱, JSON 저장/로드, 웹훅 응답, 카카오 포맷을 검증합니다.
