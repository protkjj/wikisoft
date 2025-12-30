"""
확정급여채무평가 데이터 검증 AI Agent
시스템 실행 엔트리 포인트
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# .env 파일에서 환경 변수 로드
load_dotenv(PROJECT_ROOT / ".env")

# core 모듈 import
from core.loader import ExcelLoader
from core.agent import AuditAgent
from core.reporter import ReportGenerator


def main():
    """
    메인 실행 함수
    - data/ 폴더에서 엑셀 파일 탐색
    - 데이터 로드 및 검증 수행
    - 결과를 output/ 폴더에 저장
    """
    print("=" * 60)
    print("확정급여채무평가 데이터 검증 AI Agent 시작")
    print("=" * 60)
    
    # API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 오류: .env 파일에 OPENAI_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일을 생성하고 OPENAI_API_KEY=your_key 형식으로 설정해주세요.")
        return
    
    # 폴더 구조 확인 및 생성
    data_dir = PROJECT_ROOT / "data"
    output_dir = PROJECT_ROOT / "output"
    
    data_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # 1. 엑셀 파일 탐색 및 로드
    print("\n[1단계] 엑셀 파일 탐색 중...")
    loader = ExcelLoader(data_dir)
    excel_files = loader.find_excel_files()
    
    if not excel_files:
        print(f"⚠️  경고: {data_dir} 폴더에서 엑셀 파일을 찾을 수 없습니다.")
        print("   분석할 엑셀 파일을 data/ 폴더에 넣어주세요.")
        return
    
    print(f"   발견된 엑셀 파일: {len(excel_files)}개")
    for file in excel_files:
        print(f"   - {file.name}")
    
    # 첫 번째 엑셀 파일 사용 (또는 여러 파일 처리 로직 추가 가능)
    target_file = excel_files[0]
    print(f"\n   분석 대상: {target_file.name}")
    
    # 데이터 로드
    print("\n[2단계] 엑셀 데이터 로드 중...")
    try:
        dataframes = loader.load_excel(target_file)
        print(f"   로드된 시트: {list(dataframes.keys())}")
    except Exception as e:
        print(f"❌ 오류: 엑셀 파일 로드 중 문제가 발생했습니다.")
        print(f"   {str(e)}")
        return
    
    # 2. AI 에이전트로 데이터 검증
    print("\n[3단계] AI 에이전트로 데이터 검증 수행 중...")
    try:
        agent = AuditAgent(api_key=api_key)
        audit_results = agent.audit_data(dataframes)
        print("   검증 완료")
    except Exception as e:
        print(f"❌ 오류: 데이터 검증 중 문제가 발생했습니다.")
        print(f"   {str(e)}")
        return
    
    # 3. 결과 리포트 생성
    print("\n[4단계] 검증 결과 리포트 생성 중...")
    try:
        reporter = ReportGenerator(output_dir)
        report_path = reporter.generate_report(
            audit_results=audit_results,
            source_file=target_file.name
        )
        print(f"   리포트 생성 완료: {report_path}")
    except Exception as e:
        print(f"❌ 오류: 리포트 생성 중 문제가 발생했습니다.")
        print(f"   {str(e)}")
        return
    
    print("\n" + "=" * 60)
    print("✅ 모든 작업이 완료되었습니다!")
    print(f"   결과 파일: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
