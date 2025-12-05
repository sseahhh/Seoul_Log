"""
1단계 결과를 순수 코드로 2단계 파싱

gemini-2.5-flash 대신 순수 파이썬 코드로 발언 추출

사용법:
    python parse_with_pure_code.py
"""

import json
import re
from pathlib import Path
from typing import List, Dict


def parse_speaker_line(line: str) -> tuple:
    """
    발언자 라인 파싱

    예: "○의장 최호정  안녕하세요." → ("의장 최호정", "안녕하세요.")
    """
    # ○ 다음 공백 제거하고 파싱
    match = re.match(r'^○\s*(.+?)\s{2,}(.+)$', line)
    if match:
        speaker = match.group(1).strip()
        text = match.group(2).strip()
        return speaker, text

    # 발언자만 있는 경우 (다음 줄부터 내용)
    match = re.match(r'^○\s*(.+)$', line)
    if match:
        speaker = match.group(1).strip()
        return speaker, ""

    return None, None


def split_long_text(text: str, max_length: int = 500) -> List[str]:
    """
    긴 텍스트를 문장 단위로 분할

    Args:
        text: 분할할 텍스트
        max_length: 최대 길이

    Returns:
        분할된 텍스트 리스트
    """
    if len(text) <= max_length:
        return [text]

    # 문장 단위로 분할
    sentences = re.split(r'([.?!])\s+', text)

    chunks = []
    current_chunk = ""

    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        if i + 1 < len(sentences):
            sentence += sentences[i + 1]  # 마침표 추가

        if len(current_chunk) + len(sentence) > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks if chunks else [text]


def parse_section_pure(section_text: str, agenda_title: str, speakers: List[str], previous_speaker: str = None) -> List[Dict]:
    """
    순수 코드로 섹션 파싱

    Args:
        section_text: 회의록 텍스트
        agenda_title: 안건명
        speakers: 발언자 목록 (1단계에서 제공)

    Returns:
        chunks 리스트
    """
    chunks = []
    lines = section_text.split('\n')

    current_speaker = previous_speaker  # 이전 발언자로 초기화
    current_text_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # ○로 시작하는 발언자 라인인지 확인
        if line.startswith('○'):
            # 이전 발언 저장
            if current_speaker and current_text_lines:
                full_text = ' '.join(current_text_lines).strip()

                # 500자 넘으면 분할
                text_chunks = split_long_text(full_text, max_length=500)

                for text_chunk in text_chunks:
                    chunks.append({
                        "speaker": current_speaker,
                        "agenda": agenda_title,
                        "text": text_chunk
                    })

            # 새 발언자 시작
            speaker, first_text = parse_speaker_line(line)

            if speaker:
                current_speaker = speaker
                current_text_lines = [first_text] if first_text else []
        else:
            # 발언 내용 계속
            if current_speaker:
                current_text_lines.append(line)

    # 마지막 발언 저장
    if current_speaker and current_text_lines:
        full_text = ' '.join(current_text_lines).strip()
        text_chunks = split_long_text(full_text, max_length=500)

        for text_chunk in text_chunks:
            chunks.append({
                "speaker": current_speaker,
                "agenda": agenda_title,
                "text": text_chunk
            })

    return chunks


def parse_with_pure_code(txt_path: str, agenda_mapping: List[Dict]) -> List[Dict]:
    """
    1단계 결과를 받아서 순수 코드로 파싱

    Args:
        txt_path: 원본 txt 파일 경로
        agenda_mapping: 1단계 결과 (안건 매핑)

    Returns:
        모든 chunks
    """
    # txt 파일 읽기
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 헤더 제거 (=== 이후부터)
    lines = content.split('\n')
    separator_index = -1
    for i, line in enumerate(lines):
        if '=' * 80 in line:
            separator_index = i
            break

    if separator_index != -1:
        lines = lines[separator_index + 1:]

    all_chunks = []
    last_speaker = None  # 이전 발언자 추적

    print("=" * 80)
    print("2단계: 순수 코드로 발언 추출")
    print("=" * 80)
    print()

    for idx, agenda in enumerate(agenda_mapping, 1):
        agenda_title = agenda['agenda_title']
        line_start = agenda['line_start'] - 1  # 0-indexed
        line_end = agenda['line_end']
        speakers = agenda.get('speakers', [])

        # 라인 범위 추출
        section_lines = lines[line_start:line_end]
        section_text = '\n'.join(section_lines)

        # 파싱 (이전 발언자 전달)
        chunks = parse_section_pure(section_text, agenda_title, speakers, last_speaker)

        # 청크가 있으면 마지막 발언자 업데이트
        if chunks:
            last_speaker = chunks[-1]['speaker']

        print(f"  [{idx}/{len(agenda_mapping)}] ✓ {len(chunks)}개 발언 추출: {agenda_title[:50]}...")

        all_chunks.extend(chunks)

    print()
    print(f"✅ 총 {len(all_chunks)}개 발언 추출 완료!")
    print()

    return all_chunks


def main():
    """메인 함수"""

    # 테스트: 1단계 결과 파일 읽기
    stage1_result_path = "test_results/agenda_extraction_test.json"

    if not Path(stage1_result_path).exists():
        print(f"❌ 1단계 결과 파일이 없습니다: {stage1_result_path}")
        print("먼저 test_agenda_extraction.py를 실행하세요.")
        return

    with open(stage1_result_path, 'r', encoding='utf-8') as f:
        stage1_result = json.load(f)

    # txt 파일 경로
    txt_path = "result/제332회 기획경제위원회 제1차(2025.09.01)/meeting_20251119_113659.txt"

    print("=" * 80)
    print("순수 코드로 2단계 파싱 테스트")
    print("=" * 80)
    print(f"1단계 결과: {stage1_result_path}")
    print(f"원본 파일: {txt_path}")
    print()

    # 2단계 파싱
    chunks = parse_with_pure_code(txt_path, stage1_result['agenda_mapping'])

    # 결과 저장
    final_result = {
        "meeting_info": stage1_result['meeting_info'],
        "chunks": chunks,
        "usage": {
            "method": "pure_python_code",
            "total_chunks": len(chunks)
        }
    }

    output_path = Path("test_results") / "pure_code_result.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)

    print(f"💾 결과 저장: {output_path}")
    print()

    # 통계
    speakers = set(chunk['speaker'] for chunk in chunks)
    agendas = set(chunk['agenda'] for chunk in chunks)

    print("=" * 80)
    print("📊 통계")
    print("=" * 80)
    print(f"총 발언 수: {len(chunks)}개")
    print(f"발언자: {len(speakers)}명")
    print(f"안건: {len(agendas)}개")
    print()

    print("발언자 목록:")
    for speaker in sorted(speakers):
        count = sum(1 for c in chunks if c['speaker'] == speaker)
        print(f"  - {speaker}: {count}회")
    print()


if __name__ == "__main__":
    main()
