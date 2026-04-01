"""
Evaluation script: Measure recall & precision of Kangyur File Search.

Runs predefined queries against the POC store, compares returned sources
against a ground truth mapping, and reports recall/precision metrics.
"""

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, MODEL_NAME

STORE_FILE = Path(__file__).parent / ".store_name.json"

# --- Ground Truth ---
GROUND_TRUTH = [
    {
        "query": "What are the basic rules and foundations of monastic discipline?",
        "expected": ["KL00001E"],
        "description": "Broad foundation query - should hit Vinaya Vastu",
    },
    {
        "query": "What is the ordination ceremony for becoming a monk?",
        "expected": ["KL00001E"],
        "description": "Ordination is covered in Vinaya Vastu",
    },
    {
        "query": "List of individual liberation vows for monks",
        "expected": ["KL00002E", "KL00003E"],
        "description": "Pratimoksha Sutra + Vibhanga",
    },
    {
        "query": "What are the four root downfalls or defeats (parajika)?",
        "expected": ["KL00002E", "KL00003E"],
        "description": "Parajika are in Pratimoksha + Vibhanga",
    },
    {
        "query": "Rules about stealing or taking what is not given",
        "expected": ["KL00002E", "KL00003E", "KL00001E"],
        "description": "Stealing is a parajika - Pratimoksha, Vibhanga, Vastu",
    },
    {
        "query": "Rules about sexual misconduct for monastics",
        "expected": ["KL00002E", "KL00003E"],
        "description": "Sexual misconduct is first parajika",
    },
    {
        "query": "Rules about monks eating food and meals",
        "expected": ["KL00001E", "KL00006E"],
        "description": "Food rules in Vastu and Ksudraka",
    },
    {
        "query": "Rules about robes and clothing for monks",
        "expected": ["KL00001E", "KL00006E"],
        "description": "Robe rules in Vastu and Ksudraka",
    },
    {
        "query": "Confession and purification of downfalls",
        "expected": ["KL00002E", "KL00003E"],
        "description": "Confession categories in Pratimoksha/Vibhanga",
    },
    {
        "query": "Rules specifically for Buddhist nuns",
        "expected": ["KL00004E", "KL00005E"],
        "description": "Bhikshuni-specific texts",
    },
    {
        "query": "Ordination ceremony for nuns",
        "expected": ["KL00004E", "KL00005E", "KL00001E"],
        "description": "Nun ordination in Bhikshuni texts + Vastu",
    },
    {
        "query": "The sutra of individual freedom for fully ordained nuns",
        "expected": ["KL00004E"],
        "description": "Direct title match - Bhikshuni Pratimoksha",
    },
    {
        "query": "Detailed analysis and divisions of monastic vow categories",
        "expected": ["KL00003E"],
        "description": "Vibhanga = divisions/analysis",
    },
    {
        "query": "Remainder offenses and minor infractions",
        "expected": ["KL00003E", "KL00002E"],
        "description": "Samghavasesha/minor rules in Vibhanga",
    },
    {
        "query": "Miscellaneous topics about monastic life",
        "expected": ["KL00006E"],
        "description": "Ksudraka = assorted/miscellaneous",
    },
    {
        "query": "Medicine and healthcare for monks",
        "expected": ["KL00001E", "KL00006E"],
        "description": "Medicine topics in Vastu and Ksudraka",
    },
    {
        "query": "Rainy season retreat rules",
        "expected": ["KL00001E", "KL00006E"],
        "description": "Varsa/retreat rules in Vastu",
    },
    {
        "query": "Higher classic on vowed morality",
        "expected": ["KL00007E"],
        "description": "Direct title match - Uttara Grantha",
    },
    {
        "query": "Supplementary and advanced vinaya topics",
        "expected": ["KL00007E"],
        "description": "Uttara Grantha = supplementary texts",
    },
    {
        "query": "How was the sangha community organized?",
        "expected": ["KL00001E", "KL00007E"],
        "description": "Sangha organization in Vastu + Uttara",
    },
    {
        "query": "Rules about lying and false speech",
        "expected": ["KL00002E", "KL00003E"],
        "description": "Lying is a parajika/payattika",
    },
    {
        "query": "Schism in the sangha community",
        "expected": ["KL00001E", "KL00007E"],
        "description": "Sangha schism in Vastu + Uttara",
    },
    {
        "query": "What does the text say about emptiness and sunyata?",
        "expected": [],
        "type": "negative",
        "description": "Emptiness is Prajnaparamita, not Vinaya - should have low relevance",
    },
    {
        "query": "Mantra recitation and tantric visualization practices",
        "expected": [],
        "type": "negative",
        "description": "Tantra content, not in Vinaya at all",
    },
    {
        "query": "Bodhisattva vows and the six perfections",
        "expected": [],
        "type": "negative",
        "description": "Mahayana content, not in Vinaya Pratimoksha",
    },
]


@dataclass
class QueryResult:
    query: str
    description: str
    expected: list
    returned_files: list = field(default_factory=list)
    is_negative: bool = False
    recall: float = 0.0
    precision: float = 0.0
    error: str = ""


def load_store_name():
    if STORE_FILE.exists():
        data = json.loads(STORE_FILE.read_text())
        return data.get("store_name")
    return None


def extract_cited_files(response):
    """Extract filenames from grounding metadata in the response."""
    files = []
    if not response.candidates:
        return files
    candidate = response.candidates[0]
    metadata = getattr(candidate, "grounding_metadata", None)
    if not metadata:
        return files
    chunks = getattr(metadata, "grounding_chunks", None)
    if not chunks:
        return files
    for chunk in chunks:
        ctx = getattr(chunk, "retrieved_context", None)
        if ctx:
            title = getattr(ctx, "title", None)
            if title and title not in files:
                files.append(title)
    return files


def run_single_query(client, store_name, query, model=None):
    """Run a single search query and return the raw response."""
    model = model or MODEL_NAME
    system_instruction = (
        "You are a scholar of Tibetan Buddhist scriptures. "
        "The user will ask questions in English about Buddhist teachings. "
        "Find and return the most relevant passages from the Romanized Tibetan texts. "
        "Quote the original Romanized Tibetan text and provide an English translation."
    )
    response = client.models.generate_content(
        model=model,
        contents=query,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[
                types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[store_name]
                    )
                )
            ],
        ),
    )
    return response


def matches_expected(returned_file, expected_prefix):
    """Check if a returned filename matches an expected prefix pattern."""
    return expected_prefix in returned_file


def evaluate_query(client, store_name, test_case):
    """Run one query and compute recall/precision against ground truth."""
    query = test_case["query"]
    expected = test_case["expected"]
    is_negative = test_case.get("type") == "negative"
    description = test_case["description"]

    result = QueryResult(
        query=query,
        description=description,
        expected=expected,
        is_negative=is_negative,
    )

    try:
        response = run_single_query(client, store_name, query)
        result.returned_files = extract_cited_files(response)

        if is_negative:
            result.recall = 1.0
            result.precision = 1.0 if len(result.returned_files) == 0 else 0.0
        elif len(expected) == 0:
            result.recall = 1.0
            result.precision = 1.0 if len(result.returned_files) == 0 else 0.0
        else:
            matched = 0
            for exp in expected:
                if any(matches_expected(rf, exp) for rf in result.returned_files):
                    matched += 1
            result.recall = matched / len(expected)

            if result.returned_files:
                correct = 0
                for rf in result.returned_files:
                    if any(matches_expected(rf, exp) for exp in expected):
                        correct += 1
                result.precision = correct / len(result.returned_files)
            else:
                result.precision = 0.0

    except Exception as e:
        result.error = str(e)

    return result


def print_report(results):
    """Print a formatted evaluation report."""
    print("\n" + "=" * 90)
    print("KANGYUR FILE SEARCH — RECALL & PRECISION EVALUATION REPORT")
    print("=" * 90)

    positive_results = [r for r in results if not r.is_negative]
    negative_results = [r for r in results if r.is_negative]

    print("\n--- POSITIVE QUERIES (should find relevant results) ---\n")
    for i, r in enumerate(positive_results):
        status = "PASS" if r.recall >= 0.5 else "FAIL"
        print(f"[{status}] Q{i+1}: {r.query}")
        print(f"       {r.description}")
        print(f"       Expected: {r.expected}")
        print(f"       Returned: {r.returned_files}")
        print(f"       Recall: {r.recall:.0%}  Precision: {r.precision:.0%}")
        if r.error:
            print(f"       ERROR: {r.error}")
        print()

    if negative_results:
        print("\n--- NEGATIVE QUERIES (should NOT find relevant results) ---\n")
        for i, r in enumerate(negative_results):
            status = "PASS" if len(r.returned_files) == 0 else "WARN"
            print(f"[{status}] N{i+1}: {r.query}")
            print(f"       {r.description}")
            print(f"       Returned: {r.returned_files}")
            if r.returned_files:
                print(f"       ^ False positives detected")
            print()

    print("=" * 90)
    print("AGGREGATE METRICS")
    print("=" * 90)

    if positive_results:
        avg_recall = sum(r.recall for r in positive_results) / len(positive_results)
        avg_precision = sum(r.precision for r in positive_results) / len(positive_results)
        full_recall = sum(1 for r in positive_results if r.recall == 1.0)
        zero_recall = sum(1 for r in positive_results if r.recall == 0.0)
        errors = sum(1 for r in positive_results if r.error)

        print(f"\nPositive queries: {len(positive_results)}")
        print(f"  Average Recall:    {avg_recall:.1%}")
        print(f"  Average Precision: {avg_precision:.1%}")
        print(f"  Full recall (100%): {full_recall}/{len(positive_results)}")
        print(f"  Zero recall (0%):   {zero_recall}/{len(positive_results)}")
        print(f"  Errors:             {errors}/{len(positive_results)}")

    if negative_results:
        false_pos = sum(1 for r in negative_results if r.returned_files)
        print(f"\nNegative queries: {len(negative_results)}")
        print(f"  False positive rate: {false_pos}/{len(negative_results)}")

    print("\n" + "-" * 90)
    print("RECOMMENDATION")
    print("-" * 90)
    if positive_results:
        avg_recall = sum(r.recall for r in positive_results) / len(positive_results)
        if avg_recall >= 0.8:
            print("Recall >= 80%. Plan B (raw upload) is working well.")
            print("Recommendation: Proceed to upload full Kangyur (1008 files).")
        elif avg_recall >= 0.5:
            print("Recall 50-80%. Plan B works partially.")
            print("Recommendation: Consider Plan A (bilingual augmentation) for problem areas,")
            print("or proceed with Plan B and accept lower recall.")
        else:
            print("Recall < 50%. Plan B is insufficient.")
            print("Recommendation: Switch to Plan A (bilingual augmented indexing).")
    print()


def save_results_json(results, path="evaluation_results.json"):
    """Save raw results to JSON for further analysis."""
    data = []
    for r in results:
        data.append({
            "query": r.query,
            "description": r.description,
            "expected": r.expected,
            "returned_files": r.returned_files,
            "is_negative": r.is_negative,
            "recall": r.recall,
            "precision": r.precision,
            "error": r.error,
        })
    out = Path(__file__).parent / path
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Raw results saved to {out}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate Kangyur File Search recall & precision")
    parser.add_argument("--store-name", help="File Search Store name (auto-loaded from .store_name.json)")
    parser.add_argument("--limit", type=int, help="Only run first N queries (for quick testing)")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between queries in seconds (default: 2)")
    parser.add_argument("--save-json", action="store_true", help="Save raw results to JSON")
    args = parser.parse_args()

    store_name = args.store_name or load_store_name()
    if not store_name:
        print("Error: No store name. Provide --store-name or run test_poc.py setup first.")
        sys.exit(1)

    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)

    client = genai.Client(api_key=GEMINI_API_KEY)

    test_cases = GROUND_TRUTH
    if args.limit:
        test_cases = test_cases[:args.limit]

    print(f"Running {len(test_cases)} evaluation queries against {store_name}...")
    print(f"Delay between queries: {args.delay}s\n")

    results = []
    for i, tc in enumerate(test_cases):
        label = tc.get("type", "positive").upper()
        print(f"[{i+1}/{len(test_cases)}] ({label}) {tc['query'][:60]}...")
        result = evaluate_query(client, store_name, tc)
        results.append(result)

        if result.error:
            print(f"  ERROR: {result.error}")
        else:
            print(f"  Recall: {result.recall:.0%}  Precision: {result.precision:.0%}  Files: {len(result.returned_files)}")

        if i < len(test_cases) - 1:
            time.sleep(args.delay)

    print_report(results)

    if args.save_json:
        save_results_json(results)
