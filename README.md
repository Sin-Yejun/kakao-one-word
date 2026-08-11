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
        ▼  GitHub Actions (00:10, 05:00, 06:00 KST)
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
- 오늘 데이터가 아직 없으면 보관 중인 **가장 최근 날짜**를 그 날짜 그대로 표기해 응답한다.
  요청 경로에서는 절대 크롤링하지 않는다 (아래 5초 제한 참고).

### 왜 이 구조인가

데이터는 하루 한 번만 바뀌는데 서버를 24시간 띄워 둘 이유가 없다. 크롤링을 Actions로
빼면 서버는 파일을 읽기만 하는 얇은 함수가 되어 서버리스 무료 티어에 들어맞는다.
`/crawl` 엔드포인트와 `CRON_SECRET`도 함께 없앨 수 있다.

**카카오 오픈빌더는 응답을 5초 안에 받아야 한다.** 잠들었다 깨는 무료 호스팅
(Render 무료 등)은 콜드 스타트가 수십 초라 이 제한을 넘긴다. 서버 상태에 의존하지
않는 구조로 만든 이유다.

같은 이유로 **웹훅 핸들러 안에서는 외부 네트워크 I/O를 하지 않는다.** 원본 사이트
크롤링은 약 4초가 걸려 5초 예산에 여유가 없다. 데이터 공백은 크롤러 쪽에서 메우고,
서버는 파일을 읽어 즉시 응답하는 역할만 한다. 크롤링 전용 의존성(httpx, bs4)도
모듈 최상단이 아니라 크롤링 함수 안에서 import 해 콜드 스타트 비용을 줄였다.

> ⚠️ **GitHub Actions 스케줄은 레포에 60일간 활동이 없으면 자동 비활성화된다.**
> 2026-06-25 에 실제로 이 일이 발생해 데이터가 멈췄고, 웹훅이 매번 크롤링 경로를
> 타면서 응답이 느려졌다. 지금은 크롤 결과를 매일 레포에 커밋하므로 그 커밋이
> 활동으로 집계되어 재발하지 않을 것으로 본다. 혹시 멈추면
> `gh workflow enable crawl.yml` 후 `gh workflow run crawl.yml` 로 되살린다.

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
