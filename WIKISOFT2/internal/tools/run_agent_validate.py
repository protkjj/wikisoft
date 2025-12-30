"""
Agent Validation CLI

간단한 터미널 실행기로 파일 경로를 받아 ReACT 루프를 실행하고
신뢰도/의사결정 요약을 출력합니다.

Usage:
  python -m internal.tools.run_agent_validate --file path/to.xlsx --steps 3
"""

import argparse
import asyncio
import os

from internal.tools.registry import get_registry
from internal.tools.parser import register_parser_tool
from internal.tools.validator import register_validator_tools
from internal.tools.analyzer import register_analyzer_tools
from internal.tools.corrector import register_corrector_tools
from internal.agent.react_loop import ReACTLoop
from internal.agent.confidence import ConfidenceCalculator
from internal.agent.decision_engine import DecisionEngine


def build_registry():
    registry = get_registry()
    # 도구 등록 (중복 등록 방지: 구현체에서 체크)
    register_parser_tool(registry)
    register_validator_tools(registry)
    register_analyzer_tools(registry)
    register_corrector_tools(registry)
    return registry


async def run_agent(file_path: str, steps: int, threshold: float):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    registry = build_registry()
    react_loop = ReACTLoop(registry=registry)
    confidence_calc = ConfidenceCalculator()
    decision_engine = DecisionEngine()

    print("\n🔄 ReACT 루프 실행")
    result = await react_loop.run(
        file_path=file_path,
        task="validate",
        max_steps=steps,
        confidence_threshold=threshold,
    )

    steps_taken = result.get("steps", result.get("steps_taken", 0))
    final = result.get("result", {})
    conf = final.get("confidence", 0.0)

    print(f"  • 반복 횟수: {steps_taken}")
    print(f"  • 루프 신뢰도(모의): {conf:.0%}")

    # 의사결정 (데모용)
    decision = await decision_engine.decide(
        confidence=conf or 0.5,
        data={"source": os.path.basename(file_path)},
        result={"status": final.get("status", "completed")},
    )

    print("\n✅ 의사결정 요약")
    print(f"  • 권장: {getattr(decision, 'type', 'n/a')}")

    # 신뢰도 계산 샘플
    score = confidence_calc.calculate(0.8, 0.85, 0.75, conf or 0.7)
    print("\n📊 신뢰도(샘플)")
    print(f"  • 종합: {score.overall:.0%} (도구:{score.tool:.0%}, 데이터:{score.data:.0%})")


def main():
    parser = argparse.ArgumentParser(description="Agent Validation CLI")
    parser.add_argument("--file", required=True, help="검증할 파일 경로(.xlsx)")
    parser.add_argument("--steps", type=int, default=3, help="최대 반복 횟수")
    parser.add_argument("--threshold", type=float, default=0.7, help="종료 신뢰도 임계값")
    args = parser.parse_args()

    asyncio.run(run_agent(args.file, args.steps, args.threshold))


if __name__ == "__main__":
    main()
