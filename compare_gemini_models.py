"""
Gemini Pro vs Flash 비교 스크립트 (1회용)

같은 파일에 대해 Pro와 Flash가 어떻게 다르게 파싱하는지 비교
결과는 test_gemini/result_pro, test_gemini/result_flash에 저장
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
import sys

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from data_processing.extract_metadata_hybrid import extract_metadata_hybrid, extract_metadata_hybrid_flash

load_dotenv()


def compare_models(md_file_path: str):
    """
    같은 파일을 Pro와 Flash로 각각 파싱하여 비교

    Args:
        md_file_path: 테스트할 md 파일 경로
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY가 설정되지 않았습니다.")
        return

    # 출력 폴더 생성
    output_base = Path("test_gemini")
    output_base.mkdir(exist_ok=True)

    pro_dir = output_base / "result_pro"
    flash_dir = output_base / "result_flash"

    pro_dir.mkdir(exist_ok=True)
    flash_dir.mkdir(exist_ok=True)

    md_file = Path(md_file_path)
    file_name = md_file.stem

    print("=" * 100)
    print(f"📄 파일: {md_file.name}")
    print("=" * 100)
    print()

    # 1. Gemini Pro로 파싱
    print("🤖 Gemini Pro 파싱 시작...")
    print("-" * 100)
    try:
        pro_result = extract_metadata_hybrid(
            txt_path=str(md_file),
            api_key=api_key,
            stage1_model="gemini-2.5-pro",
            verbose=True
        )

        # Pro 결과 저장
        pro_output = pro_dir / f"{file_name}.json"
        with open(pro_output, 'w', encoding='utf-8') as f:
            json.dump(pro_result, f, ensure_ascii=False, indent=2)

        print(f"✅ Pro 완료: {len(pro_result['agenda_mapping'])}개 안건, {len(pro_result['chunks'])}개 청크")
        print(f"   저장: {pro_output}")

    except Exception as e:
        print(f"❌ Pro 실패: {e}")
        import traceback
        traceback.print_exc()
        pro_result = None

    print()
    print("=" * 100)
    print()

    # 2. Gemini Flash로 파싱
    print("⚡ Gemini Flash 파싱 시작...")
    print("-" * 100)
    try:
        flash_result = extract_metadata_hybrid_flash(
            txt_path=str(md_file),
            api_key=api_key,
            verbose=True
        )

        # Flash 결과 저장
        flash_output = flash_dir / f"{file_name}.json"
        with open(flash_output, 'w', encoding='utf-8') as f:
            json.dump(flash_result, f, ensure_ascii=False, indent=2)

        print(f"✅ Flash 완료: {len(flash_result['agenda_mapping'])}개 안건, {len(flash_result['chunks'])}개 청크")
        print(f"   저장: {flash_output}")

    except Exception as e:
        print(f"❌ Flash 실패: {e}")
        import traceback
        traceback.print_exc()
        flash_result = None

    print()
    print("=" * 100)
    print("📊 비교 결과")
    print("=" * 100)

    if pro_result and flash_result:
        # 안건 수 비교
        pro_agendas = len(pro_result['agenda_mapping'])
        flash_agendas = len(flash_result['agenda_mapping'])

        print(f"\n📋 안건 수:")
        print(f"   Pro:   {pro_agendas}개")
        print(f"   Flash: {flash_agendas}개")
        print(f"   차이:  {abs(pro_agendas - flash_agendas)}개")

        # 청크 수 비교
        pro_chunks = len(pro_result['chunks'])
        flash_chunks = len(flash_result['chunks'])

        print(f"\n💬 청크 수:")
        print(f"   Pro:   {pro_chunks}개")
        print(f"   Flash: {flash_chunks}개")
        print(f"   차이:  {abs(pro_chunks - flash_chunks)}개")

        # 비용 비교
        pro_usage = pro_result.get('usage', {})
        flash_usage = flash_result.get('usage', {})

        pro_tokens = pro_usage.get('stage1_tokens', {})
        flash_tokens = flash_usage.get('stage1_tokens', {})

        print(f"\n💰 Stage 1 토큰:")
        print(f"   Pro:   input={pro_tokens.get('input', 0):,}, output={pro_tokens.get('output', 0):,}")
        print(f"   Flash: input={flash_tokens.get('input', 0):,}, output={flash_tokens.get('output', 0):,}")

        # 안건 제목 비교
        print(f"\n📝 안건 제목 비교:")
        max_len = max(pro_agendas, flash_agendas)

        for i in range(max_len):
            print(f"\n   [{i+1}]")

            if i < pro_agendas:
                pro_title = pro_result['agenda_mapping'][i]['agenda_title']
                pro_range = f"{pro_result['agenda_mapping'][i].get('line_start', '?')}-{pro_result['agenda_mapping'][i].get('line_end', '?')}"
                print(f"   Pro:   {pro_title[:60]}... (line {pro_range})")
            else:
                print(f"   Pro:   (없음)")

            if i < flash_agendas:
                flash_title = flash_result['agenda_mapping'][i]['agenda_title']
                flash_range = f"{flash_result['agenda_mapping'][i].get('line_start', '?')}-{flash_result['agenda_mapping'][i].get('line_end', '?')}"
                print(f"   Flash: {flash_title[:60]}... (line {flash_range})")
            else:
                print(f"   Flash: (없음)")

        # 중복 line range 체크
        print(f"\n⚠️  중복 line range 체크:")

        def check_overlaps(agendas, model_name):
            overlaps = []
            for i in range(len(agendas)):
                for j in range(i + 1, len(agendas)):
                    start1 = agendas[i].get('line_start', 0)
                    end1 = agendas[i].get('line_end', 0)
                    start2 = agendas[j].get('line_start', 0)
                    end2 = agendas[j].get('line_end', 0)

                    overlap_start = max(start1, start2)
                    overlap_end = min(end1, end2)
                    overlap = max(0, overlap_end - overlap_start)

                    if overlap > 5:
                        overlaps.append({
                            'agenda1': agendas[i]['agenda_title'][:40],
                            'agenda2': agendas[j]['agenda_title'][:40],
                            'overlap': overlap
                        })

            if overlaps:
                print(f"   {model_name}: {len(overlaps)}개 중복 발견")
                for ov in overlaps[:3]:
                    print(f"      - {ov['agenda1']} ↔ {ov['agenda2']} ({ov['overlap']}줄)")
            else:
                print(f"   {model_name}: ✅ 중복 없음")

        check_overlaps(pro_result['agenda_mapping'], "Pro")
        check_overlaps(flash_result['agenda_mapping'], "Flash")

    print()
    print("=" * 100)
    print(f"✅ 비교 완료!")
    print(f"   Pro 결과:   test_gemini/result_pro/{file_name}.json")
    print(f"   Flash 결과: test_gemini/result_flash/{file_name}.json")
    print("=" * 100)


def main():
    """메인 함수"""
    import sys
    from glob import glob

    # 인자가 있으면 그것 사용, 없으면 기본 파일 목록 사용
    if len(sys.argv) >= 2:
        md_file = sys.argv[1]
        files = glob(md_file)

        if not files:
            print(f"❌ 파일을 찾을 수 없습니다: {md_file}")
            return

        compare_models(files[0])
    else:
        # 기본 비교 파일 목록 (일괄상정, 본회의, 위원회 등 다양한 케이스)
        test_files = [
            "result/제332회 도시계획균형위원회 제2차(2025.09.02)/meeting_*.md",  # 일괄상정 중복 케이스
            "result/제332회 본회의 제4차(2025.09.05)/meeting_*.md",  # 본회의 개별 표결
            "result/제332회 교통위원회 제4차(2025.09.08)/meeting_*.md",  # 일반 위원회
        ]

        print("=" * 100)
        print("🔍 Gemini Pro vs Flash 자동 비교 (기본 파일 목록)")
        print("=" * 100)
        print()

        for pattern in test_files:
            files = glob(pattern)
            if files:
                print(f"\n{'=' * 100}")
                print(f"📁 파일 패턴: {pattern}")
                print(f"{'=' * 100}\n")
                compare_models(files[0])
                print("\n" * 2)
            else:
                print(f"⚠️  파일 없음: {pattern}")
                print()


if __name__ == "__main__":
    main()
