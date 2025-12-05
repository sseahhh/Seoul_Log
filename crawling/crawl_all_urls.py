import requests
from bs4 import BeautifulSoup, NavigableString
import json
import os
import re
from datetime import datetime
import time

def extract_text_with_links(element):
    """
    HTML 요소에서 텍스트와 링크를 순서대로 추출
    반환: [{"type": "text", "content": "..."} 또는 {"type": "link", "text": "...", "url": "..."}]
    """
    result = []

    for child in element.children:
        if isinstance(child, NavigableString):
            # 일반 텍스트
            text = str(child)
            if text:
                result.append({
                    "type": "text",
                    "content": text
                })
        elif child.name == 'a':
            # 링크
            link_text = child.get_text()
            href = child.get('href', '')

            # URL 완성
            if href.startswith('/'):
                full_url = f"https://ms.smc.seoul.kr{href}"
            elif href.startswith('#'):
                full_url = href  # 앵커는 나중에 base URL 추가
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = href

            result.append({
                "type": "link",
                "text": link_text,
                "url": full_url
            })
        elif child.name == 'br':
            # 줄바꿈
            result.append({
                "type": "text",
                "content": "\n"
            })
        elif child.name == 'hr':
            # 수평선
            result.append({
                "type": "separator",
                "content": "---"
            })
        else:
            # 다른 태그는 재귀적으로 처리
            result.extend(extract_text_with_links(child))

    return result

def convert_to_markdown(content_list, base_url):
    """
    구조화된 데이터를 마크다운으로 변환
    """
    markdown = ""

    for item in content_list:
        if item["type"] == "text":
            markdown += item["content"]
        elif item["type"] == "link":
            url = item["url"]
            # 앵커 링크는 base URL 추가
            if url.startswith('#'):
                url = f"{base_url}{url}"
            markdown += f"[{item['text']}]({url})"
        elif item["type"] == "separator":
            markdown += f"\n{item['content']}\n"

    return markdown


def extract_reference_materials(content_list):
    """
    (참고) 섹션에서 참고자료 링크 추출

    Returns:
        [{"title": "문서명", "url": "다운로드 URL"}]
    """
    attachments = []
    in_reference = False
    pending_links = []

    for i, item in enumerate(content_list):
        # (참고) 시작 감지
        if item["type"] == "text" and "(참고)" in item["content"]:
            in_reference = True
            pending_links = []
            continue

        # (회의록 끝에 실음) 감지 시 종료
        if in_reference and item["type"] == "text" and "회의록 끝에 실음" in item["content"]:
            in_reference = False
            # pending_links를 attachments에 추가
            attachments.extend(pending_links)
            pending_links = []
            continue

        # (참고) 구간 내의 링크 수집
        if in_reference and item["type"] == "link":
            # PDF/HWP 다운로드 링크만 추출
            if "appendixDownload" in item["url"] or item["url"].endswith(('.pdf', '.hwp', '.docx')):
                pending_links.append({
                    "title": item["text"].strip(),
                    "url": item["url"]
                })

    return attachments

def crawl_meeting_record(url):
    """
    회의록 크롤링: 텍스트 + 하이퍼링크 보존
    """
    try:
        print(f"크롤링 시작: {url}\n")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            print(f"오류: HTTP {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # 메인 컨텐츠
        canvas = soup.find('div', id='canvas')
        if not canvas:
            print("메인 컨텐츠를 찾을 수 없습니다.")
            return None

        # 제목
        title = soup.title.string if soup.title else "제목 없음"
        title = ' '.join(title.split())

        print(f"제목: {title}")
        print("=" * 80)

        # 전체 내용 추출 (텍스트 + 링크)
        content_with_links = extract_text_with_links(canvas)

        print(f"✓ 총 {len(content_with_links)}개의 요소 추출 완료")

        # 텍스트와 링크 개수 세기
        text_count = sum(1 for item in content_with_links if item["type"] == "text")
        link_count = sum(1 for item in content_with_links if item["type"] == "link")

        print(f"  - 텍스트 요소: {text_count}개")
        print(f"  - 링크 요소: {link_count}개")
        print()

        # 마크다운으로 변환
        markdown_content = convert_to_markdown(content_with_links, url)

        # 참고자료 링크 추출 ⭐ 추가
        attachments = extract_reference_materials(content_with_links)
        print(f"  - 참고자료: {len(attachments)}개")
        if attachments:
            for att in attachments:
                print(f"    * {att['title'][:50]}...")

        # 저장 경로 설정
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 폴더명으로 사용할 제목 정리 (특수문자 제거)
        folder_name = re.sub(r'[\\/:*?"<>|]', '', title)
        folder_name = folder_name.strip()

        # result/제목/ 폴더 생성
        result_dir = os.path.join('result', folder_name)
        os.makedirs(result_dir, exist_ok=True)

        print(f"저장 경로: {result_dir}")
        print()

        # 1. JSON 저장 (구조화된 데이터 + attachments 필드 추가 ⭐)
        json_data = {
            "url": url,
            "title": title,
            "timestamp": timestamp,
            "content": content_with_links,
            "attachments": attachments  # ⭐ 추가
        }

        json_filename = os.path.join(result_dir, f"meeting_{timestamp}.json")
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"✓ JSON 저장: {json_filename}")

        # 2. 마크다운 저장
        md_filename = os.path.join(result_dir, f"meeting_{timestamp}.md")
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"**URL**: {url}\n\n")
            f.write(f"**크롤링 시간**: {timestamp}\n\n")
            f.write("---\n\n")
            f.write(markdown_content)

        print(f"✓ 마크다운 저장: {md_filename}")

        # 3. 순수 텍스트 저장 (링크는 제거, 텍스트만)
        plain_text = ""
        for item in content_with_links:
            if item["type"] == "text":
                plain_text += item["content"]
            elif item["type"] == "link":
                plain_text += item["text"]  # 링크는 텍스트만
            elif item["type"] == "separator":
                plain_text += f"\n{item['content']}\n"  # 구분선 포함

        txt_filename = os.path.join(result_dir, f"meeting_{timestamp}.txt")
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(f"제목: {title}\n")
            f.write(f"URL: {url}\n")
            f.write("=" * 80 + "\n\n")
            f.write(plain_text)

        print(f"✓ 순수 텍스트 저장: {txt_filename}")

        print("\n" + "=" * 80)
        print("크롤링 완료!")
        print("=" * 80 + "\n")

        return {
            "title": title,
            "json_path": json_filename,
            "md_path": md_filename,
            "txt_path": txt_filename
        }

    except Exception as e:
        print(f"에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # SESSION_332_URLS.txt 파일에서 URL 읽기
    url_file = "SESSION_332_URLS.txt"

    try:
        with open(url_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ {url_file} 파일을 찾을 수 없습니다.")
        print("먼저 extract_session_332_links.py를 실행해서 URL을 추출하세요.")
        exit(1)

    print("=" * 80)
    print("서울시의회 회의록 크롤링 시작")
    print(f"총 {len(urls)}개 URL 크롤링")
    print("=" * 80 + "\n")

    results = []
    for idx, url in enumerate(urls, 1):
        print(f"\n[{idx}/{len(urls)}] 크롤링 중...")
        print("-" * 80)

        result = crawl_meeting_record(url)
        if result:
            results.append(result)

        # 서버 부하를 줄이기 위해 2초 대기
        if idx < len(urls):
            print(f"다음 URL까지 2초 대기...\n")
            time.sleep(2)

    # 최종 결과 요약
    print("\n" + "=" * 80)
    print("전체 크롤링 완료!")
    print("=" * 80)
    print(f"\n성공: {len(results)}/{len(urls)}개")
    print("\n크롤링된 회의록:")
    for idx, result in enumerate(results, 1):
        print(f"{idx}. {result['title']}")
    print("\n모든 데이터는 'result/' 폴더에 저장되었습니다.")
