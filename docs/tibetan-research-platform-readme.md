# Tibetan Buddhist Text Research Platform

## Extending the Translation System with Full-Text Scholarly Search

---

## Overview

This document extends the core Translation System (see `tibetan-translation-rag-readme.md`) with a powerful scholarly research capability. While the base system handles translation and term lookup, this extension enables complex research queries like:

> "Can you tell me how Je Tsongkhapa translates the word 'impermanence' and give some examples of why he might translate it differently in a given context?"

This requires searching across a full corpus of Tibetan texts, filtering by author and other metadata, and synthesizing findings with proper citations—capabilities that go beyond simple translation.

---

## The Research Query Challenge

Scholarly research queries differ fundamentally from translation requests:

| Translation Request | Research Query |
|---------------------|----------------|
| "What does སྟོང་པ་ཉིད mean?" | "How does Tsongkhapa use སྟོང་པ་ཉིད in different contexts?" |
| Single passage in, translation out | Search across corpus, analyze patterns, cite sources |
| Needs: glossary + examples | Needs: full text search + metadata filtering + synthesis |
| Response: translation | Response: analysis with citations and links |

The base system's glossary and parallel corpus are insufficient for this—we need access to **complete Tibetan texts** with **rich metadata** for filtering.

---

## Three-Source Architecture

The research platform adds Elasticsearch as a third data source, creating a complementary three-source retrieval system:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      THREE-SOURCE ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                              User Query                                     │
│        "How does Tsongkhapa translate 'impermanence'?"                      │
│                                 │                                           │
│                                 ▼                                           │
│                    ┌───────────────────────┐                                │
│                    │    QUERY ANALYSIS     │                                │
│                    │    & ROUTING          │                                │
│                    └───────────┬───────────┘                                │
│                                │                                            │
│          ┌─────────────────────┼─────────────────────┐                      │
│          ▼                     ▼                     ▼                      │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│ │    GLOSSARY     │  │ PARALLEL CORPUS │  │  ELASTICSEARCH  │              │
│ │   (pgvector)    │  │   (pgvector)    │  │  (Full Texts)   │              │
│ ├─────────────────┤  ├─────────────────┤  ├─────────────────┤              │
│ │                 │  │                 │  │                 │              │
│ │  ROLE:          │  │  ROLE:          │  │  ROLE:          │              │
│ │  Term Bridge    │  │  Translation    │  │  Source         │              │
│ │                 │  │  Reference      │  │  Documents      │              │
│ │  ─────────────  │  │  ─────────────  │  │  ─────────────  │              │
│ │  • English →    │  │  • Style        │  │  • Full Tibetan │              │
│ │    Tibetan      │  │    examples     │  │    texts        │              │
│ │    expansion    │  │  • Context      │  │  • Author       │              │
│ │  • Term         │  │    for Claude   │  │    filter       │              │
│ │    definitions  │  │  • Has English  │  │  • Text filter  │              │
│ │  • Variants     │  │    translations │  │  • Deep search  │              │
│ │                 │  │                 │  │  • Source links │              │
│ │                 │  │                 │  │                 │              │
│ │  ~50K terms     │  │  ~20K pairs     │  │  Full canon     │              │
│ │                 │  │                 │  │                 │              │
│ └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
│          │                    │                    │                        │
│          │                    │                    │                        │
│          │    ┌───────────────┘                    │                        │
│          │    │                                    │                        │
│          ▼    ▼                                    │                        │
│ ┌─────────────────────┐                           │                        │
│ │ "impermanence" →    │                           │                        │
│ │  མི་རྟག་པ            │                           │                        │
│ │  སྐད་ཅིག་མ           │────────────────────────────┘                        │
│ │  འགྱུར་བ            │     Tibetan terms sent                             │
│ │  འཇིག་པ             │     to Elasticsearch                               │
│ └─────────────────────┘                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### How the Sources Complement Each Other

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SOURCE ROLES IN SCHOLARLY QUERIES                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  USER QUERY: "How does Tsongkhapa use 'impermanence'?"                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  GLOSSARY: The Bridge                                               │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                     │   │
│  │  Problem: User query is in English, but Elasticsearch contains      │   │
│  │           Tibetan texts. How do we search?                          │   │
│  │                                                                     │   │
│  │  Solution: Glossary expands English → Tibetan                       │   │
│  │                                                                     │   │
│  │    "impermanence" → མི་རྟག་པ (mi rtag pa) — primary term            │   │
│  │                   → མི་རྟག (mi rtag) — short form                   │   │
│  │                   → སྐད་ཅིག་མ (skad cig ma) — momentariness         │   │
│  │                   → འགྱུར་བ (gyur ba) — change (related)            │   │
│  │                   → འཇིག་པ (jig pa) — disintegration (related)      │   │
│  │                                                                     │   │
│  │  Now we have Tibetan search terms for Elasticsearch!                │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ELASTICSEARCH: The Source                                          │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                     │   │
│  │  Contains: Complete Tibetan texts with metadata                     │   │
│  │                                                                     │   │
│  │  Query:                                                             │   │
│  │    • MUST match: མི་རྟག་པ OR མི་རྟག OR སྐད་ཅིག་མ OR འགྱུར་བ          │   │
│  │    • FILTER by: author = "Tsongkhapa"                               │   │
│  │                                                                     │   │
│  │  Returns: Tibetan passages + metadata + URLs                        │   │
│  │                                                                     │   │
│  │    ┌─────────────────────────────────────────────────────────┐     │   │
│  │    │  Title: Lamrim Chenmo                                   │     │   │
│  │    │  Author: Je Tsongkhapa                                  │     │   │
│  │    │  Chapter: Path of Small Capacity                        │     │   │
│  │    │  Tibetan: མི་རྟག་པ་བསམ་པ་ནི། འདི་ལྟར་སེམས་ཅན་ཐམས་ཅད...     │     │   │
│  │    │  URL: https://texts.example.com/lamrim/ch3#p45          │     │   │
│  │    └─────────────────────────────────────────────────────────┘     │   │
│  │                                                                     │   │
│  │  Note: Tibetan text only — no English translations stored here     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PARALLEL CORPUS: The Translation Helper                            │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                     │   │
│  │  Problem: ES returned Tibetan passages, but Claude needs to         │   │
│  │           translate them. How should it render these terms?         │   │
│  │                                                                     │   │
│  │  Solution: Find similar passages that DO have translations          │   │
│  │                                                                     │   │
│  │    For ES passage about མི་རྟག་པ in meditative context...           │   │
│  │    Find similar corpus passages showing how such text is            │   │
│  │    typically translated.                                            │   │
│  │                                                                     │   │
│  │  These become few-shot examples for Claude's synthesis.             │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Query Flow: Step by Step

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  COMPLETE QUERY FLOW                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  USER: "How does Tsongkhapa use the term 'impermanence'?"                   │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│  STEP 1: QUERY PARSING                                                      │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  Extract structured information from natural language:                      │
│                                                                             │
│    {                                                                        │
│      query_type: "author_term_analysis",                                    │
│      english_terms: ["impermanence"],                                       │
│      tibetan_terms: [],                                                     │
│      author: "Tsongkhapa",                                                  │
│      text_title: null,                                                      │
│      wants_examples: true,                                                  │
│      wants_explanation: true                                                │
│    }                                                                        │
│                                                                             │
│  This can use Claude for complex parsing or rules for simple patterns.      │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│  STEP 2: TERM EXPANSION (via Glossary)                                      │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  Query the glossary with English term "impermanence":                       │
│                                                                             │
│    Search: english_embedding <=> embed("impermanence")                      │
│                                                                             │
│  Results:                                                                   │
│    ┌────────────────────────────────────────────────────────────────┐      │
│    │  མི་རྟག་པ    = impermanence (primary)                          │      │
│    │  མི་རྟག      = impermanent (adjective form)                    │      │
│    │  སྐད་ཅིག་མ   = momentary (related: subtle impermanence)        │      │
│    │  འགྱུར་བ     = change (related concept)                        │      │
│    │  འཇིག་པ      = disintegration (Madhyamaka context)             │      │
│    └────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│  Now we have Tibetan terms to search in Elasticsearch.                      │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│  STEP 3: ELASTICSEARCH QUERY                                                │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  Build query using expanded Tibetan terms + author filter:                  │
│                                                                             │
│    {                                                                        │
│      "query": {                                                             │
│        "bool": {                                                            │
│          "must": [{                                                         │
│            "bool": {                                                        │
│              "should": [                                                    │
│                {"match_phrase": {"tibetan_text": "མི་རྟག་པ"}},              │
│                {"match_phrase": {"tibetan_text": "མི་རྟག"}},                │
│                {"match_phrase": {"tibetan_text": "སྐད་ཅིག་མ"}},             │
│                {"match_phrase": {"tibetan_text": "འགྱུར་བ"}},               │
│                {"match_phrase": {"tibetan_text": "འཇིག་པ"}}                 │
│              ],                                                             │
│              "minimum_should_match": 1                                      │
│            }                                                                │
│          }],                                                                │
│          "filter": [                                                        │
│            {"term": {"author.keyword": "Je Tsongkhapa"}}                    │
│          ]                                                                  │
│        }                                                                    │
│      }                                                                      │
│    }                                                                        │
│                                                                             │
│  Results: 10 Tibetan passages from Tsongkhapa's works containing            │
│           these terms, with metadata and URLs.                              │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│  STEP 4: CONTEXT ENRICHMENT                                                 │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  For each ES result, gather supporting context:                             │
│                                                                             │
│  A. Get definitions for terms in the passages                               │
│     └─→ Query glossary for any technical terms in retrieved text            │
│                                                                             │
│  B. Find similar translated passages                                        │
│     └─→ Query parallel corpus with ES passage text                          │
│     └─→ Returns passages with English translations as style reference       │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│  STEP 5: CLAUDE SYNTHESIS                                                   │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  Build comprehensive prompt with all retrieved context:                     │
│                                                                             │
│    ┌────────────────────────────────────────────────────────────────┐      │
│    │  USER'S QUESTION                                               │      │
│    │  How does Tsongkhapa use the term 'impermanence'?              │      │
│    │                                                                │      │
│    │  GLOSSARY TERMS                                                │      │
│    │  • མི་རྟག་པ = impermanence                                     │      │
│    │  • སྐད་ཅིག་མ = momentary                                       │      │
│    │  • ...                                                         │      │
│    │                                                                │      │
│    │  PASSAGES FROM TSONGKHAPA'S WORKS                              │      │
│    │                                                                │      │
│    │  [Source 1]: Lamrim Chenmo — Chapter 3                         │      │
│    │  Tibetan: མི་རྟག་པ་བསམ་པ་ནི། འདི་ལྟར་སེམས་ཅན་ཐམས་ཅད...          │      │
│    │  Link: https://texts.example.com/lamrim/ch3#p45                │      │
│    │                                                                │      │
│    │  [Source 2]: Lamrim Chenmo — Chapter 17                        │      │
│    │  Tibetan: སྐད་ཅིག་མ་རེ་རེར་འཇིག་པ...                            │      │
│    │  Link: https://texts.example.com/lamrim/ch17#p12               │      │
│    │                                                                │      │
│    │  ...                                                           │      │
│    │                                                                │      │
│    │  TRANSLATION STYLE EXAMPLES                                    │      │
│    │  (from parallel corpus for reference)                          │      │
│    │                                                                │      │
│    │  INSTRUCTIONS                                                  │      │
│    │  Translate relevant portions, analyze patterns, cite sources   │      │
│    │  using [Source N] format, include URLs for user to explore.    │      │
│    └────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│  Claude translates, analyzes, and synthesizes response.                     │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│  STEP 6: FORMATTED RESPONSE                                                 │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  Response includes:                                                         │
│  • Analysis of how Tsongkhapa uses the term                                 │
│  • Translated excerpts from his works                                       │
│  • Citations linking to source documents                                    │
│  • Explanation of contextual variations                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Elasticsearch Schema

The Elasticsearch index stores complete Tibetan texts with rich metadata for filtering:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ELASTICSEARCH DOCUMENT SCHEMA                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  {                                                                          │
│    // ─────────────────────────────────────────────────────────────────    │
│    // IDENTIFIERS                                                           │
│    // ─────────────────────────────────────────────────────────────────    │
│    "id": "lamrim-chenmo-ch3-p45",                                           │
│                                                                             │
│    // ─────────────────────────────────────────────────────────────────    │
│    // TEXT CONTENT (Tibetan only)                                           │
│    // ─────────────────────────────────────────────────────────────────    │
│    "tibetan_text": "མི་རྟག་པ་བསམ་པ་ནི། འདི་ལྟར་སེམས་ཅན་ཐམས་ཅད་འཆི་བར...",    │
│                                                                             │
│    // ─────────────────────────────────────────────────────────────────    │
│    // AUTHOR METADATA                                                       │
│    // ─────────────────────────────────────────────────────────────────    │
│    "author": "Je Tsongkhapa",                                               │
│    "author_tibetan": "རྗེ་ཙོང་ཁ་པ",                                          │
│    "author_dates": "1357-1419",                                             │
│                                                                             │
│    // ─────────────────────────────────────────────────────────────────    │
│    // TEXT METADATA                                                         │
│    // ─────────────────────────────────────────────────────────────────    │
│    "title": "Lamrim Chenmo",                                                │
│    "title_tibetan": "བྱང་ཆུབ་ལམ་རིམ་ཆེན་མོ",                                  │
│    "title_english": "Great Treatise on the Stages of the Path",             │
│                                                                             │
│    // ─────────────────────────────────────────────────────────────────    │
│    // LOCATION METADATA                                                     │
│    // ─────────────────────────────────────────────────────────────────    │
│    "chapter": "Chapter 3",                                                  │
│    "chapter_tibetan": "སྐྱེས་བུ་ཆུང་ངུའི་ལམ",                                 │
│    "chapter_english": "The Path of the Person of Small Capacity",           │
│    "section": "Contemplating Impermanence",                                 │
│    "page": "45",                                                            │
│    "paragraph": "12",                                                       │
│                                                                             │
│    // ─────────────────────────────────────────────────────────────────    │
│    // CLASSIFICATION                                                        │
│    // ─────────────────────────────────────────────────────────────────    │
│    "category": "lamrim",           // lamrim, madhyamaka, tantra, etc.      │
│    "lineage": "Gelug",             // Gelug, Kagyu, Nyingma, Sakya          │
│    "text_type": "treatise",        // treatise, commentary, liturgy         │
│                                                                             │
│    // ─────────────────────────────────────────────────────────────────    │
│    // LINKING                                                               │
│    // ─────────────────────────────────────────────────────────────────    │
│    "url": "https://texts.example.com/lamrim-chenmo/chapter-3#p45",          │
│    "source_collection": "84000",                                            │
│                                                                             │
│    // ─────────────────────────────────────────────────────────────────    │
│    // DATES                                                                 │
│    // ─────────────────────────────────────────────────────────────────    │
│    "date_composed": "14th century",                                         │
│    "date_indexed": "2024-01-15"                                             │
│  }                                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

**Why Tibetan text only (no English)?**
- Elasticsearch is the authoritative source for original texts
- English translations live in the parallel corpus (for aligned pairs)
- Avoids duplication and sync issues
- Claude translates on-demand using glossary + corpus context

**Granularity: Paragraphs vs. chapters vs. sentences**
- We recommend **paragraph-level** indexing
- Small enough for precise retrieval
- Large enough for meaningful context
- Can reconstruct larger sections by fetching adjacent paragraphs

**Metadata richness**
- Rich metadata enables powerful filtering
- Author filtering is essential for scholarly queries
- Category/lineage filtering helps when comparing traditions
- URLs enable users to explore sources directly

---

## Query Types and Routing

The system must distinguish between query types and route appropriately:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  QUERY TYPE ROUTING                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SIMPLE TRANSLATION / LOOKUP                                        │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                     │   │
│  │  Examples:                                                          │   │
│  │    • "What does སྟོང་པ་ཉིད mean?"                                    │   │
│  │    • "How do you say 'emptiness'?"                                  │   │
│  │    • [Tibetan passage for translation]                              │   │
│  │                                                                     │   │
│  │  Route to: Base Translation System                                  │   │
│  │  Uses: Glossary + Parallel Corpus only                              │   │
│  │  No Elasticsearch needed                                            │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SCHOLARLY RESEARCH                                                 │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                     │   │
│  │  Indicators:                                                        │   │
│  │    • Author mentioned ("Tsongkhapa", "Nagarjuna", etc.)             │   │
│  │    • Text mentioned ("Lamrim Chenmo", "Bodhicaryāvatāra")           │   │
│  │    • Analysis requested ("how does X use...", "compare...")         │   │
│  │    • Examples across corpus ("show me instances of...")             │   │
│  │                                                                     │   │
│  │  Examples:                                                          │   │
│  │    • "How does Tsongkhapa translate 'impermanence'?"                │   │
│  │    • "Find passages where Nagarjuna discusses emptiness"            │   │
│  │    • "Compare how Gelug and Kagyu texts explain bodhicitta"         │   │
│  │                                                                     │   │
│  │  Route to: Research Platform                                        │   │
│  │  Uses: Glossary (term expansion) + Elasticsearch (source search)   │   │
│  │        + Parallel Corpus (translation reference) + Claude          │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  HYBRID QUERIES                                                     │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                     │   │
│  │  Example:                                                           │   │
│  │    "Translate this passage and tell me what other Madhyamaka       │   │
│  │     texts discuss similar points"                                   │   │
│  │                                                                     │   │
│  │  Route to: Both systems                                             │   │
│  │    1. Base system translates the passage                            │   │
│  │    2. Research platform finds related passages                      │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Response Format for Research Queries

Research responses must include proper citations and source links:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  EXAMPLE RESEARCH RESPONSE                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  USER: "Can you tell me how Je Tsongkhapa translates the word               │
│         'impermanence' and give some examples of why he might               │
│         translate it differently in a given context?"                       │
│                                                                             │
│  ───────────────────────────────────────────────────────────────────────   │
│                                                                             │
│  ## Tsongkhapa's Treatment of "Impermanence" (མི་རྟག་པ)                      │
│                                                                             │
│  Je Tsongkhapa primarily uses the term **མི་རྟག་པ** (mi rtag pa) for        │
│  "impermanence," though the context significantly affects how this          │
│  concept is elaborated.                                                     │
│                                                                             │
│  ### Coarse Impermanence (རགས་པའི་མི་རྟག་པ)                                   │
│                                                                             │
│  In the Lamrim Chenmo's section on the path of small capacity,              │
│  Tsongkhapa emphasizes impermanence as death-awareness:                     │
│                                                                             │
│  > འཆི་བ་ནི་ངེས་པ། འཆི་བའི་དུས་མ་ངེས་པ།                                       │
│  > "Death is certain; the time of death is uncertain."                      │
│  >                                                                          │
│  > — [Source 1: Lamrim Chenmo, Ch. 3][1]                                    │
│                                                                             │
│  Here, impermanence functions as a motivational teaching to inspire         │
│  urgency in practice.                                                       │
│                                                                             │
│  ### Subtle Impermanence (ཕྲ་བའི་མི་རྟག་པ)                                    │
│                                                                             │
│  When discussing the philosophical view in later chapters, Tsongkhapa       │
│  treats impermanence as momentary change:                                   │
│                                                                             │
│  > སྐད་ཅིག་མ་རེ་རེར་འཇིག་པ                                                   │
│  > "Disintegrating moment by moment"                                        │
│  >                                                                          │
│  > — [Source 2: Lamrim Chenmo, Ch. 17][2]                                   │
│                                                                             │
│  This presentation connects to the Madhyamaka analysis of phenomena.        │
│                                                                             │
│  ### Why the Contextual Differences?                                        │
│                                                                             │
│  Tsongkhapa adapts his presentation based on the practitioner's level:      │
│                                                                             │
│  | Context              | Term Emphasis    | Purpose                     │  │
│  |----------------------|------------------|-----------------------------│  │
│  | Small capacity path  | མི་རྟག་པ          | Motivation through death    │  │
│  | Middle capacity path | སྡུག་བསྔལ་མི་རྟག    | Understanding suffering     │  │
│  | Philosophical view   | སྐད་ཅིག་མ         | Momentariness analysis      │  │
│                                                                             │
│  ### Related Terms                                                          │
│                                                                             │
│  • **འགྱུར་བ** (gyur ba) — "change" — used for transformative processes     │
│  • **འཇིག་པ** (jig pa) — "disintegration" — Madhyamaka technical term       │
│  • **ཟད་པ** (zad pa) — "exhaustion" — karmic context                        │
│                                                                             │
│  ───────────────────────────────────────────────────────────────────────   │
│                                                                             │
│  **Sources**                                                                │
│  [1]: https://texts.example.com/lamrim-chenmo/chapter-3#contemplating       │
│  [2]: https://texts.example.com/lamrim-chenmo/chapter-17#momentariness      │
│                                                                             │
│  **Explore Further**                                                        │
│  → [View all passages on མི་རྟག་པ in Tsongkhapa's works]                    │
│  → [Compare with Chandrakirti's usage]                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Critical Insight: Glossary as Bridge

The most important architectural insight is that the **glossary serves as a bridge between English queries and Tibetan search**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  THE GLOSSARY AS BRIDGE                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                          English Query                                      │
│                     "impermanence in Tsongkhapa"                            │
│                                │                                            │
│                                ▼                                            │
│                    ┌───────────────────────┐                                │
│                    │       GLOSSARY        │                                │
│                    │    (Cross-lingual     │                                │
│                    │     embeddings)       │                                │
│                    └───────────┬───────────┘                                │
│                                │                                            │
│              ┌─────────────────┼─────────────────┐                          │
│              ▼                 ▼                 ▼                          │
│         མི་རྟག་པ           སྐད་ཅིག་མ           འགྱུར་བ                        │
│                                │                                            │
│                                ▼                                            │
│                    ┌───────────────────────┐                                │
│                    │    ELASTICSEARCH      │                                │
│                    │   (Tibetan texts)     │                                │
│                    └───────────────────────┘                                │
│                                                                             │
│  Without the glossary, we couldn't search Tibetan texts with English        │
│  concepts. The cross-lingual embeddings make this possible.                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Integration with Base System

The research platform extends rather than replaces the base translation system:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SYSTEM INTEGRATION                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                              User Query                                     │
│                                 │                                           │
│                                 ▼                                           │
│                    ┌───────────────────────┐                                │
│                    │    QUERY CLASSIFIER   │                                │
│                    └───────────┬───────────┘                                │
│                                │                                            │
│              ┌─────────────────┴─────────────────┐                          │
│              │                                   │                          │
│              ▼                                   ▼                          │
│  ┌───────────────────────┐           ┌───────────────────────┐             │
│  │   BASE TRANSLATION    │           │   RESEARCH PLATFORM   │             │
│  │       SYSTEM          │           │                       │             │
│  ├───────────────────────┤           ├───────────────────────┤             │
│  │                       │           │                       │             │
│  │  • Term lookups       │           │  All base capabilities│             │
│  │  • Direct translation │           │         PLUS          │             │
│  │  • Pronunciation      │           │                       │             │
│  │                       │           │  • Author search      │             │
│  │  Sources:             │           │  • Text search        │             │
│  │  • Glossary           │           │  • Cross-corpus       │             │
│  │  • Parallel Corpus    │           │    analysis           │             │
│  │                       │           │  • Citations & links  │             │
│  │                       │           │                       │             │
│  │                       │           │  Additional source:   │             │
│  │                       │           │  • Elasticsearch      │             │
│  │                       │           │                       │             │
│  └───────────────────────┘           └───────────────────────┘             │
│                                                                             │
│  The research platform USES the base system's components                    │
│  (glossary for term expansion, corpus for translation reference)            │
│  and ADDS Elasticsearch for full-text scholarly search.                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Additional Implementation Considerations

### Author Name Normalization

Authors have multiple name variants that must be normalized:

```
"Tsongkhapa" variants:
  • Je Tsongkhapa
  • Tsong-kha-pa  
  • Tsong Khapa
  • རྗེ་ཙོང་ཁ་པ
  • ཙོང་ཁ་པ
  • Lobsang Drakpa (ordination name)
```

The system should maintain an author normalization table and expand queries to match all variants.

### Text Title Normalization

Similarly, texts have multiple names:

```
"Bodhicaryāvatāra" variants:
  • Bodhisattvacaryāvatāra
  • Way of the Bodhisattva
  • Guide to the Bodhisattva's Way of Life
  • བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ
  • sPyod 'jug (abbreviated Tibetan)
```

### Handling "Not Found" Cases

When Elasticsearch returns no results:
1. Suggest broadening the search (remove author filter)
2. Check if the author/text is in the corpus
3. Offer to search related terms
4. Never hallucinate sources

### Citation Integrity

Critical requirements:
- Never invent citations
- Every quote must link to a real document
- If uncertain about source, say so
- Prefer direct quotes over paraphrases for accuracy

---

## Implementation Phases (Research Platform Extension)

Building on the base system phases:

| Phase | Research Platform Tasks |
|-------|-------------------------|
| **Phase 1** | Define Elasticsearch schema; plan metadata fields; assess current ES data |
| **Phase 2** | Deploy/configure Elasticsearch; index texts with metadata; create author/title normalization tables |
| **Phase 3** | Implement query parser for research queries; build ES query construction logic; integrate three-source retrieval |
| **Phase 4** | Test scholarly queries; tune retrieval weights; validate citation accuracy |
| **Phase 5** | Add "Explore further" features; implement cross-reference links; user testing with scholars |

---

## Summary

The Research Platform transforms the translation system into a comprehensive scholarly tool:

| Capability | Base System | + Research Platform |
|------------|-------------|---------------------|
| Term lookup | ✓ | ✓ |
| Passage translation | ✓ | ✓ |
| Pronunciation | ✓ | ✓ |
| Author-filtered search | ✗ | ✓ |
| Cross-corpus analysis | ✗ | ✓ |
| Citations with links | ✗ | ✓ |
| Pattern analysis | ✗ | ✓ |

The key architectural additions:
1. **Elasticsearch** for full-text Tibetan search with metadata filtering
2. **Query parser** to detect scholarly intent and extract entities
3. **Term expansion** using glossary as English→Tibetan bridge
4. **Citation formatting** with links to source documents
5. **Three-source retrieval** that combines all data sources appropriately

This enables the kind of deep scholarly inquiry that researchers actually need—not just "what does this mean?" but "how is this concept used across different texts and authors?"
