# 크롤링 모듈

서울시의회 회의록 크롤링 스크립트

---

## 📁 파일 구조

```
crawling/
├── extract_session_332_links.py    # URL 추출 (Selenium)
└── crawl_all_urls.py               # 회의록 다운로드
```

---

## 🔧 사용 방법

### 1단계: URL 추출

**파일:** `extract_session_332_links.py`

```bash
python crawling/extract_session_332_links.py
```

**기능:**
- Selenium으로 서울시의회 제332회 임시회 페이지 크롤링
- 모든 회의록 링크 자동 추출

**출력:**
- `SESSION_332_URLS.txt` - 52개 회의록 URL 리스트

**필수 패키지:**
```bash
pip install selenium webdriver-manager
```

**특징:**
- 동적 페이지 크롤링 (JavaScript 렌더링 대응)
- Chrome WebDriver 자동 설치
- User-Agent 설정으로 차단 방지

---

### 2단계: 회의록 다운로드

**파일:** `crawl_all_urls.py`

```bash
python crawling/crawl_all_urls.py
```

**기능:**
- SESSION_332_URLS.txt의 URL을 순차 크롤링
- BeautifulSoup으로 HTML 파싱
- 발언자, 내용, 참고자료 추출

**출력:**
- `result/회의명/meeting_YYYYMMDD_HHMMSS.txt` - 회의록 텍스트
- `result/회의명/meeting_YYYYMMDD_HHMMSS.json` - 메타데이터 (JSON)
- `result/회의명/meeting_YYYYMMDD_HHMMSS.md` - 마크다운 (참고용)

**처리 내용:**
- ○발언자 패턴 추출
- `---` 구분선 처리
- 참고자료 섹션 포함 (링크 정보)
- 첨부 문서 링크 추출

**예시 출력:**

**TXT 파일:**
```
○위원장 서상열: 제332회 서울특별시의회 임시회 제3차 회의를 개의하겠습니다.
---
서울특별시 인공지능산업 육성 및 지원 조례안
---
○위원장 서상열: 의사일정 제1항 조례안을 상정합니다.
```

**JSON 파일:**
```json
{
  "url": "https://ms.smc.seoul.kr/record/recordView.do?key=...",
  "title": "제332회 AI경쟁력강화특별위원회 제3차",
  "date": "2025.09.10",
  "content": "회의록 전체 텍스트...",
  "attachments": [
    {"title": "검토보고서", "url": "https://..."}
  ]
}
```

---

## ⚙️ 설정

### Chrome WebDriver

Selenium은 Chrome WebDriver가 필요합니다. `webdriver-manager`가 자동으로 설치하지만, 수동 설치도 가능합니다.

```bash
# webdriver-manager 사용 (권장)
pip install webdriver-manager

# 또는 수동 다운로드
# https://chromedriver.chromium.org/downloads
```

### User-Agent

크롤링 시 서버 차단 방지를 위해 User-Agent를 설정합니다.

```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
```

---

## 📊 성능

- **URL 추출:** 약 5-10분 (52개 링크)
- **회의록 다운로드:** URL당 10-30초 (총 약 20-30분)

---

## 🐛 트러블슈팅

### Selenium 에러

```
selenium.common.exceptions.WebDriverException: Message: unknown error: cannot find Chrome binary
```

**해결:**
- Chrome 브라우저 설치 확인
- webdriver-manager 재설치

```bash
pip uninstall selenium webdriver-manager
pip install selenium webdriver-manager
```

### 크롤링 차단

서울시의회 서버가 봇 차단하는 경우:

```python
# crawl_all_urls.py 수정
time.sleep(5)  # 요청 간 대기 시간 증가 (기본 2초 → 5초)
```

---

## 🔗 관련 파일

- **SESSION_332_URLS.txt** - URL 리스트 (52개)
- **result/** - 크롤링 결과 저장 폴더

---

**마지막 업데이트:** 2025-11-22
