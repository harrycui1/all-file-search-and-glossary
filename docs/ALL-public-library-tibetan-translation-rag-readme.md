# Tibetan Buddhist Text Translation System

## A RAG-Powered Bidirectional Translation Assistant

---

## Overview

This system is a specialized translation assistant for Tibetan Buddhist texts, built on Retrieval-Augmented Generation (RAG) architecture. Unlike general-purpose translation tools, it leverages a curated glossary and parallel corpus to produce translations that are terminologically consistent, stylistically appropriate, and grounded in established Buddhist scholarship.

### What Makes This Different

General translation tools (Google Translate, DeepL, even GPT-4) struggle with Tibetan Buddhist texts because:

- **Specialized vocabulary**: Terms like སྟོང་པ་ཉིད (emptiness) and བྱང་ཆུབ་སེམས་དཔའ (bodhisattva) have precise philosophical meanings that differ from everyday usage
- **No single "correct" translation**: Different translation traditions render terms differently; consistency within a project matters more than any single choice
- **Classical vs. colloquial**: Buddhist texts use Classical Tibetan, which differs significantly from modern spoken Tibetan
- **Context-dependent meaning**: The same term may be translated differently depending on philosophical context

This system solves these problems by grounding every translation in your specific glossary and corpus, ensuring consistency and scholarly accuracy.

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Tibetan → English Translation** | Translate passages using your glossary and style |
| **English → Tibetan Lookup** | "How do you say 'compassion' in Tibetan?" |
| **Term Definitions** | Explain what a Tibetan term means with context |
| **Pronunciation** | Text-to-speech for Tibetan terms and passages |
| **Bidirectional** | Works in both directions with the same architecture |

---

## Architecture Overview

The system follows a RAG (Retrieval-Augmented Generation) pattern: rather than relying solely on an LLM's training data, we retrieve relevant information from our curated sources and provide it as context for each translation request.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HIGH-LEVEL ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                              User Query                                     │
│                    "What does བྱང་ཆུབ་སེམས་དཔའ mean?"                        │
│                          or                                                 │
│                    "How do you say 'bodhisattva'?"                          │
│                                 │                                           │
│                                 ▼                                           │
│                    ┌───────────────────────┐                                │
│                    │   QUERY PROCESSING    │                                │
│                    │   ─────────────────   │                                │
│                    │   • Language detect   │                                │
│                    │   • Intent classify   │                                │
│                    │   • Segmentation      │                                │
│                    │     (Botok)           │                                │
│                    └───────────┬───────────┘                                │
│                                │                                            │
│              ┌─────────────────┴─────────────────┐                          │
│              ▼                                   ▼                          │
│    ┌───────────────────┐               ┌───────────────────┐               │
│    │     GLOSSARY      │               │  PARALLEL CORPUS  │               │
│    │    (pgvector)     │               │    (pgvector)     │               │
│    │   ─────────────   │               │   ─────────────   │               │
│    │   ~50,000 terms   │               │  ~20,000 pairs    │               │
│    │   Tib ↔ English   │               │  Tib + English    │               │
│    │   + variants      │               │  translations     │               │
│    │   + definitions   │               │  + metadata       │               │
│    └─────────┬─────────┘               └─────────┬─────────┘               │
│              │                                   │                          │
│              └─────────────────┬─────────────────┘                          │
│                                │                                            │
│                                ▼                                            │
│                    ┌───────────────────────┐                                │
│                    │   CONTEXT ASSEMBLY    │                                │
│                    │   ─────────────────   │                                │
│                    │   • Glossary matches  │                                │
│                    │   • Similar passages  │                                │
│                    │   • Grammar analysis  │                                │
│                    └───────────┬───────────┘                                │
│                                │                                            │
│                                ▼                                            │
│                    ┌───────────────────────┐                                │
│                    │      CLAUDE API       │                                │
│                    │   ─────────────────   │                                │
│                    │   Synthesizes trans-  │                                │
│                    │   lation using the    │                                │
│                    │   retrieved context   │                                │
│                    └───────────┬───────────┘                                │
│                                │                                            │
│                                ▼                                            │
│                    ┌───────────────────────┐                                │
│                    │     TTS (Optional)    │                                │
│                    │   ─────────────────   │                                │
│                    │   Meta MMS for        │                                │
│                    │   Tibetan audio       │                                │
│                    └───────────┬───────────┘                                │
│                                │                                            │
│                                ▼                                            │
│                           Response                                          │
│              "བྱང་ཆུབ་སེམས་དཔའ means 'bodhisattva'..."                       │
│                          [🔊 Listen]                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Core Principle: Context Engineering

The key insight behind RAG is that an LLM's output quality depends heavily on what context it receives. For Tibetan Buddhist translation, this means:

> **Fill Claude's context window with exactly the right information from your corpus to produce translations that match your terminology and style.**

Rather than hoping the LLM "knows" how to translate Buddhist terms, we explicitly provide:
1. The exact glossary entries for terms in the input
2. Example translations of similar passages
3. Grammar analysis to help with complex sentences

This approach has several advantages:
- **Consistency**: Every translation uses your glossary, not the LLM's general knowledge
- **Control**: You can update translations by updating your data, not retraining a model
- **Transparency**: You can see exactly what context influenced each translation
- **No fine-tuning required**: Works with standard Claude API

---

## Data Sources

### 1. Glossary (Term Dictionary)

The glossary is the authoritative source for term translations. When the system encounters a Tibetan term, it first checks the glossary to ensure consistent translation.

**What it contains:**
- Tibetan term (in Tibetan script)
- English translation(s)
- Variant spellings and inflected forms
- Part of speech
- Definition/usage notes
- Sanskrit equivalent (if applicable)

**Example entry:**
```
Tibetan:     བྱང་ཆུབ་སེམས་དཔའ
Wylie:       byang chub sems dpa'
English:     bodhisattva
Variants:    བྱང་སེམས, བྱང་ཆུབ་སེམས་དཔའི (genitive)
POS:         noun
Definition:  A being dedicated to achieving enlightenment for the benefit 
             of all sentient beings. One who has generated bodhicitta.
Sanskrit:    bodhisattva
```

**Role in the system:**
- Term-to-term translation (both directions)
- Expanding English queries to Tibetan search terms
- Providing definitions in responses
- Ensuring terminological consistency

### 2. Parallel Corpus (Translation Examples)

The parallel corpus contains aligned Tibetan-English paragraph pairs from existing translations. These serve as style and context references.

**What it contains:**
- Tibetan passage (segmented)
- English translation
- Source text metadata (title, chapter, translator)
- Grammar analysis

**Example entry:**
```
Tibetan:     སངས་རྒྱས་དང་བྱང་ཆུབ་སེམས་དཔའ་ཐམས་ཅད་ལ་ཕྱག་འཚལ་ལོ།
English:     Homage to all the buddhas and bodhisattvas.
Source:      Bodhicaryāvatāra, Chapter 1
Translator:  Padmakara Translation Group
```

**Role in the system:**
- Providing translation style examples
- Showing how terms are used in context
- Few-shot learning examples for Claude
- Cross-lingual semantic search

---

## Bidirectional Translation

A critical feature is that the system works equally well in both directions. Users studying Tibetan texts need both:

### Tibetan → English: "What does this mean?"

```
User:    བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།

System:  
  1. Segment with Botok → བྱང་ཆུབ་སེམས་དཔའ + འི + སྤྱོད་པ + ལ + འཇུག་པ
  2. Look up each term in glossary (by Tibetan)
  3. Find similar passages in parallel corpus (by Tibetan embedding)
  4. Build prompt with glossary + examples
  5. Claude generates translation
  
Response: "Entering the Conduct of a Bodhisattva" — This is the title of 
          Śāntideva's famous work (Bodhicaryāvatāra)...
```

### English → Tibetan: "How do you say...?"

```
User:    How do you say "emptiness" in Tibetan?

System:
  1. Detect intent: English → Tibetan lookup
  2. Search glossary by English embedding → finds སྟོང་པ་ཉིད
  3. Retrieve related terms and usage examples
  4. Build response with term + pronunciation + context
  
Response: The Tibetan term for "emptiness" is སྟོང་པ་ཉིད (stong pa nyid).
          [🔊 Listen]
          
          This refers to the absence of inherent existence (svabhāva)...
```

### Why This Works: Cross-Lingual Embeddings

The magic enabling bidirectional search is the **DharmaMitra english-tibetan embedding model**. This model maps both Tibetan and English text into the same vector space, so:

```
embed("emptiness")     →  [0.234, -0.567, 0.891, ...]
embed("སྟོང་པ་ཉིད")      →  [0.231, -0.571, 0.888, ...]
                              ↑ Very similar vectors!
```

This means:
- English queries find Tibetan results
- Tibetan queries find English results
- Same index, same retrieval logic, works both ways

---

## Key Components

### Botok: Tibetan Word Segmentation

Tibetan script doesn't use spaces between words, making segmentation essential. Botok (from OpenPecha) handles this:

```
Input:   བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།

Output:  བྱང་ཆུབ་སེམས་དཔའ  (bodhisattva)     NOUN
         འི                (genitive)        PARTICLE
         སྤྱོད་པ            (conduct)         NOUN
         ལ                 (dative)          PARTICLE
         འཇུག་པ            (entering)        VERB.NOUN
```

**Why segmentation matters:**
- Enables term-by-term glossary lookup
- Lemmatization catches inflected forms (འི → base form)
- Grammar analysis helps Claude understand sentence structure
- Improves retrieval quality

### DharmaMitra Embedding Model

The `buddhist-nlp/english-tibetan` model from the DharmaMitra project is specifically trained for Buddhist texts:

- Maps Tibetan and English to the same vector space
- Trained on Buddhist parallel texts
- Understands specialized terminology
- Available on HuggingFace

**Alternatives considered:**
- Generic multilingual models (mBERT, XLM-R): Poor Tibetan support
- OpenAI embeddings: English-only
- Custom fine-tuning: Would require significant data and compute

### Vector Database (pgvector)

We use PostgreSQL with the pgvector extension for semantic search:

**Why pgvector over specialized vector DBs?**
- Integrates with existing PostgreSQL infrastructure
- Supports hybrid queries (vector similarity + metadata filters)
- Sufficient performance for ~50K glossary + ~20K corpus entries
- Simpler deployment and maintenance

**Index structure:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GLOSSARY TABLE                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  tibetan_raw          │  སྟོང་པ་ཉིད                                          │
│  tibetan_lemma        │  སྟོང་པ་ཉིད                                          │
│  english              │  emptiness                                          │
│  tibetan_embedding    │  [0.231, -0.571, ...]   ← for Tib→Eng queries       │
│  english_embedding    │  [0.234, -0.567, ...]   ← for Eng→Tib queries       │
│  variants             │  [སྟོང་ཉིད, སྟོང་པ]                                   │
│  pos_tag              │  NOUN                                               │
│  notes                │  "The absence of inherent existence..."             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  PARALLEL CORPUS TABLE                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  tibetan_raw          │  སངས་རྒྱས་དང་བྱང་ཆུབ་སེམས་དཔའ་ཐམས་ཅད་ལ་ཕྱག་འཚལ་ལོ།    │
│  english              │  Homage to all the buddhas and bodhisattvas.        │
│  embedding            │  [0.145, 0.892, ...]    ← cross-lingual embedding   │
│  source_text          │  Bodhicaryāvatāra                                   │
│  tibetan_lemmas       │  [སངས་རྒྱས, བྱང་ཆུབ་སེམས་དཔའ, ཕྱག་འཚལ]                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Claude API (Synthesis)

Claude receives the retrieved context and generates the final response. The prompt structure:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT STRUCTURE                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SYSTEM CONTEXT                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│  You are a translator of classical Tibetan Buddhist texts.                  │
│  Use the glossary terms EXACTLY as provided.                                │
│  Match the style of the example translations.                               │
│                                                                             │
│  GRAMMAR ANALYSIS                                                           │
│  ─────────────────────────────────────────────────────────────────────────  │
│  བྱང་ཆུབ་སེམས་དཔའ  NOUN   (bodhisattva)                                     │
│  འི              GEN    (genitive particle)                                 │
│  སྤྱོད་པ          NOUN   (conduct)                                          │
│  ...                                                                        │
│                                                                             │
│  GLOSSARY                                                                   │
│  ─────────────────────────────────────────────────────────────────────────  │
│  བྱང་ཆུབ་སེམས་དཔའ = bodhisattva                                             │
│  སྤྱོད་པ = conduct                                                          │
│  འཇུག་པ = entering, engaging                                                │
│  ...                                                                        │
│                                                                             │
│  REFERENCE TRANSLATIONS                                                     │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Example 1:                                                                 │
│    Tibetan: [similar passage from corpus]                                   │
│    English: [its translation]                                               │
│  ...                                                                        │
│                                                                             │
│  INPUT TEXT                                                                 │
│  ─────────────────────────────────────────────────────────────────────────  │
│  བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key prompting principles:**
- Glossary terms are mandatory ("use EXACTLY as provided")
- Examples demonstrate style, not just vocabulary
- Grammar analysis helps with complex sentences
- Output format is specified when needed

### Text-to-Speech (MMS)

Meta's Massively Multilingual Speech project includes a Tibetan model (`facebook/mms-tts-bod`):

- Supports Central Tibetan (Lhasa dialect)
- Trained partly on religious texts (good for Buddhist terminology)
- Available via HuggingFace Transformers
- Adds ~200-500ms latency

**Usage pattern:**
- On-demand generation (user clicks "Listen")
- Useful for learning pronunciation
- Especially valuable for Eng→Tib lookups

---

## Retrieval Strategy

### Three-Tier Glossary Retrieval

For Tibetan→English, we use a three-tier approach to maximize recall:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  THREE-TIER GLOSSARY RETRIEVAL                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Input: བྱང་ཆུབ་སེམས་དཔའི (genitive form)                                    │
│                                                                             │
│  TIER 1: Exact Match                                                        │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Query: WHERE tibetan_raw = 'བྱང་ཆུབ་སེམས་དཔའི'                              │
│  Result: May find nothing (genitive not in glossary as headword)            │
│                                                                             │
│  TIER 2: Lemma Match                                                        │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Botok lemmatizes: བྱང་ཆུབ་སེམས་དཔའི → བྱང་ཆུབ་སེམས་དཔའ                       │
│  Query: WHERE tibetan_lemma = 'བྱང་ཆུབ་སེམས་དཔའ'                             │
│  Result: ✓ Finds "bodhisattva" entry                                        │
│                                                                             │
│  TIER 3: Semantic Similarity                                                │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Query: ORDER BY tibetan_embedding <=> query_embedding LIMIT 5              │
│  Result: Finds related terms (བྱང་སེམས, སེམས་དཔའ, etc.)                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Parallel Corpus Retrieval

For finding similar translated passages:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CORPUS RETRIEVAL                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Input: User's Tibetan passage                                              │
│                                                                             │
│  1. Embed the input using DharmaMitra model                                 │
│  2. Vector similarity search against corpus embeddings                      │
│  3. Return top 3-5 most similar passages                                    │
│  4. These become few-shot examples for Claude                               │
│                                                                             │
│  Optional enhancements:                                                     │
│  • Boost passages with high lemma overlap                                   │
│  • Filter by text category if known                                         │
│  • Prefer passages from same source text                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Context Window Budget

Claude Sonnet has ~200K tokens, but we target ~8K for efficiency:

| Component | Typical Size | Purpose |
|-----------|--------------|---------|
| System prompt | ~500 tokens | Role, constraints, style guidance |
| Glossary entries (15) | ~300 tokens | Term translations |
| Example passages (5) | ~1,500 tokens | Style reference |
| Grammar analysis | ~200 tokens | Sentence structure |
| Input text | ~200-1,000 tokens | What to translate |
| Reserved for output | ~1,000 tokens | Translation result |
| **Buffer** | ~3,500 tokens | Safety margin |

**Implications:**
- Inputs over ~1,000 tokens may need chunking
- Complex passages may get fewer examples
- Glossary is prioritized over examples (terminology > style)

---

## Query Types and Routing

The system detects user intent and routes accordingly:

| Query Pattern | Intent | Primary Source |
|---------------|--------|----------------|
| "བྱང་ཆུབ་སེམས་དཔའ" (Tibetan only) | Translate Tib→Eng | Glossary + Corpus |
| "What does སྟོང་པ་ཉིད mean?" | Term lookup Tib→Eng | Glossary |
| "How do you say 'emptiness'?" | Term lookup Eng→Tib | Glossary |
| "Translate: May all beings..." | Translate Eng→Tib | Glossary + Corpus |
| [Long Tibetan passage] | Full translation | All sources |

---

## External Resources and Acknowledgments

### DharmaMitra Project (dharmamitra.org)

Berkeley AI Research project for Buddhist language NLP:
- `buddhist-nlp/english-tibetan` — Cross-lingual embedding model
- `buddhist-nlp/gemma-2-mitra-it` — Instruction-tuned translation model
- Tibetan stemmer, aligners, and other tools

### OpenPecha

- **[Botok](https://github.com/OpenPecha/botok)** — Tibetan word tokenizer and POS tagger
- Extensive Tibetan text corpora
- Active development community

### Meta MMS

- `facebook/mms-tts-bod` — Tibetan text-to-speech
- Part of Massively Multilingual Speech project
- 1,100+ language support

---

## Implementation Phases

### Phase 0: Evaluation & Prototyping (1-2 weeks)

**Goal:** Validate the approach before building infrastructure.

- Define success metrics (glossary adherence, style consistency, accuracy)
- Create test set of 50-100 passages with ground truth translations
- Manually simulate RAG: hand-pick glossary entries and examples, test prompts with Claude
- Establish baseline quality scores
- Go/no-go decision

### Phase 1: Data Processing (2-3 weeks)

**Goal:** Clean, segment, and prepare data for indexing.

- Process glossary: normalize Unicode, add lemmas/variants, validate
- Process parallel corpus: align, segment with Botok, extract metadata
- Quality filtering and deduplication
- Export to JSONL format

### Phase 2: Infrastructure & Indexing (2-3 weeks)

**Goal:** Set up vector database and embedding pipeline.

- Deploy PostgreSQL + pgvector
- Deploy embedding model (SageMaker or EC2)
- Create database schema with appropriate indexes
- Batch embed and index all data
- Validate retrieval quality

### Phase 3: API Implementation (2-3 weeks)

**Goal:** Build the translation service.

- Implement query processing (intent detection, segmentation)
- Implement retrieval logic (three-tier glossary, corpus search)
- Implement prompt construction
- Implement Claude API integration
- Add TTS capability
- Deploy as containerized service

### Phase 4: Testing & Tuning (2-3 weeks)

**Goal:** Optimize quality and performance.

- Automated evaluation against test set
- Human evaluation of sample translations
- Tune retrieval parameters (top_k, similarity thresholds)
- Tune prompt structure
- Performance benchmarking

### Phase 5: Deployment & Monitoring (1-2 weeks)

**Goal:** Production deployment with observability.

- Production infrastructure setup
- Monitoring dashboards (latency, errors, usage)
- Alerting configuration
- Feedback collection mechanism
- Documentation and runbooks

**Total timeline: 10-16 weeks**

---

## Failure Modes and Mitigations

| Failure Mode | What Happens | Mitigation |
|--------------|--------------|------------|
| **Context Poisoning** | Bad translation in corpus influences new translations | Quality control on corpus; human review |
| **Context Distraction** | Too many examples overwhelm glossary | Tune retrieval limits; prioritize glossary in prompt |
| **Context Confusion** | Retrieved examples from wrong genre/style | Metadata filtering; prefer same source text |
| **Context Clash** | Glossary contradicts examples | Explicit prompt instruction: "Glossary overrides examples" |
| **Term Not Found** | Input contains term not in glossary | Semantic fallback; transliterate and flag for review |
| **Segmentation Error** | Botok mis-segments input | Spot-check common patterns; graceful degradation |

---

## Future Enhancements

### Session Memory
Maintain context across multi-turn conversations and long document translations for consistency.

### User Preferences
Store individual user glossary preferences and correction history.

### Feedback Loop
Collect user corrections and integrate into glossary/corpus updates.

### Speech-to-Text
Voice input using MMS ASR for users who can speak but not type Tibetan.

### Multi-Agent Orchestration
Dynamic routing based on query complexity: simple lookups bypass full RAG pipeline.

---

## Success Criteria

| Metric | Target | How Measured |
|--------|--------|--------------|
| Glossary Adherence | >95% | % of terms translated per glossary |
| Style Consistency | >4/5 | Human evaluation score |
| Meaning Accuracy | >90% | Human evaluation of meaning preservation |
| End-to-End Latency | <3s | p95 response time |
| User Satisfaction | >4/5 | Feedback ratings |

---

## Summary

This system transforms Tibetan Buddhist text translation from a guessing game into a principled, data-driven process:

1. **Curated data** (glossary + corpus) provides the ground truth
2. **Smart retrieval** finds the right context for each query
3. **Cross-lingual embeddings** enable bidirectional operation
4. **Claude synthesis** produces natural, accurate translations
5. **Audio output** aids pronunciation and learning

The result is a translation assistant that produces consistent, scholarly-quality translations grounded in your specific terminology and style—something no general-purpose tool can match.
