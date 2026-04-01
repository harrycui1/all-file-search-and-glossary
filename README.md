# ALL File Search and Glossary

Search and retrieve passages from Tibetan Buddhist texts in ACIP (Asian Classics Input Project) / Asian Legacy Library format using Google Gemini's File Search API, with vocabulary extraction from bilingual EPUB texts.

This tool is designed to work with any Tibetan text data in ACIP Romanized format — the included POC uses the Kangyur (collected words of the Buddha) as a test dataset, but the upload and search pipeline works with any ACIP-formatted text collection.

## What This Does

1. **Upload** Romanized Tibetan `.txt` files (in ACIP format) to a Google Gemini File Search Store, tagged with category and volume metadata
2. **Search** the uploaded texts using English queries, with three modes:
   - `raw` — retrieval only, no LLM processing (fastest)
   - `fast` — LLM summary without translation
   - `context` — full scholarly response with original Tibetan quotes, English translation, and source citations
3. **Evaluate** search quality with recall/precision metrics against ground-truth queries
4. **Extract vocabulary** — parse Tibetan-English EPUB books and use an LLM to extract verified Buddhist terminology pairs

## Project Structure

```
config.py            — Configuration (API keys via env vars, model names, paths)
upload.py            — Upload .txt files to Gemini File Search Store
search.py            — Search the store (raw / fast / context modes)
test_poc.py          — End-to-end POC: create store, upload, test queries
evaluate.py          — Recall & precision evaluation (25 ground-truth queries)
vocab_extractor.py   — Extract Tibetan-English term pairs from EPUB files
docs/                — Technical documentation and planning notes
```

## Prerequisites

- Python 3.10+
- A Google Gemini API key

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/asianlegacylibrary/all-file-search-and-glossary.git
cd all-file-search-and-glossary

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Set your API key
export GEMINI_API_KEY="your-gemini-api-key"
```

## Data Setup

Text data files are not included in this repository. To use the search functionality:

1. Obtain Romanized Tibetan text files in ACIP format (`.txt`)
2. Place them in a data folder at the project root, organized by section and volume. For example, the Kangyur POC uses `KANGYUR updated to 12 30 25 WS 2/` with subfolders like `1. 'DUL BA_Vowed Morality (Vinaya)/VOL 01 (KA)/...`
3. Update the paths in `config.py` to point to your data folder
4. The upload script will automatically detect categories and volumes from the folder structure

For the vocabulary extractor, place EPUB files in an `EPUB/` folder at the project root.

## Usage

### Upload texts to a Gemini File Search Store

```bash
# Create a new store
python upload.py create --display-name kangyur-poc

# Upload POC subset (Vinaya section only)
python upload.py upload-poc --store-name fileSearchStores/your-store-id

# Upload all texts
python upload.py upload-all --store-name fileSearchStores/your-store-id
```

### Search

```bash
# Single query
python search.py --store-name fileSearchStores/your-store-id -q "What are the rules about monastic discipline?" -m context

# Interactive mode
python search.py --store-name fileSearchStores/your-store-id -m raw
```

### Run the POC end-to-end

```bash
# Setup: creates store + uploads Vinaya texts
python test_poc.py setup

# Test: runs predefined queries
python test_poc.py test

# Interactive search
python test_poc.py interactive
```

### Evaluate search quality

```bash
python evaluate.py --save-json
```

### Extract vocabulary from EPUBs

```bash
export OPENROUTER_API_KEY="your-key"
python vocab_extractor.py
```
