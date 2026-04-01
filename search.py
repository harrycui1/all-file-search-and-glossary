"""Search Romanized Tibetan Buddhist scriptures using Google Gemini File Search."""

import sys

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, MODEL_NAME

# Search modes
MODE_RAW = "raw"
MODE_FAST = "fast"
MODE_CONTEXT = "context"

# Model for each mode
RAW_MODEL = "gemini-3-flash-preview"
FAST_MODEL = "gemini-3-flash-preview"
CONTEXT_MODEL = "gemini-3-pro-preview"

# System prompts per mode
SYSTEM_PROMPT_RAW = "Quote relevant passages briefly."

SYSTEM_PROMPT_FAST = (
    "Return the most relevant Romanized Tibetan passages exactly as they appear in the source documents. "
    "Do NOT translate. Do NOT explain. Just quote the original text verbatim. "
    "IMPORTANT: Always cite the FULL original filename starting with 'KL...' (e.g., KL00001E1_'DUL BA GZHI 1_Foundation of Vowed Morality...txt). "
    "Be concise."
)

SYSTEM_PROMPT_CONTEXT = (
    "You are a scholar of Tibetan Buddhist scriptures. "
    "The user will ask questions in English about Buddhist teachings. "
    "Your task is to find and return the most relevant passages from the Romanized Tibetan texts "
    "(Kangyur - the collected words of the Buddha). "
    "\n\n"
    "For each relevant passage you find:\n"
    "1. Quote the original Romanized Tibetan text exactly as it appears\n"
    "2. Provide an English translation of the passage\n"
    "3. Identify which text/volume it comes from\n"
    "4. Explain why this passage is relevant to the query\n"
    "\n"
    "If multiple passages are relevant, present them in order of relevance. "
    "Always preserve the exact Romanized Tibetan spelling from the source documents."
)


def create_client():
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)
    return genai.Client(api_key=GEMINI_API_KEY)


def search(client, store_name, query, model=None, category_filter=None, mode=MODE_CONTEXT):
    """
    Search the Kangyur using an English query.

    Args:
        mode: MODE_RAW (retrieval only, no LLM), MODE_FAST (no translation),
              or MODE_CONTEXT (detailed with translation)
    """
    # Select model and prompt based on mode
    if mode == MODE_RAW:
        model = model or RAW_MODEL
        system_instruction = SYSTEM_PROMPT_RAW
    elif mode == MODE_FAST:
        model = model or FAST_MODEL
        system_instruction = SYSTEM_PROMPT_FAST
    else:
        model = model or MODEL_NAME
        system_instruction = SYSTEM_PROMPT_CONTEXT

    # Build file search config
    file_search_config = {
        "file_search_store_names": [store_name],
    }
    if category_filter:
        file_search_config["metadata_filter"] = f'category="{category_filter}"'

    response = client.models.generate_content(
        model=model,
        contents=query,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[
                types.Tool(
                    file_search=types.FileSearch(**file_search_config)
                )
            ],
        ),
    )

    return response


def format_raw_response(response):
    """Format raw mode: only show retrieved chunks, no LLM output. Deduplicates."""
    if not (response.candidates and response.candidates[0].grounding_metadata):
        print("No results found.")
        return

    metadata = response.candidates[0].grounding_metadata
    chunks = getattr(metadata, "grounding_chunks", None)
    if not chunks:
        print("No results found.")
        return

    # Deduplicate by text content, prefer entries with real filenames
    seen_texts = {}
    for chunk in chunks:
        ctx = getattr(chunk, "retrieved_context", None)
        if not ctx:
            continue
        text = getattr(ctx, "text", "")
        title = getattr(ctx, "title", "Unknown")
        if text not in seen_texts:
            seen_texts[text] = title
        elif title.startswith("KL"):
            # Prefer real filename over internal ID
            seen_texts[text] = title

    unique = list(seen_texts.items())
    print("=" * 80)
    print(f"RETRIEVED PASSAGES ({len(unique)} unique results)")
    print("=" * 80)

    for i, (text, title) in enumerate(unique):
        print(f"\n--- [{i+1}] {title} ---")
        print(text)


def format_response(response):
    """Format and print the search response with grounding info."""
    print("=" * 80)
    print("SEARCH RESULTS")
    print("=" * 80)

    # Main response text
    if response.text:
        print(response.text)

    # Grounding metadata (source citations)
    print("\n" + "-" * 80)
    print("SOURCE CITATIONS")
    print("-" * 80)

    if response.candidates and response.candidates[0].grounding_metadata:
        metadata = response.candidates[0].grounding_metadata
        if hasattr(metadata, "grounding_chunks") and metadata.grounding_chunks:
            for i, chunk in enumerate(metadata.grounding_chunks):
                print(f"\n[Source {i+1}]")
                if hasattr(chunk, "retrieved_context"):
                    ctx = chunk.retrieved_context
                    if hasattr(ctx, "title"):
                        print(f"  File: {ctx.title}")
                    if hasattr(ctx, "text"):
                        # Show first 300 chars of the chunk
                        text_preview = ctx.text[:300] if ctx.text else ""
                        print(f"  Preview: {text_preview}...")
        if hasattr(metadata, "grounding_supports") and metadata.grounding_supports:
            print(f"\n  Total grounding supports: {len(metadata.grounding_supports)}")
    else:
        print("  No grounding metadata available.")


def interactive_search(client, store_name, mode=MODE_CONTEXT):
    """Interactive search loop."""
    mode_labels = {
        MODE_RAW: "RAW (retrieval only, fastest)",
        MODE_FAST: "FAST (no translation)",
        MODE_CONTEXT: "CONTEXT (with translation)",
    }
    print("=" * 80)
    print("Kangyur Search - Romanized Tibetan Buddhist Scriptures")
    print(f"Mode: {mode_labels[mode]}")
    print("Type your query in English. Type 'quit' to exit.")
    print("Prefix with 'cat:CategoryName ' to filter by category.")
    print("Categories: Vinaya, Prajnaparamita_100k, Sutra_Collection, Tantra, etc.")
    print("=" * 80)

    formatter = format_raw_response if mode == MODE_RAW else format_response

    while True:
        print()
        query = input("Query> ").strip()
        if not query or query.lower() in ("quit", "exit", "q"):
            break

        # Check for category filter
        category = None
        if query.startswith("cat:"):
            parts = query.split(" ", 1)
            if len(parts) == 2:
                category = parts[0][4:]
                query = parts[1]

        print(f"\nSearching for: {query}")
        if category:
            print(f"Category filter: {category}")
        print()

        try:
            response = search(client, store_name, query, category_filter=category, mode=mode)
            formatter(response)
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Search Kangyur with English queries")
    parser.add_argument("--store-name", required=True, help="File Search Store name")
    parser.add_argument("--query", "-q", help="Single query (non-interactive mode)")
    parser.add_argument("--model", help="Model name (overrides mode default)")
    parser.add_argument("--category", "-c", help="Filter by category")
    parser.add_argument(
        "--mode", "-m",
        choices=[MODE_RAW, MODE_FAST, MODE_CONTEXT],
        default=MODE_RAW,
        help=f"Search mode: '{MODE_RAW}' = retrieval only, no LLM (default, fastest), "
             f"'{MODE_FAST}' = quick LLM summary without translation, "
             f"'{MODE_CONTEXT}' = detailed results with translation"
    )
    args = parser.parse_args()

    client = create_client()
    formatter = format_raw_response if args.mode == MODE_RAW else format_response

    if args.query:
        response = search(
            client, args.store_name, args.query,
            model=args.model, category_filter=args.category, mode=args.mode
        )
        formatter(response)
    else:
        interactive_search(client, args.store_name, mode=args.mode)
