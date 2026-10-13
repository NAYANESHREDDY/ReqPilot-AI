import asyncio
import json
from pathlib import Path

from backend.app.agents.ambiguity_agent import AmbiguityAgent
from backend.app.agents.conflict_agent import ConflictAgent
from backend.app.agents.duplicate_agent import DuplicateAgent
from backend.app.agents.llm_adapter import LLMAdapter


BENCHMARK_PATH = Path("data/evaluation/benchmark_cases.json")


def normalize(value):
    return " ".join(str(value).lower().strip().split())


def ambiguity_audit(cases):
    agent = AmbiguityAgent()

    print("\n" + "=" * 70)
    print("AMBIGUITY AGENT — CURRENT BEHAVIOR")
    print("=" * 70)

    for case in cases:
        if case.get("category") != "ambiguity":
            continue

        req = {
            "id": case["id"],
            "summary": case["text"],
            "description": "",
        }

        predictions = agent.detect_ambiguities([req])
        detected = sorted(
            {
                normalize(item.get("detected_phrase", ""))
                for item in predictions
                if item.get("detected_phrase")
            }
        )
        expected = sorted(
            normalize(item)
            for item in case.get("expected_ambiguities", [])
        )

        tp = sorted(set(detected) & set(expected))
        fp = sorted(set(detected) - set(expected))
        fn = sorted(set(expected) - set(detected))

        print(f"\n{case['id']}")
        print(f"  Expected : {expected}")
        print(f"  Detected : {detected}")
        print(f"  TP       : {tp}")
        print(f"  FP       : {fp}")
        print(f"  FN       : {fn}")
        print(f"  Result   : {'PASS' if not fp and not fn else 'MISMATCH'}")


async def conflict_audit(cases):
    # No API key is required because the current ConflictAgent's
    # benchmark path is deterministic/rule-based.
    llm = LLMAdapter(api_key=None)
    agent = ConflictAgent(llm)

    print("\n" + "=" * 70)
    print("CONFLICT AGENT — CURRENT BEHAVIOR")
    print("=" * 70)

    for case in cases:
        if case.get("category") != "conflict":
            continue

        req_a = {
            "id": case["id"] + "-A",
            "summary": case["statement_a"],
            "description": "",
        }

        req_b = {
            "id": case["id"] + "-B",
            "summary": case["statement_b"],
            "description": "",
        }

        predictions = await agent.detect_conflicts([req_a, req_b])

        detected = len(predictions) > 0

        print(f"\n{case['id']}")
        print(f"  Expected conflict : YES")
        print(f"  Detected conflict : {'YES' if detected else 'NO'}")

        if predictions:
            for prediction in predictions:
                print(f"  Type              : {prediction.get('title')}")
                print(f"  Severity          : {prediction.get('severity')}")
                print(f"  Confidence        : {prediction.get('confidence')}")

        print(f"  Result            : {'PASS' if detected else 'MISSED'}")


def duplicate_audit(cases):
    agent = DuplicateAgent()

    print("\n" + "=" * 70)
    print("DUPLICATE AGENT — CURRENT BEHAVIOR")
    print("=" * 70)

    for case in cases:
        if case.get("category") != "duplicate":
            continue

        req_a = {
            "id": case["id"] + "-A",
            "summary": case["statement_a"],
            "description": "",
        }

        req_b = {
            "id": case["id"] + "-B",
            "summary": case["statement_b"],
            "description": "",
        }

        predictions = agent.detect_duplicates([req_a, req_b])

        detected = len(predictions) > 0

        print(f"\n{case['id']}")
        print(f"  Expected recommendation : {case.get('recommendation')}")
        print(f"  Expected similarity     : {case.get('expected_similarity')}")

        if predictions:
            for prediction in predictions:
                confidence = prediction.get("confidence")
                print(f"  Actual similarity       : {confidence}")
                print(f"  Detected duplicate      : YES")
        else:
            print("  Actual similarity       : below threshold / not reported")
            print("  Detected duplicate      : NO")

        print(f"  Result                  : {'PASS' if detected else 'MISSED'}")


def main():
    if not BENCHMARK_PATH.exists():
        raise FileNotFoundError(
            f"Benchmark file not found: {BENCHMARK_PATH.resolve()}"
        )

    data = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    cases = data["test_cases"]

    print("=" * 70)
    print("REQPILOT AI — PRE-FIX EVALUATION AUDIT")
    print("=" * 70)
    print(f"Benchmark suite : {data.get('benchmark_suite')}")
    print(f"Domain          : {data.get('domain')}")
    print(f"Total cases     : {len(cases)}")

    ambiguity_audit(cases)
    asyncio.run(conflict_audit(cases))
    duplicate_audit(cases)

    print("\n" + "=" * 70)
    print("PRE-FIX AUDIT COMPLETE")
    print("=" * 70)
    print("No project source files were modified.")


if __name__ == "__main__":
    main()
