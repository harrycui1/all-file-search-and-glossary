"""
MVP: Tibetan-English Vocabulary Extractor
从 EPUB 中提取藏英段落对，使用 LLM 提取关键术语，验证存在性
"""

import json
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
import requests

# ============ Step 1: Parse EPUB/XHTML ============

def extract_paragraph_pairs(xhtml_path: str) -> list[dict]:
    """
    从 XHTML 文件中提取藏英段落对
    藏文: <small> 标签内的 Roman ASCII
    英文: 紧随其后的段落
    """
    with open(xhtml_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    pairs = []
    current_pair = {"id": None, "tibetan": [], "english": []}

    for p in soup.find_all('p'):
        text = p.get_text(strip=True)

        # 检测段落标记 [G1], [G2], etc.
        id_match = re.match(r'\[G(\d+)\]', text)
        if id_match:
            # 保存上一个 pair
            if current_pair["tibetan"] or current_pair["english"]:
                pairs.append(current_pair)
            current_pair = {"id": f"G{id_match.group(1)}", "tibetan": [], "english": []}
            continue

        # 检测藏文 (在 <small> 标签内)
        small_tag = p.find('small')
        if small_tag:
            tibetan_text = small_tag.get_text(strip=True)
            if tibetan_text:
                current_pair["tibetan"].append(tibetan_text)
        # 英文段落 (class 包含 noindent1, block1, center1 等)
        elif p.get('class') and any(c in ['noindent1', 'block1', 'center1'] for c in p.get('class', [])):
            english_text = p.get_text(strip=True)
            if english_text:
                current_pair["english"].append(english_text)

    # 保存最后一个 pair
    if current_pair["tibetan"] or current_pair["english"]:
        pairs.append(current_pair)

    # 合并藏英文本
    for pair in pairs:
        pair["tibetan"] = " ".join(pair["tibetan"])
        pair["english"] = " ".join(pair["english"])

    return [p for p in pairs if p["tibetan"] and p["english"]]


# ============ Step 2: LLM Extract Key Terms ============

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

def extract_key_terms(tibetan: str, english: str) -> list[dict]:
    """
    使用 LLM 从藏英段落对中提取关键术语对
    """
    prompt = f"""You are a Tibetan-English Buddhist terminology expert.

Given a Tibetan text (in Roman ASCII transliteration) and its English translation by Geshe Michael Roach, extract key Buddhist technical terms.

For each term, provide:
1. tibetan: The Tibetan term in Roman ASCII (exactly as it appears in the source)
2. english: The English translation used by Geshe Michael
3. category: One of [philosophical_term, proper_name, text_title, practice_term, other]

IMPORTANT:
- Only extract terms that ACTUALLY APPEAR in the Tibetan text
- The Tibetan must be an exact substring of the source text
- Focus on Buddhist technical vocabulary, not common words

Tibetan: {tibetan}

English: {english}

Return a JSON array of term objects. If no technical terms found, return empty array [].
Example: [{{"tibetan": "KUN GZHI", "english": "foundation consciousness", "category": "philosophical_term"}}]

JSON:"""

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "anthropic/claude-opus-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024
        }
    )

    if response.status_code != 200:
        print(f"API Error: {response.status_code} - {response.text}")
        return []

    # 解析 JSON
    result = response.json()
    text = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

    # 尝试提取 JSON 数组
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return []
    return []


# ============ Step 3: Verify Existence ============

def verify_term_existence(term: dict, tibetan_source: str, english_source: str) -> dict:
    """
    验证提取的术语是否确实存在于原文中
    """
    tibetan_term = term.get("tibetan", "")
    english_term = term.get("english", "")

    # 藏文验证 (不区分大小写，处理空格变体)
    tibetan_normalized = tibetan_term.upper().replace("'", "'").replace("'", "'")
    source_normalized = tibetan_source.upper().replace("'", "'").replace("'", "'")
    tibetan_exists = tibetan_normalized in source_normalized

    # 英文验证 (不区分大小写)
    english_exists = english_term.lower() in english_source.lower()

    return {
        **term,
        "tibetan_verified": tibetan_exists,
        "english_verified": english_exists,
        "both_verified": tibetan_exists and english_exists
    }


# ============ Main Pipeline ============

def process_chapter(xhtml_path: str, output_path: str = None, limit: int = None):
    """
    处理单个章节文件
    """
    print(f"Processing: {xhtml_path}")

    # Step 1: 提取段落对
    pairs = extract_paragraph_pairs(xhtml_path)
    print(f"Found {len(pairs)} paragraph pairs")

    if limit:
        pairs = pairs[:limit]
        print(f"Processing first {limit} pairs for MVP")

    all_terms = []

    for i, pair in enumerate(pairs):
        print(f"\n--- Processing {pair['id']} ({i+1}/{len(pairs)}) ---")
        print(f"Tibetan: {pair['tibetan'][:80]}...")
        print(f"English: {pair['english'][:80]}...")

        # Step 2: LLM 提取术语
        terms = extract_key_terms(pair["tibetan"], pair["english"])
        print(f"Extracted {len(terms)} terms")

        # Step 3: 验证存在性
        for term in terms:
            verified = verify_term_existence(term, pair["tibetan"], pair["english"])
            verified["source_id"] = pair["id"]
            verified["source_tibetan"] = pair["tibetan"]
            verified["source_english"] = pair["english"]
            all_terms.append(verified)

            status = "✓" if verified["both_verified"] else "✗"
            print(f"  {status} {verified['tibetan']} -> {verified['english']}")

    # 输出结果
    result = {
        "source_file": str(xhtml_path),
        "total_pairs": len(pairs),
        "total_terms": len(all_terms),
        "verified_terms": len([t for t in all_terms if t["both_verified"]]),
        "terms": all_terms
    }

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nSaved to: {output_path}")

    return result


if __name__ == "__main__":
    # MVP: 处理 Golden Key 的第一章，限制前 5 个段落
    epub_dir = Path("/Users/haowei/Downloads/Code/ALL_Search/EPUB")
    chapter_path = epub_dir / "The Golden Key Difficult Questions In the Mind Only School of Buddhism Part One.epub" / "OEBPS" / "chap01.xhtml"
    output_path = epub_dir.parent / "vocab_output.json"

    result = process_chapter(str(chapter_path), str(output_path), limit=5)

    print(f"\n========== Summary ==========")
    print(f"Total terms extracted: {result['total_terms']}")
    print(f"Terms verified in both languages: {result['verified_terms']}")
