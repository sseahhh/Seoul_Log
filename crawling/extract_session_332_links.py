"""
Selenium을 사용하여 제332회 임시회의 모든 회의록 링크를 자동 추출
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def extract_session_332_links():
    """제332회 임시회의 모든 회의록 링크 추출"""

    print("=" * 80)
    print("서울시의회 제332회 임시회 회의록 링크 자동 추출")
    print("=" * 80 + "\n")

    # Chrome 옵션 설정
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # 브라우저 창 숨기기 (필요시 주석 해제)
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    # WebDriver 시작
    print("Chrome 브라우저 시작 중...")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # 페이지 로드
        url = "https://ms.smc.seoul.kr/kr/assembly/session.do"
        print(f"페이지 로딩: {url}\n")
        driver.get(url)

        # 페이지 로딩 대기
        time.sleep(3)

        print("제11대 트리 펼치기 중...")
        # 제11대 트리 노드 찾아서 클릭
        try:
            # Fancytree에서 제11대 노드 찾기
            th11_node = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[@class='fancytree-title' and contains(text(), '제11대')]"))
            )

            if th11_node:
                # 스크롤해서 보이게 하기
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", th11_node)
                time.sleep(1)

                # 제11대 앞의 expander 클릭
                parent_li = th11_node.find_element(By.XPATH, "./ancestor::li[1]")

                # 이미 펼쳐져 있는지 확인
                if "fancytree-expanded" not in parent_li.get_attribute("class"):
                    expander = parent_li.find_element(By.CSS_SELECTOR, "span.fancytree-expander")
                    expander.click()
                    time.sleep(2)  # 로딩 대기
                    print("✓ 제11대 트리 펼침\n")
                else:
                    print("✓ 제11대 트리 이미 펼쳐져 있음\n")
            else:
                print("⚠ 제11대 노드를 찾을 수 없습니다.\n")
        except Exception as e:
            print(f"제11대 클릭 중 오류: {e}\n")
            import traceback
            traceback.print_exc()

        print("제332회 임시회 찾기 중...")
        # 제332회 노드 찾아서 클릭
        session_332_li = None
        try:
            # 제332회 찾기
            session_332 = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[@class='fancytree-title' and contains(text(), '제332회') and contains(text(), '임시회')]"))
            )

            if session_332:
                print(f"✓ 발견: {session_332.text}")

                # 스크롤해서 보이게 하기
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", session_332)
                time.sleep(1)

                # 제332회 펼치기
                session_332_li = session_332.find_element(By.XPATH, "./ancestor::li[1]")

                # expander가 이미 펼쳐져 있는지 확인
                if "fancytree-expanded" not in session_332_li.get_attribute("class"):
                    expander = session_332_li.find_element(By.CSS_SELECTOR, "span.fancytree-expander")
                    expander.click()
                    time.sleep(2)  # 로딩 대기
                    print("✓ 제332회 트리 펼침\n")
                else:
                    print("✓ 제332회 트리 이미 펼쳐져 있음\n")

                # 1단계: 본회의, 운영위원회 등 1차 하위 폴더들 펼치기
                print("1차 하위 위원회 목록 펼치기 중...")
                time.sleep(2)

                # 제332회 바로 아래 1차 하위 폴더만 찾기 (여러 방법 시도)
                level1_folders = []

                # 방법 1: fancytree-folder 클래스로 찾기
                try:
                    level1_folders = session_332_li.find_elements(By.XPATH, "./ul/li[contains(@class, 'fancytree-folder')]")
                except:
                    pass

                # 방법 2: fancytree-lazy 클래스로 찾기 (동적 로딩)
                if len(level1_folders) == 0:
                    try:
                        level1_folders = session_332_li.find_elements(By.XPATH, "./ul/li[contains(@class, 'fancytree-lazy')]")
                    except:
                        pass

                # 방법 3: 모든 li 찾기 (폴더 여부 상관없이)
                if len(level1_folders) == 0:
                    try:
                        level1_folders = session_332_li.find_elements(By.XPATH, "./ul/li")
                    except:
                        pass

                print(f"  발견된 1차 하위 폴더: {len(level1_folders)}개")

                if len(level1_folders) == 0:
                    print("  ⚠ 1차 하위 폴더를 찾을 수 없습니다. DOM 구조 확인 필요\n")
                    # 디버깅: 제332회 li의 HTML 구조 확인
                    try:
                        html_snippet = session_332_li.get_attribute('innerHTML')[:500]
                        print(f"  제332회 li 내부 구조 (첫 500자):\n{html_snippet}\n")
                    except:
                        pass

                for idx, folder in enumerate(level1_folders, 1):
                    try:
                        # fancytree-node span 찾기
                        node_span = folder.find_element(By.CSS_SELECTOR, "span.fancytree-node")
                        title = node_span.find_element(By.CSS_SELECTOR, "span.fancytree-title")
                        expander = node_span.find_element(By.CSS_SELECTOR, "span.fancytree-expander")

                        folder_class = node_span.get_attribute("class")
                        is_lazy = "fancytree-lazy" in folder_class
                        is_expanded = "fancytree-expanded" in folder_class

                        # 펼쳐져 있지 않으면 클릭
                        if not is_expanded:
                            # 스크롤
                            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", title)
                            time.sleep(0.5)

                            print(f"  {idx}. {title.text} 펼치기{'(lazy 로딩)' if is_lazy else ''}...")
                            expander.click()

                            # lazy 로딩이면 더 오래 대기
                            if is_lazy:
                                time.sleep(2)
                            else:
                                time.sleep(1)
                        else:
                            print(f"  {idx}. {title.text} - 이미 펼쳐져 있음")
                    except Exception as e:
                        print(f"  ⚠ {idx}번 폴더 펼치기 실패: {str(e)}")
                        continue

                print("✓ 1차 하위 폴더 펼침 완료\n")

                # 2단계: 모든 2차 하위 폴더들도 펼치기 (각 위원회의 회차별)
                print("2차 하위 폴더 펼치기 중...")
                time.sleep(2)

                # 제332회 영역 내의 모든 li (폴더 포함) 찾기
                all_nodes = session_332_li.find_elements(By.XPATH, ".//span[contains(@class, 'fancytree-node')]")
                # 폴더만 필터링 (fancytree-folder 클래스 있는 것)
                all_folders = [node for node in all_nodes if "fancytree-folder" in node.get_attribute("class") or "fancytree-lazy" in node.get_attribute("class")]
                print(f"  발견된 전체 폴더 노드: {len(all_folders)}개")

                expanded_count = 0
                failed_count = 0
                for idx, folder_node in enumerate(all_folders, 1):
                    try:
                        folder_class = folder_node.get_attribute("class")
                        is_lazy = "fancytree-lazy" in folder_class
                        is_expanded = "fancytree-expanded" in folder_class

                        # 펼쳐져 있지 않으면 클릭
                        if not is_expanded:
                            # 스크롤
                            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", folder_node)
                            time.sleep(0.3)

                            expander = folder_node.find_element(By.CSS_SELECTOR, "span.fancytree-expander")

                            # expander가 클릭 가능한지 확인
                            if expander.is_displayed():
                                expander.click()
                                expanded_count += 1

                                # lazy 로딩이면 더 오래 대기
                                if is_lazy:
                                    time.sleep(1)
                                else:
                                    time.sleep(0.5)

                                # 진행상황 표시 (10개마다)
                                if expanded_count % 10 == 0:
                                    print(f"    진행: {expanded_count}개 폴더 펼침...")
                    except Exception as e:
                        failed_count += 1
                        # 실패가 너무 많으면 중단
                        if failed_count > 50:
                            print(f"    ⚠ 연속 실패가 많아 중단합니다.")
                            break
                        continue

                print(f"✓ 추가로 {expanded_count}개 폴더 펼침 완료 (실패: {failed_count}개)\n")

        except Exception as e:
            print(f"제332회 클릭 중 오류: {e}\n")
            import traceback
            traceback.print_exc()

        # 모든 회의록 링크 추출
        print("회의록 링크 추출 중...\n")
        time.sleep(2)

        # 제332회 영역에서만 링크 찾기
        all_links = []
        if session_332_li:
            # 그 안에 있는 모든 a 태그 찾기
            all_links = session_332_li.find_elements(By.XPATH, ".//a[contains(@href, 'recordView.do')]")
            print(f"제332회 영역에서 발견된 회의록 링크: {len(all_links)}개\n")
        else:
            # session_332_li를 찾지 못한 경우 재시도
            try:
                session_332_li = driver.find_element(By.XPATH, "//span[@class='fancytree-title' and contains(text(), '제332회') and contains(text(), '임시회')]//ancestor::li[1]")
                all_links = session_332_li.find_elements(By.XPATH, ".//a[contains(@href, 'recordView.do')]")
                print(f"제332회 영역에서 발견된 회의록 링크: {len(all_links)}개\n")
            except:
                # 실패하면 전체에서 찾기
                print("제332회 영역 찾기 실패. 전체에서 검색합니다.\n")
                all_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'recordView.do')]")

        meeting_links = []

        for link in all_links:
            try:
                href = link.get_attribute('href')
                text = link.text.strip()

                if href and 'recordView.do?key=' in href and text:
                    meeting_links.append({
                        'url': href,
                        'title': text
                    })
                    print(f"  ✓ {text}")
            except:
                continue

        print(f"\n총 {len(meeting_links)}개의 회의록 링크 발견\n")
        print("=" * 80)

        # URL만 추출해서 출력
        urls = [link['url'] for link in meeting_links]

        if urls:
            print("\n추출된 URL 목록:\n")
            for url in urls:
                print(url)

            # 파일로 저장
            with open('SESSION_332_URLS.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(urls))

            print(f"\n✓ URL이 SESSION_332_URLS.txt 파일에 저장되었습니다.")

            # 상세 정보도 저장
            with open('SESSION_332_DETAILS.txt', 'w', encoding='utf-8') as f:
                for link in meeting_links:
                    f.write(f"{link['title']}\n{link['url']}\n\n")

            print(f"✓ 상세 정보가 SESSION_332_DETAILS.txt 파일에 저장되었습니다.")
        else:
            print("⚠ 회의록 링크를 찾지 못했습니다.")
            print("\n페이지 스크린샷을 저장합니다...")
            driver.save_screenshot('selenium_debug.png')
            print("✓ selenium_debug.png 저장 완료")

        return urls

    except Exception as e:
        print(f"에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()

        # 디버깅을 위한 스크린샷
        try:
            driver.save_screenshot('selenium_error.png')
            print("\n에러 스크린샷이 selenium_error.png에 저장되었습니다.")
        except:
            pass

        return []

    finally:
        print("\n브라우저 종료 중...")
        driver.quit()
        print("완료!")

if __name__ == "__main__":
    urls = extract_session_332_links()

    if urls:
        print(f"\n\n최종 결과: {len(urls)}개 URL 추출 완료")
    else:
        print("\n\n실패: URL을 추출하지 못했습니다.")
        print("다음을 확인해주세요:")
        print("1. Chrome WebDriver가 설치되어 있는지")
        print("2. 인터넷 연결이 정상인지")
        print("3. selenium_debug.png 파일을 확인해 페이지 상태 점검")
