"""
POC Test Script: End-to-end test of Kangyur File Search.

Usage:
    # Step 1: Create store and upload files
    python test_poc.py setup

    # Step 2: Run test queries
    python test_poc.py test --store-name fileSearchStores/xxx

    # Step 3: Interactive search
    python test_poc.py interactive --store-name fileSearchStores/xxx
"""

import sys
import json
from pathlib import Path

from upload import create_client, create_store, upload_folder
from search import search, format_response
from config import POC_FOLDER

STORE_FILE = Path(__file__).parent / ".store_name.json"

TEST_QUERIES = [
    "What are the rules about monks eating food?",
    "What does the Buddha say about stealing or taking what is not given?",
    "Describe the ordination ceremony for monks",
    "What are the rules about sexual misconduct for monastics?",
    "What does this text say about confession and purification of downfalls?",
    "Rules about robes and clothing for monks and nuns",
    "What are the four defeats or root downfalls?",
]


def save_store_name(name):
    STORE_FILE.write_text(json.dumps({"store_name": name}))
    print(f"Store name saved to {STORE_FILE}")


def load_store_name():
    if STORE_FILE.exists():
        data = json.loads(STORE_FILE.read_text())
        return data.get("store_name")
    return None


def setup():
    """Create store and upload POC files."""
    client = create_client()

    print("=== Step 1: Creating File Search Store ===")
    store = create_store(client, "kangyur-vinaya-poc")
    save_store_name(store.name)

    print(f"\n=== Step 2: Uploading Vinaya texts from POC folder ===")
    print(f"Folder: {POC_FOLDER}")
    results = upload_folder(client, store.name, POC_FOLDER)

    print(f"\n=== Setup Complete ===")
    print(f"Store name: {store.name}")
    print(f"You can now run: python test_poc.py test --store-name {store.name}")
    return store.name


def run_tests(store_name):
    """Run test queries against the store."""
    client = create_client()

    print(f"=== Running {len(TEST_QUERIES)} test queries ===")
    print(f"Store: {store_name}\n")

    for i, query in enumerate(TEST_QUERIES):
        print(f"\n{'#' * 80}")
        print(f"TEST {i+1}: {query}")
        print(f"{'#' * 80}")

        try:
            response = search(client, store_name, query)
            format_response(response)
        except Exception as e:
            print(f"ERROR: {e}")

        print()
        if i < len(TEST_QUERIES) - 1:
            cont = input("Press Enter for next query (or 'skip' to end)> ")
            if cont.strip().lower() == "skip":
                break


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="POC Test for Kangyur File Search")
    parser.add_argument("action", choices=["setup", "test", "interactive"])
    parser.add_argument("--store-name", help="Store name (auto-loaded if saved)")
    args = parser.parse_args()

    if args.action == "setup":
        setup()
    elif args.action == "test":
        store_name = args.store_name or load_store_name()
        if not store_name:
            print("Error: No store name. Run 'setup' first or provide --store-name")
            sys.exit(1)
        run_tests(store_name)
    elif args.action == "interactive":
        store_name = args.store_name or load_store_name()
        if not store_name:
            print("Error: No store name. Run 'setup' first or provide --store-name")
            sys.exit(1)
        from search import interactive_search
        client = create_client()
        interactive_search(client, store_name)
