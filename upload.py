"""Upload Romanized Tibetan text files to Google Gemini File Search Store."""

import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, KANGYUR_BASE, POC_FOLDER


def create_client():
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Run: export GEMINI_API_KEY='your-key-here'")
        sys.exit(1)
    return genai.Client(api_key=GEMINI_API_KEY)


def create_store(client, display_name="kangyur-poc"):
    """Create a File Search Store."""
    store = client.file_search_stores.create(
        config={"display_name": display_name}
    )
    print(f"Created store: {store.name}")
    print(f"Display name: {display_name}")
    return store


def get_category_from_path(filepath):
    """Extract category metadata from file path."""
    parts = Path(filepath).parts
    for part in parts:
        if "DUL BA" in part:
            return "Vinaya"
        if "'BUM" in part:
            return "Prajnaparamita_100k"
        if "NYI KHRI" in part:
            return "Prajnaparamita_25k"
        if "BRGYAD STONG" in part:
            return "Prajnaparamita_8k"
        if "DKON BRTZEGS" in part:
            return "Ratnakuta"
        if "PHAL CHEN" in part:
            return "Avatamsaka"
        if "MDO MANG" in part:
            return "Sutra_Collection"
        if "MYANG 'DAS" in part:
            return "Nirvana"
        if "RGYUD" in part:
            return "Tantra"
    return "Unknown"


def get_volume_from_path(filepath):
    """Extract volume info from file path."""
    parts = Path(filepath).parts
    for part in parts:
        if part.startswith("VOL"):
            return part
    return "Unknown"


def upload_folder(client, store_name, folder_path, max_files=None):
    """Upload all .txt files from a folder (recursively) to the store."""
    txt_files = sorted(Path(folder_path).rglob("*.txt"))

    if max_files:
        txt_files = txt_files[:max_files]

    print(f"Found {len(txt_files)} .txt files to upload")

    results = []
    for i, filepath in enumerate(txt_files):
        filepath_str = str(filepath)
        category = get_category_from_path(filepath_str)
        volume = get_volume_from_path(filepath_str)
        filename = filepath.name

        print(f"\n[{i+1}/{len(txt_files)}] Uploading: {filename}")
        print(f"  Category: {category}, Volume: {volume}")

        try:
            # Copy to temp path with ASCII-safe name to avoid SDK encoding issues
            tmpdir = tempfile.mkdtemp(prefix="kangyur_upload_")
            safe_path = os.path.join(tmpdir, f"kangyur_{i:04d}.txt")
            shutil.copy2(filepath_str, safe_path)

            # 1. Upload file via Files API
            uploaded_file = client.files.upload(
                file=safe_path,
                config={"display_name": filename},
            )
            shutil.rmtree(tmpdir)
            print(f"  Uploaded as: {uploaded_file.name}")

            # 2. Import into File Search Store with metadata
            operation = client.file_search_stores.import_file(
                file_search_store_name=store_name,
                file_name=uploaded_file.name,
                config={
                    "custom_metadata": [
                        {"key": "category", "string_value": category},
                        {"key": "volume", "string_value": volume},
                        {"key": "filename", "string_value": filename},
                    ]
                },
            )
            print(f"  Status: imported successfully")
            results.append({"file": filename, "status": "ok"})
        except Exception as e:
            print(f"  Error: {e}")
            results.append({"file": filename, "status": "error", "error": str(e)})

        # Small delay to avoid rate limits
        time.sleep(0.5)

    print(f"\n--- Upload Summary ---")
    ok = sum(1 for r in results if r["status"] == "ok")
    err = sum(1 for r in results if r["status"] == "error")
    print(f"Success: {ok}, Failed: {err}, Total: {len(results)}")

    return results


def list_stores(client):
    """List all existing File Search Stores."""
    print("Existing stores:")
    for store in client.file_search_stores.list():
        print(f"  - {store.name} ({store.display_name})")


def list_documents(client, store_name):
    """List all documents in a store."""
    print(f"Documents in {store_name}:")
    for doc in client.file_search_stores.documents.list(parent=store_name):
        print(f"  - {doc.name}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Upload Tibetan texts to Gemini File Search")
    parser.add_argument("action", choices=["create", "upload-poc", "upload-all", "list-stores", "list-docs"])
    parser.add_argument("--store-name", help="Store name (e.g., fileSearchStores/xxx)")
    parser.add_argument("--display-name", default="kangyur-poc", help="Display name for new store")
    parser.add_argument("--max-files", type=int, help="Max files to upload (for testing)")
    parser.add_argument("--folder", help="Custom folder path to upload")
    args = parser.parse_args()

    client = create_client()

    if args.action == "create":
        store = create_store(client, args.display_name)
        print(f"\nSave this store name for later use:")
        print(f"  {store.name}")

    elif args.action == "upload-poc":
        if not args.store_name:
            print("Error: --store-name required")
            sys.exit(1)
        folder = args.folder or POC_FOLDER
        upload_folder(client, args.store_name, folder, args.max_files)

    elif args.action == "upload-all":
        if not args.store_name:
            print("Error: --store-name required")
            sys.exit(1)
        upload_folder(client, args.store_name, KANGYUR_BASE, args.max_files)

    elif args.action == "list-stores":
        list_stores(client)

    elif args.action == "list-docs":
        if not args.store_name:
            print("Error: --store-name required")
            sys.exit(1)
        list_documents(client, args.store_name)
